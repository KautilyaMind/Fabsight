"""Basic scenario metrics for completed agent states."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from fabsight.config import AGENT_REPORT_DIR

def evaluate_agent_states(states: list[tuple[str,dict[str,Any]]],report_dir:Path=AGENT_REPORT_DIR)->dict[str,Any]:
    details=[]
    for name,state in states:
        calls=state.get("tool_history",[]); report=state.get("final_report") or {}
        details.append({"scenario":name,"completed":bool(report),"tool_calls":len(calls),"iteration_limit_respected":state.get("iteration_count",0)<=state.get("max_iterations",6),"tool_failure_recovered":bool(state.get("errors")) and bool(report),"conflict_detected":bool(state.get("evidence_conflicts")),"citation_valid":all(s.get("citation_id","").startswith("S") for s in report.get("relevant_technical_references",[])),"structured_report":all(k in report for k in ("case_summary","investigation_hypotheses","limitations","provenance"))})
    n=len(details); failure_scenarios=[x for x in details if "failure" in x["scenario"]]; conflict_scenarios=[x for x in details if "conflict" in x["scenario"]]
    report={"scenarios":n,"successful_completion_rate":sum(x["completed"] for x in details)/n if n else 0.0,"average_tool_calls":sum(x["tool_calls"] for x in details)/n if n else 0.0,"maximum_iteration_violations":sum(not x["iteration_limit_respected"] for x in details),"tool_failure_recovery_rate":sum(x["tool_failure_recovered"] for x in failure_scenarios)/max(1,len(failure_scenarios)),"evidence_conflict_detection_rate":sum(x["conflict_detected"] for x in conflict_scenarios)/max(1,len(conflict_scenarios)),"citation_validity_rate":sum(x["citation_valid"] for x in details)/n if n else 0.0,"structured_final_report_success_rate":sum(x["structured_report"] for x in details)/n if n else 0.0,"details":details,"note":"Small deterministic scenario suite, not a causal-validity benchmark."}
    report_dir.mkdir(parents=True,exist_ok=True); (report_dir/"agent_evaluation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    return report
