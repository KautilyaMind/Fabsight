"""Conditional-edge routing functions."""
from fabsight.agents.state import InvestigationState

ACTION_TO_NODE={"ANALYZE_PROCESS":"analyze_process","ANALYZE_VISION":"analyze_vision","CHECK_EQUIPMENT":"check_equipment","RETRIEVE_KNOWLEDGE":"retrieve_knowledge","REVIEW_EVIDENCE":"review_evidence","FINALIZE":"generate_final_report"}
def route_plan(state: InvestigationState) -> str: return ACTION_TO_NODE[state["next_action"]]
def route_review(state: InvestigationState) -> str:
    if state.get("evidence_sufficient") or state.get("iteration_count",0)>=state.get("max_iterations",6): return "generate_final_report"
    return "plan_investigation"
