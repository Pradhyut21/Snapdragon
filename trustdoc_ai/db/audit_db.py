"""
TrustDoc AI — SQLite audit trail helper.

Provides `AuditDB`: a thin wrapper around `sqlite3` that:
- Applies WAL and foreign-key PRAGMAs on every new connection (Req 14.4)
- Runs numbered migration files from db/migrations/ (Req 14.3)
- Exposes parameterised CRUD and read methods for every audit-trail table (Req 14.1, 14.2)

All SQL uses '?' placeholders — no f-string or .format() interpolation.

Module-level factory `get_db(path)` returns a singleton per path (Req 14.1).
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Module-level singleton registry  {path: AuditDB}
# ---------------------------------------------------------------------------
_instances: dict[str, "AuditDB"] = {}

_DEFAULT_DB_PATH = Path.home() / ".trustdoc_ai" / "audit.db"


def get_db(path: str | None = None) -> "AuditDB":
    """Return a singleton ``AuditDB`` for *path*.

    If *path* is ``None`` the default location
    ``~/.trustdoc_ai/audit.db`` is used.
    """
    resolved = str(Path(path).resolve()) if path else str(_DEFAULT_DB_PATH.resolve())
    if resolved not in _instances:
        db = AuditDB()
        db.connect(resolved)
        _instances[resolved] = db
    return _instances[resolved]


# ---------------------------------------------------------------------------
# AuditDB
# ---------------------------------------------------------------------------

class AuditDB:
    """SQLite connection helper for the TrustDoc AI audit trail."""

    def __init__(self) -> None:
        self._conn: sqlite3.Connection | None = None

    # ------------------------------------------------------------------
    # 1. Connection management
    # ------------------------------------------------------------------

    def connect(self, path: str) -> None:
        """Open (or create) the SQLite database at *path*.

        Applies ``PRAGMA journal_mode = WAL`` and
        ``PRAGMA foreign_keys = ON`` immediately — these are
        connection-scoped in SQLite and must be re-applied each time.
        """
        db_path = Path(path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row  # rows accessible as dicts

        # PRAGMAs are connection-scoped — always apply on every new connection
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.commit()

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        """Thin wrapper around ``cursor.execute(sql, params)``."""
        if self._conn is None:
            raise RuntimeError("AuditDB: not connected — call connect() first")
        return self._conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict]:
        """Execute *sql* and return all rows as a list of plain dicts."""
        cursor = self.execute(sql, params)
        rows = cursor.fetchall()
        # sqlite3.Row supports dict() conversion
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # 2. Migration runner
    # ------------------------------------------------------------------

    def run_migrations(self, migrations_dir: str) -> None:
        """Apply any unapplied numbered migrations from *migrations_dir*.

        Migration files must match ``\\d{3}_*.sql`` (e.g. ``001_initial.sql``).
        Already-applied versions (tracked in ``schema_version``) are skipped.
        Each successfully applied migration is recorded in ``schema_version``.
        """
        if self._conn is None:
            raise RuntimeError("AuditDB: not connected — call connect() first")

        mig_path = Path(migrations_dir)
        if not mig_path.is_dir():
            raise FileNotFoundError(f"Migrations directory not found: {migrations_dir}")

        # Ensure schema_version table exists before querying it
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version     INTEGER PRIMARY KEY,
                applied_at  TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

        # Gather already-applied versions
        applied: set[int] = {
            row[0] for row in self._conn.execute("SELECT version FROM schema_version")
        }

        # Collect migration files matching the naming convention
        pattern = re.compile(r"^(\d{3})_.+\.sql$")
        candidates: list[tuple[int, Path]] = []
        for entry in mig_path.iterdir():
            m = pattern.match(entry.name)
            if m:
                candidates.append((int(m.group(1)), entry))

        # Sort numerically by version prefix
        candidates.sort(key=lambda t: t[0])

        for version, filepath in candidates:
            if version in applied:
                continue  # already applied

            sql_text = filepath.read_text(encoding="utf-8")
            self._conn.executescript(sql_text)  # runs the full file (may contain transactions)

            # Record this version as applied
            self._conn.execute(
                "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (?, datetime('now'))",
                (version,),
            )
            self._conn.commit()

    # ------------------------------------------------------------------
    # 3. CRUD write methods
    # ------------------------------------------------------------------

    def insert_run(
        self,
        run_id: str,
        started_at: str,
        status: str,
        doc_count: int = 0,
        claim_count: int = 0,
    ) -> None:
        """Insert a new pipeline run record."""
        self.execute(
            """
            INSERT INTO runs (run_id, started_at, status, doc_count, claim_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, started_at, status, doc_count, claim_count),
        )
        self._conn.commit()  # type: ignore[union-attr]

    def update_run(
        self,
        run_id: str,
        status: str,
        completed_at: str | None = None,
        doc_count: int | None = None,
        claim_count: int | None = None,
    ) -> None:
        """Update mutable fields on an existing run record."""
        # Build the SET clause dynamically but safely (column names are literals)
        fields: list[str] = ["status = ?"]
        values: list[Any] = [status]

        if completed_at is not None:
            fields.append("completed_at = ?")
            values.append(completed_at)
        if doc_count is not None:
            fields.append("doc_count = ?")
            values.append(doc_count)
        if claim_count is not None:
            fields.append("claim_count = ?")
            values.append(claim_count)

        values.append(run_id)
        self.execute(
            f"UPDATE runs SET {', '.join(fields)} WHERE run_id = ?",  # noqa: S608 — column names are literals
            tuple(values),
        )
        self._conn.commit()  # type: ignore[union-attr]

    def insert_document(
        self,
        doc_id: str,
        run_id: str,
        file_name: str,
        file_path: str,
        ingestion_ts: str,
        page_count: int = 0,
        status: str = "PENDING",
    ) -> None:
        """Insert a new document ingestion record."""
        self.execute(
            """
            INSERT INTO documents
                (doc_id, run_id, file_name, file_path, ingestion_ts, page_count, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (doc_id, run_id, file_name, file_path, ingestion_ts, page_count, status),
        )
        self._conn.commit()  # type: ignore[union-attr]

    def insert_claim(
        self,
        claim_id: str,
        doc_id: str,
        run_id: str,
        claim_text: str,
        source_offset_start: int,
        source_offset_end: int,
        created_at: str,
        verdict: str | None = None,
        confidence_score: float | None = None,
    ) -> None:
        """Insert an extracted claim record."""
        self.execute(
            """
            INSERT INTO claims
                (claim_id, doc_id, run_id, claim_text,
                 source_offset_start, source_offset_end,
                 created_at, verdict, confidence_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                claim_id,
                doc_id,
                run_id,
                claim_text,
                source_offset_start,
                source_offset_end,
                created_at,
                verdict,
                confidence_score,
            ),
        )
        self._conn.commit()  # type: ignore[union-attr]

    def insert_debate_transcript(
        self,
        transcript_id: str,
        claim_id: str,
        transcript_json: str,
        created_at: str,
    ) -> None:
        """Insert a full debate transcript (JSON blob)."""
        self.execute(
            """
            INSERT INTO debate_transcripts (transcript_id, claim_id, transcript_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (transcript_id, claim_id, transcript_json, created_at),
        )
        self._conn.commit()  # type: ignore[union-attr]

    def insert_ep_log(
        self,
        log_id: str,
        timestamp: str,
        agent_name: str,
        model_name: str,
        requested_provider: str,
        actual_provider: str,
        latency_ms: float | None = None,
    ) -> None:
        """Insert an EP indicator log entry."""
        self.execute(
            """
            INSERT INTO ep_indicator_log
                (log_id, timestamp, agent_name, model_name,
                 requested_provider, actual_provider, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_id,
                timestamp,
                agent_name,
                model_name,
                requested_provider,
                actual_provider,
                latency_ms,
            ),
        )
        self._conn.commit()  # type: ignore[union-attr]

    def insert_hitl_item(
        self,
        queue_id: str,
        claim_id: str,
        doc_id: str,
        run_id: str,
        verdict: str,
        escalated_at: str,
        confidence_score: float | None = None,
    ) -> None:
        """Insert a new human-review queue item with status ``PENDING``."""
        self.execute(
            """
            INSERT INTO human_review_queue
                (queue_id, claim_id, doc_id, run_id, verdict,
                 confidence_score, status, escalated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?)
            """,
            (
                queue_id,
                claim_id,
                doc_id,
                run_id,
                verdict,
                confidence_score,
                escalated_at,
            ),
        )
        self._conn.commit()  # type: ignore[union-attr]

    def update_hitl_status(
        self,
        queue_id: str,
        status: str,
        human_annotation: str | None = None,
        reviewer_action_ts: str | None = None,
    ) -> None:
        """Update the status (and optionally annotation/timestamp) of a HITL queue item."""
        fields: list[str] = ["status = ?"]
        values: list[Any] = [status]

        if human_annotation is not None:
            fields.append("human_annotation = ?")
            values.append(human_annotation)
        if reviewer_action_ts is not None:
            fields.append("reviewer_action_ts = ?")
            values.append(reviewer_action_ts)

        values.append(queue_id)
        self.execute(
            f"UPDATE human_review_queue SET {', '.join(fields)} WHERE queue_id = ?",  # noqa: S608
            tuple(values),
        )
        self._conn.commit()  # type: ignore[union-attr]

    def insert_document_result(
        self,
        result_id: str,
        doc_id: str,
        run_id: str,
        result_json: str,
        created_at: str,
    ) -> None:
        """Insert a validated document result record."""
        self.execute(
            """
            INSERT INTO document_results (result_id, doc_id, run_id, result_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (result_id, doc_id, run_id, result_json, created_at),
        )
        self._conn.commit()  # type: ignore[union-attr]

    def insert_schema_error(
        self,
        error_id: str,
        run_id: str,
        raw_json: str,
        error_message: str,
        created_at: str,
        doc_id: str | None = None,
    ) -> None:
        """Insert a schema-validation error record."""
        self.execute(
            """
            INSERT INTO schema_errors
                (error_id, run_id, doc_id, raw_json, error_message, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (error_id, run_id, doc_id, raw_json, error_message, created_at),
        )
        self._conn.commit()  # type: ignore[union-attr]

    # ------------------------------------------------------------------
    # 4. Read methods
    # ------------------------------------------------------------------

    def get_claims_for_run(self, run_id: str) -> list[dict]:
        """Return all claims for *run_id* as a list of plain dicts."""
        return self.fetchall(
            "SELECT * FROM claims WHERE run_id = ? ORDER BY created_at",
            (run_id,),
        )

    def get_transcript_for_claim(self, claim_id: str) -> dict | None:
        """Return the debate transcript for *claim_id* as a parsed dict, or ``None``."""
        rows = self.fetchall(
            "SELECT transcript_json FROM debate_transcripts WHERE claim_id = ? LIMIT 1",
            (claim_id,),
        )
        if not rows:
            return None
        return json.loads(rows[0]["transcript_json"])

    def get_hitl_queue(
        self,
        run_id: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        """Return HITL queue items, optionally filtered by *run_id* and/or *status*."""
        conditions: list[str] = []
        params: list[Any] = []

        if run_id is not None:
            conditions.append("run_id = ?")
            params.append(run_id)
        if status is not None:
            conditions.append("status = ?")
            params.append(status)

        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        return self.fetchall(
            f"SELECT * FROM human_review_queue {where_clause} ORDER BY escalated_at DESC",  # noqa: S608
            tuple(params),
        )

    def get_ep_log_recent(self, n: int = 50) -> list[dict]:
        """Return the *n* most recent EP log entries ordered by timestamp DESC."""
        return self.fetchall(
            "SELECT * FROM ep_indicator_log ORDER BY timestamp DESC LIMIT ?",
            (n,),
        )

    def get_run_summary(self, run_id: str) -> dict | None:
        """Return the run record for *run_id* as a dict, or ``None`` if not found."""
        rows = self.fetchall(
            "SELECT * FROM runs WHERE run_id = ? LIMIT 1",
            (run_id,),
        )
        return rows[0] if rows else None
