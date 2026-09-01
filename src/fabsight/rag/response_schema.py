"""Structured, serializable RAG response types."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RAGSource:
    citation_id: str
    source_file: str
    page: int | None
    source_type: str
    chunk_id: str


@dataclass
class RAGResponse:
    mode: str
    answer: str
    sources: list[RAGSource]
    retrieval_query: str
    retrieved_chunks: list[dict[str, Any]]
    limitations: list[str]
    case_id: str | None = None
    observations: list[str] | None = None
    investigation_areas: list[str] | None = None
    additional_evidence: list[str] | None = None
    guardrail_flags: list[str] | None = None
    context_truncated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


LLM_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "observations": {"type": "array", "items": {"type": "string"}},
        "investigation_areas": {"type": "array", "items": {"type": "string"}},
        "additional_evidence": {"type": "array", "items": {"type": "string"}},
        "limitations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["answer", "observations", "investigation_areas", "additional_evidence", "limitations"],
}
