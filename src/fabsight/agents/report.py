"""Structured final investigation report assembly."""
from __future__ import annotations
from typing import Any
from fabsight.agents.evidence import build_hypotheses
from fabsight.agents.state import InvestigationState

def build_final_report(state: InvestigationState, grounded: dict[str, Any] | None = None) -> dict[str, Any]:
    case=state["case_data"]
    knowledge=state.get("knowledge_evidence") or []
    sources=[{"citation_id":f"S{i}","source_file":r.get("source_file"),"page":r.get("page"),"source_type":r.get("source_type"),"chunk_id":r.get("chunk_id")} for i,r in enumerate(knowledge,1)]
    hypotheses=build_hypotheses(state)
    limitations=["No real-world physical root cause is confirmed.","Named telemetry relationships are synthetic educational rules, not production process physics or control limits.","Anonymous SECOM variables have unknown physical meanings.","Independent evidence records are linked synthetically.","FabSight does not replace qualified process engineers."]
    limitations.extend(f"Unavailable: {gap}." for gap in state.get("evidence_gaps",[]))
    if state.get("iteration_count",0)>=state.get("max_iterations",6): limitations.append("The bounded investigation iteration limit was reached.")
    return {"title":"FabSight Investigation Report","case_id":state["case_id"],"case_summary":{"process_step":case.fab_context.process_step,"evidence_status":case.evidence_status},"process_findings":state.get("process_evidence"),"vision_findings":state.get("vision_evidence"),"synthetic_telemetry_findings":state.get("rca_evidence"),"simulated_rca_result":state.get("rca_evidence",{}).get("rca_prediction") if state.get("rca_evidence") else None,"equipment_context":state.get("equipment_evidence"),"relevant_technical_references":sources,"grounded_explanation":grounded,"investigation_hypotheses":hypotheses,"evidence_conflicts":state.get("evidence_conflicts",[]),"additional_data_needed":state.get("evidence_gaps",[]) or ["named process telemetry from an authoritative source","temporal trends","previous-lot comparison","actual equipment-condition measurements"],"limitations":limitations,"provenance":state.get("provenance",{}),"confidence":state.get("confidence","LOW"),"tool_calls":len(state.get("tool_history",[]))+int(grounded is not None),"iteration_count":state.get("iteration_count",0)}
