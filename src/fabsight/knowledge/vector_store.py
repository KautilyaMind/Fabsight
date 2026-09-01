"""Small persisted FAISS vector store retaining complete chunk provenance."""

from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np

from fabsight.knowledge.chunking import KnowledgeChunk


class FaissVectorStore:
    """Cosine-style search using normalized vectors and inner product."""

    def __init__(self, index: faiss.Index, chunks: list[KnowledgeChunk]) -> None:
        if index.ntotal != len(chunks):
            raise ValueError("FAISS index and chunk metadata are misaligned.")
        self.index = index
        self.chunks = chunks

    @classmethod
    def build(cls, vectors: np.ndarray, chunks: list[KnowledgeChunk]) -> "FaissVectorStore":
        matrix = np.asarray(vectors, dtype=np.float32)
        if matrix.ndim != 2 or len(matrix) != len(chunks) or not len(chunks):
            raise ValueError("Embedding matrix must align with at least one chunk.")
        faiss.normalize_L2(matrix)
        index = faiss.IndexFlatIP(matrix.shape[1])
        index.add(matrix)
        return cls(index, chunks)

    def search(self, query_vector: np.ndarray, top_k: int) -> list[tuple[KnowledgeChunk, float]]:
        if top_k < 1:
            raise ValueError("top_k must be at least one.")
        vector = np.asarray(query_vector, dtype=np.float32).reshape(1, -1)
        if vector.shape[1] != self.index.d:
            raise ValueError(f"Query dimension {vector.shape[1]} does not match index dimension {self.index.d}.")
        faiss.normalize_L2(vector)
        scores, indices = self.index.search(vector, min(top_k, len(self.chunks)))
        return [
            (self.chunks[int(index)], float(score))
            for index, score in zip(indices[0], scores[0], strict=True)
            if index >= 0
        ]

    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(directory / "knowledge.index"))
        with (directory / "chunks.jsonl").open("w", encoding="utf-8", newline="\n") as output:
            for chunk in self.chunks:
                output.write(json.dumps(chunk.to_dict(), sort_keys=True) + "\n")

    @classmethod
    def load(cls, directory: Path) -> "FaissVectorStore":
        index_path = directory / "knowledge.index"
        chunks_path = directory / "chunks.jsonl"
        if not index_path.is_file() or not chunks_path.is_file():
            raise FileNotFoundError(
                f"Knowledge index is missing from {directory}. Run the build script first."
            )
        index = faiss.read_index(str(index_path))
        chunks = [
            KnowledgeChunk.from_dict(json.loads(line))
            for line in chunks_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        return cls(index, chunks)
