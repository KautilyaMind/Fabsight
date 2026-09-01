"""Structured optional LLM planning with deterministic fallback."""
from __future__ import annotations
import json
from typing import Any
from fabsight.agents.prompts import INVESTIGATION_SYSTEM_PROMPT, PLANNER_PROMPT
from fabsight.agents.state import Action, InvestigationState, PlannerDecision
from fabsight.rag.llm_client import LLMClient

ALLOWED_ACTIONS: set[str] = {"ANALYZE_PROCESS", "ANALYZE_VISION", "ANALYZE_TELEMETRY", "CHECK_EQUIPMENT", "RETRIEVE_KNOWLEDGE", "REVIEW_EVIDENCE", "FINALIZE"}
PLANNER_SCHEMA = {"type":"object","properties":{"next_action":{"type":"string","enum":sorted(ALLOWED_ACTIONS)},"reason":{"type":"string"},"missing_evidence":{"type":"array","items":{"type":"string"}}},"required":["next_action","reason","missing_evidence"]}

def deterministic_plan(state: InvestigationState) -> PlannerDecision:
    attempted = set(state.get("attempted_tools", []))
    choices: list[tuple[str, str, str, str]] = [
        ("process_evidence", "analyze_process", "ANALYZE_PROCESS", "process evidence"),
        ("vision_evidence", "analyze_vision", "ANALYZE_VISION", "visual evidence"),
        ("rca_evidence", "analyze_telemetry", "ANALYZE_TELEMETRY", "synthetic telemetry RCA evidence"),
        ("equipment_evidence", "get_equipment_context", "CHECK_EQUIPMENT", "equipment context"),
        ("knowledge_evidence", "retrieve_knowledge", "RETRIEVE_KNOWLEDGE", "technical references"),
    ]
    missing = [label for field, _, _, label in choices if not state.get(field) and not (field=="rca_evidence" and not getattr(state.get("case_data"),"telemetry_evidence",None))]
    if state.get("iteration_count", 0) >= state.get("max_iterations", 6):
        return {"next_action":"FINALIZE", "reason":"Maximum bounded investigation iterations reached.", "missing_evidence":missing}
    for field, tool, action, _ in choices:
        if field=="rca_evidence" and not getattr(state.get("case_data"),"telemetry_evidence",None): continue
        if not state.get(field) and tool not in attempted:
            return {"next_action":action, "reason":f"{field} has not been inspected.", "missing_evidence":missing}
    if missing:
        return {"next_action":"FINALIZE", "reason":"Missing evidence tools were attempted; finalize with explicit limitations.", "missing_evidence":missing}
    return {"next_action":"REVIEW_EVIDENCE", "reason":"Available evidence is ready for sufficiency review.", "missing_evidence":missing}

def _valid(value: Any) -> bool:
    return isinstance(value, dict) and value.get("next_action") in ALLOWED_ACTIONS and isinstance(value.get("reason"), str) and isinstance(value.get("missing_evidence"), list)

class InvestigationPlanner:
    def __init__(self, llm: LLMClient | None = None) -> None: self.llm = llm
    def plan(self, state: InvestigationState) -> tuple[PlannerDecision, bool]:
        if self.llm is None: return deterministic_plan(state), False
        summary = {"case_id":state.get("case_id"),"available_evidence":[k for k in ("process_evidence","vision_evidence","rca_evidence","equipment_evidence","knowledge_evidence") if state.get(k)],"telemetry_available":bool(getattr(state.get("case_data"),"telemetry_evidence",None)),"attempted_tools":state.get("attempted_tools",[]),"evidence_gaps":state.get("evidence_gaps",[]),"iteration_count":state.get("iteration_count",0),"max_iterations":state.get("max_iterations",6)}
        for _ in range(2):
            try:
                value=json.loads(self.llm.generate(INVESTIGATION_SYSTEM_PROMPT, f"{PLANNER_PROMPT}\n\nSTATE\n{json.dumps(summary)}", PLANNER_SCHEMA))
                if _valid(value):
                    action=value["next_action"]
                    if action=="ANALYZE_TELEMETRY" and not getattr(state.get("case_data"),"telemetry_evidence",None): break
                    mapping={"ANALYZE_PROCESS":"analyze_process","ANALYZE_VISION":"analyze_vision","ANALYZE_TELEMETRY":"analyze_telemetry","CHECK_EQUIPMENT":"get_equipment_context","RETRIEVE_KNOWLEDGE":"retrieve_knowledge"}
                    if mapping.get(action) in set(state.get("attempted_tools",[])): break
                    return value, False
            except (ValueError, TypeError, KeyError): pass
        return deterministic_plan(state), True
