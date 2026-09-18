"""End-to-end TrustDoc AI pipeline orchestrator."""

from __future__ import annotations

import json
from pathlib import Path

from trustdoc_ai.agents.claim_extractor import ClaimExtractionAgent
from trustdoc_ai.agents.doc_intel import DocIntelAgent
from trustdoc_ai.agents.retrieval import RetrievalAgent
from trustdoc_ai.agents.schema_mapper import SchemaMapperAgent
from trustdoc_ai.agents.verifier import DebateVerifier
from trustdoc_ai.agents.vision import VisionAgent
from trustdoc_ai.core.hardware_detect import detect_hardware
from trustdoc_ai.core.types import PipelineResult
from trustdoc_ai.core.utils import new_id, utc_now
from trustdoc_ai.db.audit_db import AuditDB


class TrustDocOrchestrator:
    def __init__(self, db_path: str = "trustdoc_ai/demo/trustdoc_demo.db") -> None:
        self.db_path = db_path
        self.db = AuditDB()
        self.db.connect(db_path)
        self.db.run_migrations("trustdoc_ai/db/migrations")

    def run(self, paths: list[str], report_path: str = "trustdoc_ai/demo/output/report.json") -> PipelineResult:
        run_id = new_id("run")
        started_at = utc_now()
        self.db.insert_run(run_id, started_at, "RUNNING", doc_count=len(paths), claim_count=0)

        try:
            hardware = detect_hardware()
            documents = VisionAgent().analyze(DocIntelAgent().parse(paths))
            for document in documents:
                self.db.insert_document(
                    document.doc_id,
                    run_id,
                    document.name,
                    document.path,
                    utc_now(),
                    page_count=document.page_count,
                    status="COMPLETE",
                )

            retrieval = RetrievalAgent()
            retrieval.build(documents)

            claims = ClaimExtractionAgent().extract(documents)
            verifier = DebateVerifier(self.db, hardware)
            mapper = SchemaMapperAgent()
            verdicts: list[dict] = []

            for claim in claims:
                self.db.insert_claim(
                    claim.claim_id,
                    claim.doc_id,
                    run_id,
                    claim.text,
                    claim.source_offset_start,
                    claim.source_offset_end,
                    utc_now(),
                )
                evidence = retrieval.query(claim.text, top_k=5)
                transcript = verifier.verify(claim, evidence)
                self.db.insert_debate_transcript(
                    new_id("transcript"),
                    claim.claim_id,
                    json.dumps(transcript.__dict__),
                    utc_now(),
                )
                record = mapper.map_result(documents, claim, transcript)
                self.db.insert_document_result(
                    new_id("result"),
                    claim.doc_id,
                    run_id,
                    json.dumps(record),
                    utc_now(),
                )
                if transcript.verdict == "CONTRADICTED" or transcript.confidence_score < 0.6:
                    self.db.insert_hitl_item(
                        new_id("hitl"),
                        claim.claim_id,
                        claim.doc_id,
                        run_id,
                        transcript.verdict,
                        utc_now(),
                        confidence_score=transcript.confidence_score,
                    )
                verdicts.append(record)

            self.db.update_run(run_id, "COMPLETE", completed_at=utc_now(), claim_count=len(claims))
            hitl = self.db.get_hitl_queue(run_id=run_id)
            judge_model_active = verifier.judge_model.is_available
            inference_note = (
                f"Judge role executed on-device via ONNX Runtime ({verifier.judge_model.model_name}) with transparent EP logging."
                if judge_model_active
                else "Demo verifier used local deterministic rules fallback."
            )
            report = {
                "run_id": run_id,
                "created_at": utc_now(),
                "provider": {
                    "arch": hardware.arch,
                    "platform": hardware.platform,
                    "ort_version": hardware.ort_version,
                    "qnn_ep_available": hardware.qnn_ep_available,
                    "qnn_htp_dll_path": hardware.qnn_htp_dll_path,
                    "judge_model": verifier.judge_model.model_name if judge_model_active else "local_rules_debate_v1",
                    "inference_note": inference_note,
                },
                "documents": [document.__dict__ for document in documents],
                "verdicts": verdicts,
                "human_review_queue": hitl,
                "ep_log_recent": self.db.get_ep_log_recent(50),
            }
            output = Path(report_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2), encoding="utf-8")
            return PipelineResult(
                run_id=run_id,
                verdicts=verdicts,
                hitl_queue=hitl,
                report_path=str(output.resolve()),
                db_path=str(Path(self.db_path).resolve()),
                provider=report["provider"],
            )
        except Exception:
            self.db.update_run(run_id, "FAILED", completed_at=utc_now())
            raise
