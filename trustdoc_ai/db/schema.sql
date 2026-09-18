-- =============================================================================
-- TrustDoc AI — Canonical SQLite Schema
-- =============================================================================
--
-- NOTE: Apply these PRAGMAs at every new connection (not just schema creation):
--   PRAGMA journal_mode = WAL;   -- Enables write-ahead logging (Req 14.4)
--   PRAGMA foreign_keys = ON;    -- Enforce referential integrity
--
-- These PRAGMAs are connection-scoped in SQLite and are NOT stored in the
-- database file, so they must be re-applied each time a connection is opened.
-- See audit_db.py for the connection helper that applies them automatically.
-- =============================================================================


-- ── Schema version tracking ──────────────────────────────────────────────────
-- Tracks which numbered migration files have been applied.
-- The lightweight migration runner in audit_db.py queries this table at startup
-- and applies any unapplied files from db/migrations/ in order.
CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER PRIMARY KEY,  -- migration number (e.g. 1, 2, 3)
    applied_at  TEXT NOT NULL         -- ISO-8601 timestamp of when it was applied
);


-- ── Pipeline run records ─────────────────────────────────────────────────────
-- One row per pipeline execution (i.e. per "Run" initiated by the user).
-- All documents and claims processed in a single run share the same run_id.
CREATE TABLE IF NOT EXISTS runs (
    run_id        TEXT PRIMARY KEY,          -- uuid4
    started_at    TEXT NOT NULL,             -- ISO-8601
    completed_at  TEXT,                      -- NULL while still running
    status        TEXT NOT NULL,             -- RUNNING | COMPLETE | FAILED
    doc_count     INTEGER DEFAULT 0,         -- total documents submitted in this run
    claim_count   INTEGER DEFAULT 0          -- total claims extracted in this run
);


-- ── Ingested document records ────────────────────────────────────────────────
-- One row per document file submitted for processing.
-- Links back to its parent run via run_id.
CREATE TABLE IF NOT EXISTS documents (
    doc_id        TEXT PRIMARY KEY,                        -- uuid4 assigned by Doc_Intel_Agent
    run_id        TEXT NOT NULL REFERENCES runs(run_id),   -- parent pipeline run
    file_name     TEXT NOT NULL,                           -- original file basename
    file_path     TEXT NOT NULL,                           -- absolute path at ingestion time
    ingestion_ts  TEXT NOT NULL,                           -- ISO-8601 timestamp
    page_count    INTEGER DEFAULT 0,                       -- number of pages detected
    status        TEXT NOT NULL                            -- PENDING | PROCESSING | COMPLETE | ERROR
);


-- ── Extracted claims ─────────────────────────────────────────────────────────
-- One row per discrete factual claim extracted by Claim_Extraction_Agent.
-- verdict and confidence_score are NULL until the Debate_Verifier completes.
CREATE TABLE IF NOT EXISTS claims (
    claim_id             TEXT PRIMARY KEY,                           -- uuid4
    doc_id               TEXT NOT NULL REFERENCES documents(doc_id), -- source document
    run_id               TEXT NOT NULL REFERENCES runs(run_id),      -- parent run
    claim_text           TEXT NOT NULL,                              -- full declarative statement
    source_offset_start  INTEGER,                                    -- char offset in source text (nullable)
    source_offset_end    INTEGER,                                    -- char offset in source text (nullable)
    verdict              TEXT,                                       -- SUPPORTED | CONTRADICTED | UNSUPPORTED
    confidence_score     REAL,                                       -- [0.0, 1.0]; NULL until judged
    created_at           TEXT NOT NULL                               -- ISO-8601
);


-- ── Full debate transcripts ───────────────────────────────────────────────────
-- Stores the complete DebateTranscript for each verified claim as a JSON blob.
-- This is a primary artifact (Req 8.5): it is NOT derivable from other tables.
-- transcript_json contains: claim_text, evidence_snippets, prosecutor_argument,
-- defender_argument, judge_rationale, verdict, confidence_score, and EP log refs.
CREATE TABLE IF NOT EXISTS debate_transcripts (
    transcript_id   TEXT PRIMARY KEY,                          -- uuid4
    claim_id        TEXT NOT NULL REFERENCES claims(claim_id), -- associated claim
    transcript_json TEXT NOT NULL,                             -- full DebateTranscript serialised to JSON
    created_at      TEXT NOT NULL                              -- ISO-8601
);


-- ── Schema validation error records ─────────────────────────────────────────
-- Stores raw JSON records that failed Schema_Mapper_Agent validation (Req 9.3).
-- Kept separate from document_results so failures are never silently discarded.
-- doc_id is nullable because some errors may occur before a doc_id is assigned.
CREATE TABLE IF NOT EXISTS schema_errors (
    error_id       TEXT PRIMARY KEY,  -- uuid4
    run_id         TEXT NOT NULL,     -- parent run (no FK: run may be partially written)
    doc_id         TEXT,              -- source document (nullable)
    raw_json       TEXT NOT NULL,     -- the unvalidated JSON payload
    error_message  TEXT NOT NULL,     -- jsonschema validation error message
    created_at     TEXT NOT NULL      -- ISO-8601
);


-- ── Human-in-the-loop review queue ──────────────────────────────────────────
-- Escalated claim records requiring human review (Req 10.2–10.6).
-- Claims land here when verdict == 'CONTRADICTED' OR confidence_score < 0.60.
-- The reviewer updates status to 'REVIEWED' and optionally adds human_annotation.
CREATE TABLE IF NOT EXISTS human_review_queue (
    queue_id            TEXT PRIMARY KEY,                          -- uuid4
    claim_id            TEXT NOT NULL REFERENCES claims(claim_id), -- escalated claim
    doc_id              TEXT NOT NULL,                             -- denormalised for quick UI filtering
    run_id              TEXT NOT NULL,                             -- denormalised for quick UI filtering
    verdict             TEXT NOT NULL,                             -- verdict at escalation time
    confidence_score    REAL,                                      -- score at escalation time
    status              TEXT NOT NULL DEFAULT 'PENDING',           -- PENDING | REVIEWED
    human_annotation    TEXT,                                      -- reviewer's free-text note (nullable)
    reviewer_action_ts  TEXT,                                      -- ISO-8601; NULL until reviewed
    escalated_at        TEXT NOT NULL                              -- ISO-8601
);


-- ── Per-inference EP indicator log ──────────────────────────────────────────
-- One row per ONNX Runtime inference call (Req 11.2–11.3).
-- Records whether the call ran on the Hexagon NPU (QNNExecutionProvider) or
-- fell back to CPU, plus the measured wall-clock latency.
CREATE TABLE IF NOT EXISTS ep_indicator_log (
    log_id              TEXT PRIMARY KEY,  -- uuid4
    timestamp           TEXT NOT NULL,     -- ISO-8601 start of inference call
    agent_name          TEXT NOT NULL,     -- e.g. "Prosecutor_Pass", "Embedding_Agent"
    model_name          TEXT NOT NULL,     -- e.g. "llama_v3_2_3b_instruct"
    requested_provider  TEXT NOT NULL,     -- "QNNExecutionProvider" | "CPUExecutionProvider"
    actual_provider     TEXT NOT NULL,     -- read from session.get_providers()[0] after init
    latency_ms          REAL               -- wall-clock inference time in ms (nullable at session init)
);


-- ── Validated document result records ────────────────────────────────────────
-- Stores the final, schema-validated JSON record produced by Schema_Mapper_Agent
-- for each document (Req 9.1, 9.4). Failed records go to schema_errors instead.
CREATE TABLE IF NOT EXISTS document_results (
    result_id    TEXT PRIMARY KEY,                           -- uuid4
    doc_id       TEXT NOT NULL REFERENCES documents(doc_id), -- source document
    run_id       TEXT NOT NULL,                              -- parent run (denormalised for filtering)
    result_json  TEXT NOT NULL,                              -- full validated JSON record
    created_at   TEXT NOT NULL                               -- ISO-8601
);
