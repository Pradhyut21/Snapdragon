"""Lightweight vision/layout pass."""

from __future__ import annotations

from trustdoc_ai.core.types import Document


class VisionAgent:
    """Annotate parsed documents with simple visual/layout signals.

    Scanned-page FastVLM integration belongs here. Until model artifacts are
    available, this pass records visible text cues without claiming vision-model
    inference.
    """

    def analyze(self, documents: list[Document]) -> list[Document]:
        for document in documents:
            lower = document.text.lower()
            document.layout["mentions_signature"] = "signature" in lower
            document.layout["mentions_stamp"] = "stamp" in lower
            document.layout["table_like_lines"] = sum(
                1 for line in document.text.splitlines() if "|" in line or ":" in line
            )
        return documents
