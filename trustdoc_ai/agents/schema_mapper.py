"""Map pipeline outputs to a stable JSON record."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from trustdoc_ai.core.types import Claim, DebateTranscript, Document


class SchemaMapperAgent:
    def map_result(
        self,
        documents: list[Document],
        claim: Claim,
        transcript: DebateTranscript,
    ) -> dict[str, Any]:
        source = next(document for document in documents if document.doc_id == claim.doc_id)
        return {
            "claim_id": claim.claim_id,
            "source_document": {
                "doc_id": source.doc_id,
                "name": source.name,
                "path": source.path,
            },
            "claim": {
                "text": claim.text,
                "key": claim.key,
                "value": claim.value,
                "source_offset_start": claim.source_offset_start,
                "source_offset_end": claim.source_offset_end,
            },
            "verification": asdict(transcript),
        }
