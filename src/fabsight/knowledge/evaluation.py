"""Small topic-hit sanity evaluation for local retrieval."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fabsight.config import RETRIEVAL_REPORT_DIR
from fabsight.knowledge.retriever import KnowledgeRetriever

EVALUATION_QUERIES = (
    {"query": "wafer edge ring pattern", "expected_topic": "edge_ring"},
    {"query": "what is chemical mechanical planarization", "expected_topic": "cmp"},
    {"query": "etch process control and uniformity", "expected_topic": "etch"},
    {"query": "statistical process control baseline", "expected_topic": "spc"},
    {"query": "equipment maintenance and alarm chronology", "expected_topic": "maintenance"},
    {"query": "wafer map scratch spatial pattern", "expected_topic": "scratch"},
    {"query": "lithography manufacturing monitoring", "expected_topic": "lithography"},
    {"query": "investigate conflicting inspection evidence", "expected_topic": "anomaly_investigation"},
)


def evaluate_retrieval(
    retriever: KnowledgeRetriever,
    report_dir: Path = RETRIEVAL_REPORT_DIR,
    *,
    top_k: int = 3,
    queries: tuple[dict[str, str], ...] = EVALUATION_QUERIES,
) -> dict[str, Any]:
    """Measure whether an expected metadata topic appears in the top-k chunks."""
    details = []
    hits = 0
    for item in queries:
        results = retriever.search(item["query"], top_k=top_k)
        hit = any(item["expected_topic"] in result.metadata.get("topics", []) for result in results)
        hits += int(hit)
        details.append(
            {
                **item,
                "hit": hit,
                "retrieved_chunks": [result.chunk_id for result in results],
                "retrieved_sources": [result.source_file for result in results],
            }
        )
    report = {
        "evaluation_queries": len(queries),
        "top_k": top_k,
        "successful_expected_topic_hits": hits,
        "hit_rate": hits / len(queries) if queries else 0.0,
        "details": details,
        "note": "This is a basic retrieval sanity check, not a production benchmark.",
    }
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "retrieval_evaluation.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return report
