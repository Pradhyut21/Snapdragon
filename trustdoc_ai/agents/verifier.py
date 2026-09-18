"""Adversarial debate verifier."""

from __future__ import annotations

import time
from dataclasses import asdict

from trustdoc_ai.core.hardware_detect import HardwareProfile, get_hardware_profile
from trustdoc_ai.core.types import Claim, DebateTranscript, EvidenceSnippet
from trustdoc_ai.core.utils import new_id, utc_now
from trustdoc_ai.db.audit_db import AuditDB


class LocalDebateModel:
    """Deterministic local verifier used until ONNX LLM artifacts are configured.

    It is intentionally not branded as an LLM. Each role still executes through
    a separate call path and is logged independently for auditability.
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


class DebateVerifier:
    """Run Prosecutor, Defender, and Judge as distinct auditable calls."""

    def __init__(self, db: AuditDB, hardware: HardwareProfile | None = None) -> None:
        self.db = db
        self.hardware = hardware or get_hardware_profile()
        self.model = LocalDebateModel()

    def verify(self, claim: Claim, evidence: list[EvidenceSnippet]) -> DebateTranscript:
        prosecutor, prosecutor_log = self._logged_call("Prosecutor_Pass", "prosecutor", claim, evidence)
        defender, defender_log = self._logged_call("Defender_Pass", "defender", claim, evidence)
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
        output = self.model.infer(role, claim, evidence)
        latency_ms = (time.perf_counter() - started) * 1000
        log_id = new_id("ep")
        self.db.insert_ep_log(
            log_id=log_id,
            timestamp=utc_now(),
            agent_name=agent_name,
            model_name=self.model.model_name,
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
