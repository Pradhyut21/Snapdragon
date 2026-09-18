"""Claim extraction from structured text."""

from __future__ import annotations

import re

from trustdoc_ai.core.types import Claim, Document
from trustdoc_ai.core.utils import new_id

FIELD_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 _/-]{2,60})\s*:\s*(.{2,160})\s*$")
SENTENCE_RE = re.compile(r"[^.!?\n]*(?:\d{4}-\d{2}-\d{2}|\$?\d[\d,.]*|approved|rejected)[^.!?\n]*[.!?]", re.IGNORECASE)


class ClaimExtractionAgent:
    """Extract checkable factual claims using conservative local rules."""

    def extract(self, documents: list[Document]) -> list[Claim]:
        claims: list[Claim] = []
        for document in documents:
            claims.extend(self._extract_fields(document))
            claims.extend(self._extract_sentences(document))
        return claims

    def _extract_fields(self, document: Document) -> list[Claim]:
        claims: list[Claim] = []
        offset = 0
        for line in document.text.splitlines():
            match = FIELD_RE.match(line)
            if match:
                key = " ".join(match.group(1).strip().split())
                value = match.group(2).strip()
                text = f"{key} is {value}."
                claims.append(
                    Claim(
                        claim_id=new_id("claim"),
                        doc_id=document.doc_id,
                        text=text,
                        source_offset_start=offset,
                        source_offset_end=offset + len(line),
                        key=key.lower(),
                        value=value,
                    )
                )
            offset += len(line) + 1
        return claims

    def _extract_sentences(self, document: Document) -> list[Claim]:
        claims: list[Claim] = []
        for match in SENTENCE_RE.finditer(document.text):
            sentence = " ".join(match.group(0).strip().split())
            if ":" in sentence:
                continue
            claims.append(
                Claim(
                    claim_id=new_id("claim"),
                    doc_id=document.doc_id,
                    text=sentence,
                    source_offset_start=match.start(),
                    source_offset_end=match.end(),
                )
            )
        return claims
