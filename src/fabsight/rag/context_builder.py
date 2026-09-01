"""Bounded context assembly with explicit untrusted-reference boundaries."""

from __future__ import annotations

from dataclasses import dataclass

from fabsight.integration.case_schema import ManufacturingCase
from fabsight.knowledge.retriever import RetrievalResult


@dataclass(frozen=True)
class BuiltContext:
    text: str
    results: list[RetrievalResult]
    truncated: bool


def _case_facts(case: ManufacturingCase) -> str:
    p, v, e = case.process_evidence, case.vision_evidence, case.equipment_context
    features = ", ".join(p.top_anonymous_features[:5]) or "none listed"
    telemetry=""
    if case.telemetry_evidence and case.telemetry_evidence.rca_prediction:
        prediction=case.telemetry_evidence.rca_prediction
        telemetry=f"\nSynthetic telemetry run: {case.telemetry_evidence.run_id}\nSimulated RCA prediction: {prediction.get('predicted_cause')}\nRCA model confidence: {prediction.get('confidence',0):.1%}\nTelemetry trend summary: {case.telemetry_evidence.trend_summary or {}}\nSimulation scope: not a real production-process diagnosis"
    return f"""CASE FACTS
Case ID: {case.case_id}
Process step: {case.fab_context.process_step}
Process model: {p.prediction}
Failure probability: {p.failure_probability:.1%}
Risk: {p.risk_level}
Important anonymous variables: {features} (physical meanings unknown)
Vision pattern: {v.defect_class}
Vision confidence: {v.confidence:.1%}
Evidence status: {case.evidence_status}
Tool status: {e.tool_status}
Recent alarm count: {e.recent_alarm_count}
Maintenance days ago: {e.maintenance_days_ago}
Synthetic linkage: {case.integration_metadata.linkage_notice}{telemetry}"""


def build_rag_context(
    results: list[RetrievalResult], *, case: ManufacturingCase | None = None,
    max_context_chars: int = 12000, max_chunk_chars: int = 3000,
) -> BuiltContext:
    parts = [_case_facts(case)] if case else []
    used: list[RetrievalResult] = []
    seen: set[str] = set()
    truncated = False
    for number, result in enumerate(results, 1):
        if result.chunk_id in seen:
            continue
        seen.add(result.chunk_id)
        text = result.text[:max_chunk_chars]
        truncated |= len(text) < len(result.text)
        page = str(result.page) if result.page is not None else "not applicable"
        block = f"REFERENCE {number} [S{number}]\nSource: {result.source_file}\nPage: {page}\nSource type: {result.source_type}\nChunk ID: {result.chunk_id}\nBEGIN UNTRUSTED DOCUMENT CONTENT\n{text}\nEND UNTRUSTED DOCUMENT CONTENT"
        candidate = "\n\n".join(parts + [block])
        if len(candidate) > max_context_chars:
            truncated = True
            break
        parts.append(block)
        used.append(result)
    return BuiltContext("\n\n".join(parts), used, truncated)
