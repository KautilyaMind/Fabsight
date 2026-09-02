"""Checkpointed supervisory graph using real LangGraph interrupt/resume."""
from __future__ import annotations
from datetime import datetime,timezone
from typing import Any,Callable,TypedDict
from langgraph.graph import END,START,StateGraph
from langgraph.types import interrupt
from fabsight.agents.human_review import review_request

class OperationalState(TypedDict,total=False):
 investigation_id:str; case_id:str; status:str; agent_state:dict[str,Any]; review_request:dict[str,Any]; human_feedback:list[dict[str,Any]]; approval_status:str; reanalysis_count:int; created_at:str; updated_at:str

def build_operational_graph(run_agent:Callable[[str],dict[str,Any]],checkpointer,require_final_approval:bool=True):
 def execute(state):
  agent=run_agent(state["case_id"]); feedback=state.get("human_feedback",[]); agent["human_feedback"]=feedback
  if feedback:agent["observations"]=[*agent.get("observations",[]),*[f"Human observation ({x.get('provenance','HUMAN_PROVIDED')}): {x.get('comment','')}" for x in feedback if x.get("comment")]]
  return {"status":"RUNNING","agent_state":agent,"updated_at":datetime.now(timezone.utc).isoformat()}
 def gate(state): return {"review_request":review_request(state["investigation_id"],state["agent_state"]),"status":"WAITING_FOR_HUMAN"}
 def request(state):
  feedback=interrupt(state["review_request"]); feedback={**feedback,"provenance":"HUMAN_PROVIDED","timestamp":datetime.now(timezone.utc).isoformat()}; return {"human_feedback":[feedback],"reanalysis_count":state.get("reanalysis_count",0)+int(feedback.get("action") in {"ADD_EVIDENCE","REQUEST_REANALYSIS"}),"status":"RESUMED","approval_status":"APPROVED" if feedback.get("action")=="APPROVE" else "REJECTED" if feedback.get("action")=="REJECT" else "AI_GENERATED"}
 def finalize(state):
  report=dict(state["agent_state"].get("final_report") or {}); feedback=state.get("human_feedback",[]); approval=state.get("approval_status","AI_GENERATED")
  if approval=="REJECTED":report["investigation_hypotheses"]=[{**x,"status":"REJECTED_BY_HUMAN"} for x in report.get("investigation_hypotheses",state["agent_state"].get("hypotheses",[]))]
  report.update({"investigation_id":state["investigation_id"],"status":"COMPLETED","human_feedback":feedback,"agent_trace":state["agent_state"].get("trace",[]),"approval_status":approval,"generated_by":"FABSIGHT_AGENT","generated_at":datetime.now(timezone.utc).isoformat(),"reviewed_by_role":feedback[-1].get("author_role") if feedback else None,"review_timestamp":datetime.now(timezone.utc).isoformat() if feedback else None}); return {"status":"COMPLETED","agent_state":{**state["agent_state"],"final_report":report},"updated_at":datetime.now(timezone.utc).isoformat()}
 def after_feedback(state):
  action=state.get("human_feedback",[{}])[-1].get("action"); return "execute_agent" if action in {"ADD_EVIDENCE","REQUEST_REANALYSIS"} and state.get("reanalysis_count",0)<1 else "finalize"
 g=StateGraph(OperationalState); g.add_node("execute_agent",execute); g.add_node("human_review_gate",gate); g.add_node("request_human_review",request); g.add_node("finalize",finalize); g.add_edge(START,"execute_agent"); g.add_edge("execute_agent","human_review_gate")
 g.add_conditional_edges("human_review_gate",lambda s:"request" if require_final_approval or s["review_request"]["reason"]!="FINAL_REPORT_APPROVAL" else "finalize",{"request":"request_human_review","finalize":"finalize"}); g.add_conditional_edges("request_human_review",after_feedback,{"execute_agent":"execute_agent","finalize":"finalize"}); g.add_edge("finalize",END); return g.compile(checkpointer=checkpointer)
