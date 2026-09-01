"""Build the local knowledge index and its reproducibility metadata."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fabsight.config import (
    EMBEDDING_MODEL_NAME,
    KNOWLEDGE_BASE_VERSION,
    KNOWLEDGE_CHUNK_OVERLAP,
    KNOWLEDGE_CHUNK_SIZE,
    KNOWLEDGE_PROCESSED_DIR,
    KNOWLEDGE_RAW_DIR,
)
from fabsight.knowledge.chunking import chunk_documents
from fabsight.knowledge.embeddings import EmbeddingProvider, SentenceTransformerEmbeddings
from fabsight.knowledge.loaders import SUPPORTED_EXTENSIONS, load_documents
from fabsight.knowledge.vector_store import FaissVectorStore


def build_knowledge_base(
    raw_dir: Path = KNOWLEDGE_RAW_DIR,
    processed_dir: Path = KNOWLEDGE_PROCESSED_DIR,
    *,
    embedding_provider: EmbeddingProvider | None = None,
    chunk_size: int = KNOWLEDGE_CHUNK_SIZE,
    chunk_overlap: int = KNOWLEDGE_CHUNK_OVERLAP,
) -> dict[str, Any]:
    """Load, chunk, embed, persist, and describe the complete local knowledge base."""
    documents, ingestion = load_documents(raw_dir)
    if not documents:
        extensions = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise FileNotFoundError(
            "No knowledge-base documents found.\n\n"
            f"Place supported files in:\n{raw_dir.resolve()}\n\nSupported: {extensions}"
        )
    chunks = chunk_documents(documents, chunk_size=chunk_size, overlap=chunk_overlap)
    provider = embedding_provider or SentenceTransformerEmbeddings()
    vectors = provider.encode([chunk.text for chunk in chunks])
    store = FaissVectorStore.build(vectors, chunks)
    store.save(processed_dir)
    metadata = {
        "knowledge_base_version": KNOWLEDGE_BASE_VERSION,
        "build_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "embedding_model": provider.model_name,
        "vector_store": "FAISS IndexFlatIP",
        "similarity": "inner product over normalized embeddings (cosine-style score)",
        "chunk_size_characters": chunk_size,
        "chunk_overlap_characters": chunk_overlap,
        "documents_found": ingestion["files_found"],
        "documents_loaded": ingestion["files_loaded"],
        "document_units_loaded": ingestion["document_units_loaded"],
        "unsupported_files_skipped": ingestion["unsupported_files"],
        "chunks_created": len(chunks),
        "embedding_dimensions": int(vectors.shape[1]),
        "source_type_counts": {
            source_type: sum(chunk.source_type == source_type for chunk in chunks)
            for source_type in sorted({chunk.source_type for chunk in chunks})
        },
    }
    (processed_dir / "index_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata
