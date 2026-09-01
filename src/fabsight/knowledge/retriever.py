"""Reusable structured semantic retrieval over the local FAISS index."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from fabsight.config import KNOWLEDGE_PROCESSED_DIR
from fabsight.knowledge.embeddings import EmbeddingProvider, SentenceTransformerEmbeddings
from fabsight.knowledge.vector_store import FaissVectorStore


@dataclass(frozen=True)
class RetrievalResult:
    chunk_id: str
    text: str
    source_file: str
    page: int | None
    similarity_score: float
    source_type: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class KnowledgeRetriever:
    """Load a local index and return cited technical passages, not conclusions."""

    def __init__(
        self,
        index_dir: Path = KNOWLEDGE_PROCESSED_DIR,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self.embedding_provider = embedding_provider or SentenceTransformerEmbeddings()
        self.store = FaissVectorStore.load(index_dir)

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        query = query.strip()
        if not query:
            raise ValueError("Knowledge search query cannot be empty.")
        vector = self.embedding_provider.encode([query])[0]
        return [
            RetrievalResult(
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                source_file=chunk.source_file,
                page=chunk.page,
                similarity_score=score,
                source_type=chunk.source_type,
                metadata=chunk.metadata,
            )
            for chunk, score in self.store.search(vector, top_k)
        ]
