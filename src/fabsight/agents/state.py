"""Shared state and structured records for one bounded investigation."""
from __future__ import annotations
import operator
from typing import Annotated, Any, Literal, TypedDict

Action = Literal["ANALYZE_PROCESS", "ANALYZE_VISION", "ANALYZE_TELEMETRY", "CHECK_EQUIPMENT", "RETRIEVE_KNOWLEDGE", "REVIEW_EVIDENCE", "FINALIZE"]

class PlannerDecision(TypedDict):
    next_action: Action
    reason: str
    missing_evidence: list[str]

class ToolCallRecord(TypedDict):
    tool_name: str
    input_summary: str
    timestamp: str
    success: bool
    output_summary: str

class Hypothesis(TypedDict):
    statement: str
    supporting_evidence: list[str]
    confidence: Literal["LOW", "MODERATE", "HIGH"]
    status: Literal["HYPOTHESIS"]
    limitations: list[str]
    provenance: Literal["DERIVED"]

class InvestigationState(TypedDict, total=False):
    case_id: str
    case_data: Any
    process_evidence: dict[str, Any] | None
    vision_evidence: dict[str, Any] | None
    telemetry_evidence: dict[str, Any] | None
    rca_evidence: dict[str, Any] | None
    equipment_evidence: dict[str, Any] | None
    knowledge_evidence: list[dict[str, Any]]
    investigation_plan: PlannerDecision
    next_action: Action
    tool_history: Annotated[list[ToolCallRecord], operator.add]
    attempted_tools: list[str]
    observations: Annotated[list[str], operator.add]
    hypotheses: list[Hypothesis]
    evidence_gaps: list[str]
    evidence_conflicts: list[str]
    confidence: str
    evidence_sufficient: bool
    iteration_count: int
    max_iterations: int
    final_report: dict[str, Any] | None
    trace: Annotated[list[str], operator.add]
    errors: Annotated[list[str], operator.add]
    provenance: dict[str, Any]
