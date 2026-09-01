"""Small offline tests for the v0.6 retrieval foundation."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.integration.case_schema import (  # noqa: E402
    EquipmentContext,
    FabContext,
    IntegrationMetadata,
    ManufacturingCase,
    ProcessEvidence,
    VisionEvidence,
)
from fabsight.integration.provenance import CaseProvenance  # noqa: E402
from fabsight.knowledge.build import build_knowledge_base  # noqa: E402
from fabsight.knowledge.chunking import chunk_documents  # noqa: E402
from fabsight.knowledge.evaluation import evaluate_retrieval  # noqa: E402
from fabsight.knowledge.loaders import (  # noqa: E402
    KnowledgeDocument,
    discover_documents,
    load_document,
    load_documents,
)
from fabsight.knowledge.query_builder import build_case_query  # noqa: E402
from fabsight.knowledge.retriever import KnowledgeRetriever, RetrievalResult  # noqa: E402
from fabsight.knowledge.vector_store import FaissVectorStore  # noqa: E402


class TinyEmbeddings:
    """Deterministic keyword/hash embeddings that require no model download."""

    model_name = "test-tiny-embeddings"
    vocabulary = ("etch", "edge", "wafer", "cmp", "monitoring", "maintenance", "scratch")

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = []
        for text in texts:
            lower = text.lower()
            values = [float(lower.count(word)) for word in self.vocabulary]
            digest = hashlib.sha256(lower.encode()).digest()
            values.append(int.from_bytes(digest[:2], "little") / 65535 + 0.01)
            vectors.append(values)
        return np.asarray(vectors, dtype=np.float32)


def _raw_fixture(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "etch.md").write_text(
        "# Etch reference\n\nEtch process monitoring includes uniformity review and wafer inspection.",
        encoding="utf-8",
    )
    (directory / "wafer.txt").write_text(
        "A wafer edge ring is a spatial edge pattern. Scratch patterns are linear.",
        encoding="utf-8",
    )
    (directory / "skip.csv").write_text("unsupported", encoding="utf-8")
    (directory / "document_provenance.json").write_text(
        json.dumps(
            {
                "etch.md": {"source_type": "PUBLIC_REFERENCE", "topics": ["etch", "monitoring"]},
                "wafer.txt": {"source_type": "USER_PROVIDED", "topics": ["edge", "scratch"]},
            }
        ),
        encoding="utf-8",
    )


def _case() -> ManufacturingCase:
    return ManufacturingCase(
        case_id="CASE-00001",
        created_at="2025-01-01T00:00:00",
        fab_context=FabContext("WAF-1", "LOT-1", "ETCH-01", "ETCH", "EVT-1", "2025-01-01"),
        process_evidence=ProcessEvidence("SECOM-1", "FAIL", 0.8, "HIGH", ["feature_001"]),
        vision_evidence=VisionEvidence("WM811K-1", "EDGE_RING", 0.9, "HIGH", [{"class": "EDGE_RING", "probability": 0.9}]),
        equipment_context=EquipmentContext("ETCH-01", "ACTIVE", 0, [], None, []),
        evidence_status="CONSISTENT",
        provenance=CaseProvenance(),
        integration_metadata=IntegrationMetadata("test", "1", 42, "2025-01-01", "CONSISTENT"),
    )


def test_supported_documents_load_and_unsupported_skip(tmp_path: Path) -> None:
    _raw_fixture(tmp_path)
    supported, unsupported = discover_documents(tmp_path)
    assert {path.name for path in supported} == {"etch.md", "wafer.txt"}
    assert [path.name for path in unsupported] == ["skip.csv"]
    documents, summary = load_documents(tmp_path)
    assert len(documents) == 2
    assert summary["unsupported_files"] == ["skip.csv"]
    assert {item.source_type for item in documents} == {"PUBLIC_REFERENCE", "USER_PROVIDED"}
    with pytest.raises(ValueError, match="Unsupported"):
        load_document(tmp_path / "skip.csv")


def test_chunking_preserves_metadata_and_nonempty_text() -> None:
    document = KnowledgeDocument(
        text="etch monitoring " * 100,
        source_file="reference.md",
        page=4,
        document_type="MARKDOWN",
        source_type="PUBLIC_REFERENCE",
        metadata={"topics": ["etch"]},
    )
    chunks = chunk_documents([document], chunk_size=200, overlap=30)
    assert len(chunks) > 1
    assert all(chunk.text and chunk.source_file == "reference.md" for chunk in chunks)
    assert all(chunk.page == 4 and chunk.source_type == "PUBLIC_REFERENCE" for chunk in chunks)
    assert all(chunk.metadata["topics"] == ["etch"] for chunk in chunks)


def test_embedding_and_vector_store_build_search_save_reload(tmp_path: Path) -> None:
    documents = [
        KnowledgeDocument("etch process monitoring", "etch.md", None, "MARKDOWN", "PUBLIC_REFERENCE", {}),
        KnowledgeDocument("wafer edge ring inspection", "wafer.md", None, "MARKDOWN", "USER_PROVIDED", {}),
    ]
    chunks = chunk_documents(documents)
    embedder = TinyEmbeddings()
    vectors = embedder.encode([chunk.text for chunk in chunks])
    assert vectors.shape == (2, 8)
    store = FaissVectorStore.build(vectors, chunks)
    results = store.search(embedder.encode(["edge wafer"])[0], top_k=1)
    assert len(results) == 1 and results[0][0].source_file == "wafer.md"
    assert -1 <= results[0][1] <= 1
    store.save(tmp_path)
    reloaded = FaissVectorStore.load(tmp_path)
    assert reloaded.search(embedder.encode(["etch"])[0], top_k=5)


def test_retriever_returns_structured_results_and_top_k(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    processed = tmp_path / "processed"
    _raw_fixture(raw)
    build_knowledge_base(raw, processed, embedding_provider=TinyEmbeddings())
    retriever = KnowledgeRetriever(processed, TinyEmbeddings())
    one = retriever.search("wafer edge", top_k=1)
    many = retriever.search("wafer edge", top_k=10)
    assert len(one) == 1 and len(many) == 2
    assert isinstance(one[0], RetrievalResult)
    assert one[0].source_file == "wafer.txt"
    assert one[0].source_type == "USER_PROVIDED"


def test_query_builder_handles_manufacturing_case() -> None:
    query = build_case_query(_case())
    assert "etch" in query and "edge ring" in query
    assert "abnormal process monitoring" in query
    assert "feature_001" not in query


def test_missing_knowledge_base_fails_gracefully(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="No knowledge-base documents found"):
        build_knowledge_base(tmp_path / "missing", tmp_path / "processed", embedding_provider=TinyEmbeddings())
    with pytest.raises(FileNotFoundError, match="Run the build script"):
        KnowledgeRetriever(tmp_path / "missing-index", TinyEmbeddings())


def test_retrieval_evaluation_runs(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    processed = tmp_path / "processed"
    reports = tmp_path / "reports"
    _raw_fixture(raw)
    build_knowledge_base(raw, processed, embedding_provider=TinyEmbeddings())
    report = evaluate_retrieval(
        KnowledgeRetriever(processed, TinyEmbeddings()),
        reports,
        top_k=2,
        queries=(
            {"query": "etch monitoring", "expected_topic": "etch"},
            {"query": "wafer scratch", "expected_topic": "scratch"},
        ),
    )
    assert report["successful_expected_topic_hits"] == 2
    assert report["hit_rate"] == 1.0
    assert (reports / "retrieval_evaluation.json").is_file()
