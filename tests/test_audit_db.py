import json

from trustdoc_ai.db.audit_db import AuditDB


def test_migrations_create_expected_tables(tmp_path):
    db = AuditDB()
    db.connect(str(tmp_path / "audit.db"))
    db.run_migrations("trustdoc_ai/db/migrations")

    tables = {
        row["name"]
        for row in db.fetchall(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }

    assert "runs" in tables
    assert "claims" in tables
    assert "debate_transcripts" in tables
    assert "ep_indicator_log" in tables
    assert db.fetchall("SELECT version FROM schema_version") == [{"version": 1}]


def test_transcript_and_ep_log_round_trip(tmp_path):
    db = AuditDB()
    db.connect(str(tmp_path / "audit.db"))
    db.run_migrations("trustdoc_ai/db/migrations")

    db.insert_run("run-1", "2026-09-18T00:00:00Z", "RUNNING", doc_count=1)
    db.insert_document(
        "doc-1",
        "run-1",
        "invoice.txt",
        "D:/Snapdragon/trustdoc_ai/demo/docs/invoice.txt",
        "2026-09-18T00:00:01Z",
        page_count=1,
        status="COMPLETE",
    )
    db.insert_claim(
        "claim-1",
        "doc-1",
        "run-1",
        "Payment due date is 2026-10-15.",
        0,
        31,
        "2026-09-18T00:00:02Z",
        verdict="CONTRADICTED",
        confidence_score=0.82,
    )

    transcript = {
        "claim_text": "Payment due date is 2026-10-15.",
        "prosecutor_argument": "The purchase order says 2026-11-15.",
        "defender_argument": "The invoice itself says 2026-10-15.",
        "judge_rationale": "The document pair disagrees.",
        "verdict": "CONTRADICTED",
        "confidence_score": 0.82,
    }
    db.insert_debate_transcript(
        "transcript-1",
        "claim-1",
        json.dumps(transcript),
        "2026-09-18T00:00:03Z",
    )
    db.insert_ep_log(
        "ep-1",
        "2026-09-18T00:00:04Z",
        "Judge_Pass",
        "local_test_model",
        "QNNExecutionProvider",
        "CPUExecutionProvider",
        12.5,
    )

    assert db.get_transcript_for_claim("claim-1") == transcript
    assert db.get_ep_log_recent(1)[0]["actual_provider"] == "CPUExecutionProvider"
