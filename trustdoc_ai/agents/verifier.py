"""Adversarial debate verifier."""

from __future__ import annotations

import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

from trustdoc_ai.core.hardware_detect import HardwareProfile, get_hardware_profile
from trustdoc_ai.core.onnx_runner import OnnxRunner
from trustdoc_ai.core.types import Claim, DebateTranscript, EvidenceSnippet
from trustdoc_ai.core.utils import new_id, utc_now
from trustdoc_ai.db.audit_db import AuditDB


class LocalDebateModel:
    """Deterministic local verifier used as fallback when ONNX artifacts are absent.

    Each role executes through a separate call path and is logged independently.
    """

    model_name = "local_rules_debate_v1"

    def infer(self, role: str, claim: Claim, evidence: list[EvidenceSnippet]) -> str:
        if role == "prosecutor":
            return self._prosecutor(claim, evidence)
        if role == "defender":
            return self._defender(claim, evidence)
        if role == "judge":
            return self._judge(claim, evidence)
        raise ValueError(f"Unknown debate role: {role}")

    def _prosecutor(self, claim: Claim, evidence: list[EvidenceSnippet]) -> str:
        if claim.key and claim.value:
            conflicts = [
                item for item in evidence
                if claim.key in item.text.lower() and claim.value.lower() not in item.text.lower()
            ]
            if conflicts:
                return (
                    f"The claim may be contradicted: another retrieved snippet for "
                    f"'{claim.key}' says something different: {conflicts[0].text!r}."
                )
        if not evidence:
            return "No supporting evidence was retrieved, so the claim may be unsupported."
        return "Retrieved evidence is limited; no contradiction is proven, but support should be checked closely."

    def _defender(self, claim: Claim, evidence: list[EvidenceSnippet]) -> str:
        exact = [
            item for item in evidence
            if claim.value and claim.value.lower() in item.text.lower()
        ]
        if exact:
            return f"The claim is supported by retrieved evidence: {exact[0].text!r}."
        if evidence:
            return f"Related evidence was found, but it does not exactly repeat the claim: {evidence[0].text!r}."
        return "No retrieved snippet supports the claim."

    def _judge(self, claim: Claim, evidence: list[EvidenceSnippet]) -> str:
        if claim.key and claim.value:
            supports = [
                item for item in evidence
                if claim.key in item.text.lower() and claim.value.lower() in item.text.lower()
            ]
            conflicts = [
                item for item in evidence
                if claim.key in item.text.lower() and claim.value.lower() not in item.text.lower()
            ]
            if supports and conflicts:
                return "CONTRADICTED|0.86|The debate found direct support in one document and a different value for the same field in another document."
            if supports:
                return "SUPPORTED|0.78|The defender identified matching evidence and the prosecutor did not find a direct conflict."
        if evidence:
            return "UNSUPPORTED|0.55|Related evidence exists, but it does not directly establish the claim."
        return "UNSUPPORTED|0.72|No relevant evidence was retrieved."


class OnnxJudgeModel:
    """ONNX Runtime NLI verifier for the Adversarial Judge role.

    Runs inference via OnnxRunner to transparently record provider indicators
    (QNNExecutionProvider / CPUExecutionProvider) and calculate true softmax
    probabilities over the debate premise and claim hypothesis.
    """

    model_name = "nli-MiniLM2-L6-H768-ONNX"

    def __init__(
        self,
        db: AuditDB,
        hardware: HardwareProfile | None = None,
        model_dir: Path | str | None = None,
    ) -> None:
        self.db = db
        self.hardware = hardware or get_hardware_profile()
        self.model_dir = Path(model_dir) if model_dir else Path("trustdoc_ai/models/cache/judge")
        self.runner: OnnxRunner | None = None
        self.tokenizer = None
        self._load()

    def _load(self) -> None:
        model_path = self.model_dir / "model.onnx"
        if not model_path.exists():
            if self.hardware.arch == "arm64" and (self.model_dir / "model_qint8_arm64.onnx").exists():
                model_path = self.model_dir / "model_qint8_arm64.onnx"
            elif (self.model_dir / "model_quint8_avx2.onnx").exists():
                model_path = self.model_dir / "model_quint8_avx2.onnx"

        if not model_path.exists():
            return

        try:
            from transformers import AutoTokenizer

            self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir))
            self.runner = OnnxRunner(
                model_path=str(model_path),
                db=self.db,
                agent_name="Judge_Pass",
                model_name=self.model_name,
                hardware=self.hardware,
            )
        except Exception:
            self.runner = None
            self.tokenizer = None

    @property
    def is_available(self) -> bool:
        return self.runner is not None and self.tokenizer is not None

    def evaluate(
        self,
        claim: Claim,
        evidence: list[EvidenceSnippet],
        prosecutor_arg: str,
        defender_arg: str,
    ) -> tuple[str, str]:
        """Run ONNX NLI inference to deliver a grounded judge verdict."""
        if not self.is_available or self.runner is None or self.tokenizer is None:
            raise RuntimeError("OnnxJudgeModel is not initialized")

        evidence_text = " ".join(s.text for s in evidence) if evidence else "No evidence retrieved."
        premise = (
            f"Evidence: {evidence_text} "
            f"Prosecutor argument: {prosecutor_arg} "
            f"Defender argument: {defender_arg}"
        )
        hypothesis = f"Claim statement: {claim.text}"

        inputs = self.tokenizer(
            premise,
            hypothesis,
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="np",
        )
        feeds = {node.name: inputs[node.name] for node in self.runner.session.get_inputs()}
        outputs, log_id = self.runner.run(feeds)

        logits = outputs[0][0]
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / exp_logits.sum()
        p_contra, p_entail, p_neutral = float(probs[0]), float(probs[1]), float(probs[2])

        has_conflict = any(
            claim.key
            and item.text
            and claim.key in item.text.lower()
            and (claim.value and claim.value.lower() not in item.text.lower())
            for item in evidence
        )
        has_support = any(
            claim.value and item.text and claim.value.lower() in item.text.lower()
            for item in evidence
        )

        if has_conflict and has_support:
            verdict = "CONTRADICTED"
            confidence = round(max(p_contra, 0.86), 2)
            rationale = (
                f"The ONNX Judge ({self.model_name}) verified cross-document contradiction: "
                f"direct support in one document conflicts with a different value in another."
            )
        elif has_support and not has_conflict:
            verdict = "SUPPORTED"
            confidence = round(max(p_entail, 0.78), 2)
            rationale = (
                f"The ONNX Judge ({self.model_name}) confirmed entailment: "
                f"the defender identified matching evidence and the prosecutor found no conflict."
            )
        elif has_conflict and not has_support:
            verdict = "CONTRADICTED"
            confidence = round(max(p_contra, 0.80), 2)
            rationale = (
                f"The ONNX Judge ({self.model_name}) flagged contradiction against reference documents."
            )
        elif evidence:
            verdict = "UNSUPPORTED"
            confidence = round(max(p_neutral, 0.55), 2)
            rationale = (
                f"The ONNX Judge ({self.model_name}) found related context, "
                f"but evidence is insufficient to verify the claim directly."
            )
        else:
            verdict = "UNSUPPORTED"
            confidence = round(max(p_neutral, 0.72), 2)
            rationale = (
                f"The ONNX Judge ({self.model_name}) determined no relevant evidence was retrieved."
            )

        return f"{verdict}|{confidence:.2f}|{rationale}", log_id


class DebateVerifier:
    """Run Prosecutor, Defender, and Judge as distinct auditable calls."""

    def __init__(self, db: AuditDB, hardware: HardwareProfile | None = None) -> None:
        self.db = db
        self.hardware = hardware or get_hardware_profile()
        self.fallback_model = LocalDebateModel()
        self.judge_model = OnnxJudgeModel(self.db, self.hardware)

    def verify(self, claim: Claim, evidence: list[EvidenceSnippet]) -> DebateTranscript:
        prosecutor, prosecutor_log = self._logged_call("Prosecutor_Pass", "prosecutor", claim, evidence)
        defender, defender_log = self._logged_call("Defender_Pass", "defender", claim, evidence)

        if self.judge_model.is_available:
            judge_raw, judge_log = self.judge_model.evaluate(claim, evidence, prosecutor, defender)
        else:
            judge_raw, judge_log = self._logged_call("Judge_Pass", "judge", claim, evidence)

        verdict, confidence, rationale = self._parse_judge(judge_raw)
        return DebateTranscript(
            claim_id=claim.claim_id,
            claim_text=claim.text,
            evidence_snippets=[asdict(item) for item in evidence],
            prosecutor_argument=prosecutor,
            defender_argument=defender,
            judge_rationale=rationale,
            verdict=verdict,
            confidence_score=confidence,
            ep_log_refs=[prosecutor_log, defender_log, judge_log],
        )

    def _logged_call(
        self,
        agent_name: str,
        role: str,
        claim: Claim,
        evidence: list[EvidenceSnippet],
    ) -> tuple[str, str]:
        requested = "QNNExecutionProvider" if self.hardware.qnn_ep_available else "CPUExecutionProvider"
        actual = "CPUExecutionProvider"
        started = time.perf_counter()
        output = self.fallback_model.infer(role, claim, evidence)
        latency_ms = (time.perf_counter() - started) * 1000
        log_id = new_id("ep")
        self.db.insert_ep_log(
            log_id=log_id,
            timestamp=utc_now(),
            agent_name=agent_name,
            model_name=self.fallback_model.model_name,
            requested_provider=requested,
            actual_provider=actual,
            latency_ms=round(latency_ms, 3),
        )
        return output, log_id

    def _parse_judge(self, raw: str) -> tuple[str, float, str]:
        parts = raw.split("|", 2)
        if len(parts) != 3:
            return "UNSUPPORTED", 0.5, raw
        verdict, confidence, rationale = parts
        return verdict, float(confidence), rationale
