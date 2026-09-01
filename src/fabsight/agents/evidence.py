"""Evidence sufficiency, conflict, and hypothesis logic."""
from __future__ import annotations
from typing import Any
from fabsight.agents.state import Hypothesis, InvestigationState

def review_evidence(state: InvestigationState) -> dict[str, Any]:
    gaps=[]
    for field,label in (("process_evidence","process evidence"),("vision_evidence","visual evidence"),("equipment_evidence","equipment context"),("knowledge_evidence","technical references")):
        if not state.get(field): gaps.append(label)
    conflicts=[]
    p,v=state.get("process_evidence"),state.get("vision_evidence")
    if p and v:
        visual_abnormal=v.get("defect_class") not in {"NONE","NO_PATTERN","NORMAL"} and v.get("confidence",0)>=0.8
        if p.get("risk_level")=="LOW" and visual_abnormal:
            conflicts.append("Evidence conflict detected: strong visual defect evidence accompanies LOW statistical process risk; do not force a single conclusion.")
        if p.get("risk_level")=="HIGH" and v.get("defect_class") in {"NONE","NO_PATTERN","NORMAL"}:
            conflicts.append("Evidence conflict detected: HIGH statistical process risk has no corresponding visual defect pattern.")
    sufficient=bool(p and (v or "analyze_vision" in state.get("attempted_tools",[])) and state.get("equipment_evidence") and state.get("knowledge_evidence"))
    available=sum(bool(state.get(x)) for x in ("process_evidence","vision_evidence","equipment_evidence","knowledge_evidence"))
    confidence="MODERATE" if sufficient and not conflicts else "LOW"
    return {"evidence_sufficient":sufficient,"confidence":confidence,"evidence_gaps":gaps,"evidence_conflicts":conflicts}

def build_hypotheses(state: InvestigationState) -> list[Hypothesis]:
    support=[]
    if state.get("process_evidence"): support.append(f"{state['process_evidence'].get('risk_level')} statistical process risk")
    if state.get("vision_evidence"): support.append(f"{state['vision_evidence'].get('defect_class')} visual pattern")
    if state.get("equipment_evidence"): support.append("synthetic equipment history reviewed")
    if state.get("knowledge_evidence"): support.append("retrieved technical references")
    statement="Available statistical, visual, equipment, and reference evidence may warrant a focused process-stability investigation."
    if state.get("evidence_conflicts"): statement="The conflicting evidence streams warrant independent validation before forming a stronger investigation hypothesis."
    return [{"statement":statement,"supporting_evidence":support,"confidence":state.get("confidence","LOW"),"status":"HYPOTHESIS","limitations":["This is not a confirmed physical root cause.","Synthetic linkage does not prove physical correlation."],"provenance":"DERIVED"}]
