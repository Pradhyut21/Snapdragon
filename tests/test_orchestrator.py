import json

from trustdoc_ai.orchestrator import TrustDocOrchestrator


def test_demo_pipeline_finds_planted_contradiction(tmp_path):
    db_path = tmp_path / "audit.db"
    report_path = tmp_path / "report.json"
    result = TrustDocOrchestrator(db_path=str(db_path)).run(
        [
            "trustdoc_ai/demo/docs/invoice.txt",
            "trustdoc_ai/demo/docs/purchase_order.txt",
        ],
        report_path=str(report_path),
    )

    verdicts = [
        item["verification"]["verdict"]
        for item in result.verdicts
        if item["claim"]["key"] == "payment due date"
    ]

    assert verdicts == ["CONTRADICTED", "CONTRADICTED"]
    assert len(result.hitl_queue) == 2

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["run_id"] == result.run_id
    note = report["provider"]["inference_note"]
    assert "Judge role executed on-device" in note or note.startswith("Demo verifier")
    assert report["provider"]["judge_model"] in ("nli-MiniLM2-L6-H768-ONNX", "local_rules_debate_v1")
    assert len(report["ep_log_recent"]) >= 6
