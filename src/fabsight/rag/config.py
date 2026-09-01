"""Environment-only LLM and RAG configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from fabsight.config import PROJECT_ROOT


def load_env_file(path: Path = PROJECT_ROOT / ".env") -> None:
    """Load unset variables from a simple .env file without exposing their values."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name, value = name.strip(), value.strip().strip('"').strip("'")
        if name and name not in os.environ:
            os.environ[name] = value


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    model: str
    api_key: str
    top_k: int = 5
    max_context_chars: int = 12000
    max_chunk_chars: int = 3000
    timeout_seconds: float = 60.0

    @classmethod
    def from_env(cls, *, env_file: Path | None = None) -> "LLMSettings":
        load_env_file(env_file or PROJECT_ROOT / ".env")
        provider = os.getenv("LLM_PROVIDER", "google").strip().lower()
        key = os.getenv("LLM_API_KEY", "").strip()
        if provider == "google" and not key:
            key = os.getenv("GOOGLE_API_KEY", "").strip()
        return cls(
            provider=provider,
            model=os.getenv("LLM_MODEL", "").strip(),
            api_key=key,
            top_k=int(os.getenv("RAG_TOP_K", "5")),
            max_context_chars=int(os.getenv("RAG_MAX_CONTEXT_CHARS", "12000")),
            max_chunk_chars=int(os.getenv("RAG_MAX_CHUNK_CHARS", "3000")),
            timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "60")),
        )

    def validation_error(self) -> str | None:
        missing = []
        if not self.provider:
            missing.append("LLM_PROVIDER")
        if not self.model:
            missing.append("LLM_MODEL")
        if not self.api_key:
            missing.append("LLM_API_KEY or GOOGLE_API_KEY")
        if missing:
            return "LLM generation unavailable because configuration is missing: " + ", ".join(missing) + ".\nConfigure .env using .env.example."
        if self.provider != "google":
            return f"Unsupported LLM provider: {self.provider}. This version supports google."
        return None
