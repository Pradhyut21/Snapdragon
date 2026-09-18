-- Migration 001: Initial schema
-- Applied by: audit_db.py run_migrations()
-- Description: Creates all base tables for TrustDoc AI audit trail

BEGIN TRANSACTION;

-- ── Schema version tracking ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL
);

-- ── Pipeline runs ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS runs (
    run_id          TEXT PRIMARY KEY,   -- uuid4
    started_at      TEXT NOT NULL,      -- ISO-8601
    completed_at    TEXT,
    status          TEXT NOT NULL,      -- RUNNING | COMPLETE | FAILED
    doc_count       INTEGER DEFAULT 0,
    claim_count     INTEGER DEFAULT 0
);

-- ── Ingested documents ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS documents (
    doc_id          TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL REFERENCES runs(run_id),
    file_name       TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    ingestion_ts    TEXT NOT NULL,
    page_count      INTEGER DEFAULT 0,
    status          TEXT NOT NULL       -- PENDING | PROCESSING | COMPLETE | ERROR
);

-- ── Extracted claims ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS claims (
    claim_id            TEXT PRIMARY KEY,
    doc_id              TEXT NOT NULL REFERENCES documents(doc_id),
    run_id              TEXT NOT NULL REFERENCES runs(run_id),
    claim_text          TEXT NOT NULL,
    source_offset_start INTEGER,
    source_offset_end   INTEGER,
    verdict             TEXT,           -- SUPPORTED | CONTRADICTED | UNSUPPORTED
    confidence_score    REAL,
    created_at          TEXT NOT NULL
);

-- ── Debate transcripts ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS debate_transcripts (
    transcript_id   TEXT PRIMARY KEY,
    claim_id        TEXT NOT NULL REFERENCES claims(claim_id),
    transcript_json TEXT NOT NULL,   -- full DebateTranscript serialized to JSON
    created_at      TEXT NOT NULL
);

-- ── Schema mapper error table ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS schema_errors (
    error_id        TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,
    doc_id          TEXT,
    raw_json        TEXT NOT NULL,
    error_message   TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

-- ── Human review queue ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS human_review_queue (
    queue_id            TEXT PRIMARY KEY,
    claim_id            TEXT NOT NULL REFERENCES claims(claim_id),
    doc_id              TEXT NOT NULL,
    run_id              TEXT NOT NULL,
    verdict             TEXT NOT NULL,
    confidence_score    REAL,
    status              TEXT NOT NULL DEFAULT 'PENDING',  -- PENDING | REVIEWED
    human_annotation    TEXT,
    reviewer_action_ts  TEXT,
    escalated_at        TEXT NOT NULL
);

-- ── EP indicator log ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ep_indicator_log (
    log_id              TEXT PRIMARY KEY,
    timestamp           TEXT NOT NULL,
    agent_name          TEXT NOT NULL,
    model_name          TEXT NOT NULL,
    requested_provider  TEXT NOT NULL,
    actual_provider     TEXT NOT NULL,
    latency_ms          REAL
);

-- ── Validated document result records ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS document_results (
    result_id       TEXT PRIMARY KEY,
    doc_id          TEXT NOT NULL REFERENCES documents(doc_id),
    run_id          TEXT NOT NULL,
    result_json     TEXT NOT NULL,   -- full validated JSON record
    created_at      TEXT NOT NULL
);

-- ── Record this migration ──────────────────────────────────────────────────
INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (1, datetime('now'));

COMMIT;
