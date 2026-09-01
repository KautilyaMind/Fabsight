"""Understandable retrieval and generation checks for v0.7."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from fabsight.config import RAG_REPORT_DIR
from fabsight.rag.citations import BRACKET_CITATION_PATTERN
from fabsight.rag.guardrails import find_guardrail_flags
from fabsight.rag.rag_chain import RAGChain

RAG_EVALUATION_QUESTIONS = (
    {"question": "What does CMP do?", "expected_topic": "cmp"},
    {"question": "What is wafer edge non-uniformity?", "expected_topic": "edge_ring"},
    {"question": "How is etch uniformity monitored?", "expected_topic": "etch"},
    {"question": "Why use statistical process control?", "expected_topic": "spc"},
    {"question": "Why review equipment maintenance history?", "expected_topic": "maintenance"},
    {"question": "What is a scratch wafer-map pattern?", "expected_topic": "scratch"},
    {"question": "How should conflicting evidence be investigated?", "expected_topic": "anomaly_investigation"},
    {"question": "What is lithography process monitoring?", "expected_topic": "lithography"},
    {"question": "Why compare neighboring lots?", "expected_topic": "monitoring"},
    {"question": "Can a wafer pattern prove physical cause?", "expected_topic": "inspection"},
)


def evaluate_rag(chain: RAGChain, report_dir: Path = RAG_REPORT_DIR, *, questions: tuple[dict[str, str], ...] = RAG_EVALUATION_QUESTIONS, response_factory: Callable[[str], Any] | None = None) -> dict[str, Any]:
    details, retrieval_hits, valid_citations, structured, violations = [], 0, 0, 0, 0
    for item in questions:
        results = chain.retriever.search(item["question"], top_k=chain.settings.top_k)
        hit = any(item["expected_topic"] in r.metadata.get("topics", []) for r in results)
        retrieval_hits += int(hit)
        try:
            response = response_factory(item["question"]) if response_factory else chain.ask(item["question"])
            source_ids = {s.citation_id for s in response.sources}
            cited = {citation.strip() for group in BRACKET_CITATION_PATTERN.findall(response.answer) for citation in group.split(",")}
            citation_valid = bool(cited) and cited <= source_ids
            success = bool(response.answer and response.sources and response.limitations)
            flags = response.guardrail_flags or find_guardrail_flags(response.answer)
        except RuntimeError as exc:
            response, citation_valid, success, flags = None, False, False, [str(exc)]
        valid_citations += int(citation_valid)
        structured += int(success)
        violations += len(flags)
        details.append({**item, "retrieval_hit": hit, "citation_valid": citation_valid, "structured_response_success": success, "guardrail_flags": flags, "retrieved_sources": [r.source_file for r in results]})
    count = len(questions)
    report = {"evaluation_questions": count, "retrieval_hit_rate": retrieval_hits / count if count else 0.0, "citation_validity_rate": valid_citations / count if count else 0.0, "structured_response_success_rate": structured / count if count else 0.0, "guardrail_violation_count": violations, "details": details, "note": "Lightweight sanity checks; not a perfect truth or groundedness evaluator."}
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "rag_evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
