"""Load local PDF, Markdown, and text references with source provenance."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}
VALID_SOURCE_TYPES = {"PUBLIC_REFERENCE", "USER_PROVIDED", "SYNTHETIC_EDUCATIONAL"}
PROVENANCE_FILENAME = "document_provenance.json"


@dataclass(frozen=True)
class KnowledgeDocument:
    text: str
    source_file: str
    page: int | None
    document_type: str
    source_type: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def clean_text(text: str) -> str:
    """Normalize whitespace while retaining paragraph boundaries."""
    paragraphs = [re.sub(r"\s+", " ", item).strip() for item in re.split(r"\n\s*\n", text)]
    return "\n\n".join(item for item in paragraphs if item)


def discover_documents(raw_dir: Path) -> tuple[list[Path], list[Path]]:
    """Return supported and unsupported user-visible files in stable order."""
    if not raw_dir.is_dir():
        return [], []
    files = sorted(
        path for path in raw_dir.iterdir() if path.is_file() and path.name != PROVENANCE_FILENAME
    )
    return (
        [path for path in files if path.suffix.lower() in SUPPORTED_EXTENSIONS],
        [path for path in files if path.suffix.lower() not in SUPPORTED_EXTENSIONS and path.name != ".gitkeep"],
    )


def load_provenance_manifest(raw_dir: Path) -> dict[str, dict[str, Any]]:
    path = raw_dir / PROVENANCE_FILENAME
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Document provenance manifest must be a JSON object.")
    return value


def _source_metadata(path: Path, manifest: dict[str, dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    metadata = dict(manifest.get(path.name, {}))
    source_type = metadata.pop("source_type", "USER_PROVIDED")
    if source_type not in VALID_SOURCE_TYPES:
        raise ValueError(f"Invalid source_type for {path.name}: {source_type}")
    return source_type, metadata


def load_document(
    path: Path, manifest: dict[str, dict[str, Any]] | None = None
) -> list[KnowledgeDocument]:
    """Load one supported file; PDF output contains one document per non-empty page."""
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported knowledge document type: {path.suffix}")
    manifest = manifest or {}
    source_type, extra_metadata = _source_metadata(path, manifest)
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(path)
        documents = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = clean_text(page.extract_text() or "")
            if text:
                documents.append(
                    KnowledgeDocument(
                        text=text,
                        source_file=path.name,
                        page=page_number,
                        document_type="PDF",
                        source_type=source_type,
                        metadata=extra_metadata,
                    )
                )
        return documents
    text = clean_text(path.read_text(encoding="utf-8"))
    if not text:
        return []
    return [
        KnowledgeDocument(
            text=text,
            source_file=path.name,
            page=None,
            document_type="MARKDOWN" if path.suffix.lower() == ".md" else "TEXT",
            source_type=source_type,
            metadata=extra_metadata,
        )
    ]


def load_documents(raw_dir: Path) -> tuple[list[KnowledgeDocument], dict[str, Any]]:
    """Discover and load a folder, returning clear ingestion statistics."""
    supported, unsupported = discover_documents(raw_dir)
    manifest = load_provenance_manifest(raw_dir)
    documents = [item for path in supported for item in load_document(path, manifest)]
    return documents, {
        "files_found": len(supported) + len(unsupported),
        "supported_files": [path.name for path in supported],
        "unsupported_files": [path.name for path in unsupported],
        "files_loaded": len({item.source_file for item in documents}),
        "document_units_loaded": len(documents),
    }
