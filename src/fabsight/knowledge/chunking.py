"""Understandable overlapping character chunking with metadata preservation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from fabsight.knowledge.loaders import KnowledgeDocument


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    text: str
    source_file: str
    page: int | None
    document_type: str
    source_type: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "KnowledgeChunk":
        return cls(**value)


def chunk_documents(
    documents: list[KnowledgeDocument], *, chunk_size: int = 1000, overlap: int = 150
) -> list[KnowledgeChunk]:
    """Split text with modest overlap so boundary context is not lost."""
    if chunk_size < 100:
        raise ValueError("Chunk size must be at least 100 characters.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("Chunk overlap must be nonnegative and smaller than chunk size.")
    chunks: list[KnowledgeChunk] = []
    sequence = 1
    step = chunk_size - overlap
    for document in documents:
        for start in range(0, len(document.text), step):
            text = document.text[start : start + chunk_size].strip()
            if not text:
                continue
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"CHUNK-{sequence:06d}",
                    text=text,
                    source_file=document.source_file,
                    page=document.page,
                    document_type=document.document_type,
                    source_type=document.source_type,
                    metadata={**document.metadata, "character_start": start},
                )
            )
            sequence += 1
            if start + chunk_size >= len(document.text):
                break
    return chunks
