"""Local sentence-transformer embeddings with clear offline failure handling."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import numpy as np

from fabsight.config import EMBEDDING_MODEL_DIR, EMBEDDING_MODEL_NAME


class EmbeddingProvider(Protocol):
    model_name: str

    def encode(self, texts: list[str]) -> np.ndarray: ...


class SentenceTransformerEmbeddings:
    """Lazily load a compact local model and emit normalized float32 vectors."""

    def __init__(
        self,
        model_name: str = EMBEDDING_MODEL_NAME,
        cache_dir: Path = EMBEDDING_MODEL_DIR,
    ) -> None:
        self.model_name = model_name
        try:
            from sentence_transformers import SentenceTransformer
            try:
                # Prefer the cache so routine searches make no network request.
                self._model = SentenceTransformer(
                    model_name, cache_folder=str(cache_dir), local_files_only=True
                )
            except Exception:
                # The first run may download the public model into the local cache.
                self._model = SentenceTransformer(model_name, cache_folder=str(cache_dir))
        except Exception as exc:
            raise RuntimeError(
                f"Could not load embedding model '{model_name}'. The first run requires "
                "internet access to download it; later runs use the local cache. "
                f"Original error: {exc}"
            ) from exc

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            raise ValueError("At least one text is required for embedding.")
        vectors = self._model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype=np.float32)
