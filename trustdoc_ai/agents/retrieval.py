"""Local chunking, embedding, and retrieval."""

from __future__ import annotations

import math
import re
from collections import Counter

from trustdoc_ai.core.types import Document, EvidenceSnippet

TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _cosine(a: Counter[str], b: Counter[str]) -> float:
    common = set(a) & set(b)
    numerator = sum(a[key] * b[key] for key in common)
    denom_a = math.sqrt(sum(value * value for value in a.values()))
    denom_b = math.sqrt(sum(value * value for value in b.values()))
    if denom_a == 0 or denom_b == 0:
        return 0.0
    return numerator / (denom_a * denom_b)


class RetrievalAgent:
    """Numpy-free local vector index based on bag-of-words cosine search."""

    def __init__(self) -> None:
        self._chunks: list[tuple[Document, str, Counter[str]]] = []

    def build(self, documents: list[Document]) -> None:
        self._chunks.clear()
        for document in documents:
            for chunk in self._chunk(document.text):
                self._chunks.append((document, chunk, Counter(_tokens(chunk))))

    def query(self, text: str, top_k: int = 5) -> list[EvidenceSnippet]:
        query_vec = Counter(_tokens(text))
        scored = [
            EvidenceSnippet(
                doc_id=document.doc_id,
                doc_name=document.name,
                text=chunk,
                score=round(_cosine(query_vec, chunk_vec), 4),
            )
            for document, chunk, chunk_vec in self._chunks
        ]
        scored.sort(key=lambda item: item.score, reverse=True)
        return [item for item in scored[:top_k] if item.score > 0]

    def _chunk(self, text: str, max_chars: int = 600) -> list[str]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        chunks: list[str] = []
        current = ""
        for line in lines:
            if len(current) + len(line) + 1 > max_chars and current:
                chunks.append(current)
                current = line
            else:
                current = f"{current}\n{line}".strip()
        if current:
            chunks.append(current)
        return chunks
