"""Small graph nodes that update shared investigation state."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Callable
from fabsight.agents.evidence import review_evidence as assess_evidence
from fabsight.agents.planner import InvestigationPlanner
from fabsight.agents.report import build_final_report
from fabsight.agents.state import InvestigationState, ToolCallRecord
from fabsight.agents.tools import AgentTools

def _record(name:str,input_summary:str,success:bool,output_summary:str)->ToolCallRecord:
    return {"tool_name":name,"input_summary":input_summary,"timestamp":datetime.now(timezone.utc).isoformat(),"success":success,"output_summary":output_summary[:300]}

class AgentNodes:
    def __init__(self, tools: AgentTools, planner: InvestigationPlanner, final_synthesizer: Callable[[Any],dict[str,Any]] | None = None) -> None:
        self.tools,self.planner,self.final_synthesizer=tools,planner,final_synthesizer
    def load_case(self,state:InvestigationState)->dict[str,Any]:
        case=state["case_data"]
        if case.case_id!=state["case_id"]: raise ValueError("Requested case ID does not match loaded case.")
        return {"process_evidence":None,"vision_evidence":None,"equipment_evidence":None,"knowledge_evidence":[],"attempted_tools":[],"evidence_gaps":[],"evidence_conflicts":[],"confidence":"LOW","evidence_sufficient":False,"iteration_count":0,"final_report":None,"provenance":case.provenance.to_dict(),"trace":["load_case"]}
    def plan_investigation(self,state:InvestigationState)->dict[str,Any]:
        decision,fallback=self.planner.plan(state)
        errors=["Planner output invalid; deterministic fallback used."] if fallback else []
        return {"investigation_plan":decision,"next_action":decision["next_action"],"evidence_gaps":decision["missing_evidence"],"trace":["plan_investigation"],"errors":errors}
    def _tool(self,state:InvestigationState,name:str,field:str,call:Callable[[],Any],summary:Callable[[Any],str],observation:Callable[[Any],str])->dict[str,Any]:
        attempted=list(state.get("attempted_tools",[])); attempted.append(name)
        update={"attempted_tools":attempted,"iteration_count":state.get("iteration_count",0)+1,"trace":[name]}
        try:
            value=call(); update[field]=value; update["tool_history"]=[_record(name,state["case_id"],True,summary(value))]; update["observations"]=[observation(value)]
        except Exception as exc:
            update[field]=None; update["tool_history"]=[_record(name,state["case_id"],False,type(exc).__name__)]; update["errors"]=[f"{name} unavailable: {exc}"]; update["observations"]=[f"{name} evidence unavailable; investigation continued."]
        return update
    def analyze_process(self,state): return self._tool(state,"analyze_process","process_evidence",lambda:self.tools.analyze_process(state["case_data"]),lambda x:f"risk={x['risk_level']}",lambda x:f"Process model reports {x['risk_level']} risk with {x['failure_probability']:.1%} failure probability.")
    def analyze_vision(self,state): return self._tool(state,"analyze_vision","vision_evidence",lambda:self.tools.analyze_wafer(state["case_data"]),lambda x:f"pattern={x['defect_class']}",lambda x:f"Vision model reports {x['defect_class']} with {x['confidence']:.1%} confidence.")
    def check_equipment(self,state): return self._tool(state,"get_equipment_context","equipment_evidence",lambda:self.tools.get_equipment_context(state["case_data"]),lambda x:f"tool={x['tool_id']} alarms={x['recent_alarm_count']}",lambda x:f"Synthetic equipment context has {x['recent_alarm_count']} recent alarms and status {x['tool_status']}.")
    def retrieve_knowledge(self,state): return self._tool(state,"retrieve_knowledge","knowledge_evidence",lambda:self.tools.retrieve_knowledge(state["case_data"]),lambda x:f"chunks={len(x)}",lambda x:f"Retrieved {len(x)} technical reference chunks.")
    def review_evidence(self,state):
        result=assess_evidence(state); return {**result,"trace":["review_evidence"]}
    def generate_final_report(self,state):
        grounded=None
        if not state.get("knowledge_evidence"):
            return {"final_report":build_final_report(state,None),"trace":["generate_final_report"],"observations":["Grounded explanation skipped because reference context is unavailable."]}
        try:
            grounded=self.final_synthesizer(state["case_data"]) if self.final_synthesizer else self.tools.grounded_explanation(state["case_data"])
        except Exception as exc:
            error=f"grounded_explanation unavailable: {exc}"
            return {"final_report":build_final_report(state,None),"trace":["generate_final_report"],"errors":[error],"tool_history":[_record("grounded_explanation",state["case_id"],False,type(exc).__name__)]}
        return {"final_report":build_final_report(state,grounded),"trace":["generate_final_report"],"tool_history":[_record("grounded_explanation",state["case_id"],True,"structured grounded response")]}
