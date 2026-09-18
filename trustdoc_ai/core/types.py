"""Shared data types for the TrustDoc AI pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    doc_id: str
    path: str
    name: str
    text: str
    page_count: int = 1
    layout: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceSnippet:
    doc_id: str
    doc_name: str
    text: str
    score: float


@dataclass
class Claim:
    claim_id: str
    doc_id: str
    text: str
    source_offset_start: int
    source_offset_end: int
    key: str | None = None
    value: str | None = None


@dataclass
class DebateTranscript:
    claim_id: str
    claim_text: str
    evidence_snippets: list[dict[str, Any]]
    prosecutor_argument: str
    defender_argument: str
    judge_rationale: str
    verdict: str
    confidence_score: float
    ep_log_refs: list[str]


@dataclass
class PipelineResult:
    run_id: str
    verdicts: list[dict[str, Any]]
    hitl_queue: list[dict[str, Any]]
    report_path: str
    db_path: str
    provider: dict[str, Any]
