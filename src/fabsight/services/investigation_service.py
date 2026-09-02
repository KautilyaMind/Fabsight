"""Application orchestration independent of HTTP and UI layers."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any,Callable
from langgraph.types import Command
from fabsight.agents.graph import InvestigationAgent
from fabsight.agents.human_review import HumanFeedback
from fabsight.agents.operational_graph import build_operational_graph
from fabsight.agents.persistence import CheckpointStore
from fabsight.config import CHECKPOINT_DB_PATH,FAB_DB_PATH,INTEGRATED_CASE_DIR,REQUIRE_FINAL_APPROVAL
from fabsight.database import InvestigationStore
from fabsight.integration.io import load_cases

class InvestigationService:
 def __init__(self,db_path:Path=FAB_DB_PATH,checkpoint_path:Path=CHECKPOINT_DB_PATH,agent_factory:Callable[[],Any]|None=None,cases_path:Path|None=None,require_final_approval:bool=REQUIRE_FINAL_APPROVAL):
  self.store=InvestigationStore(db_path); self.checkpoints=CheckpointStore(checkpoint_path); self.cases_path=cases_path or INTEGRATED_CASE_DIR/"cases.jsonl"; self.agent_factory=agent_factory or InvestigationAgent; self.graph=build_operational_graph(self._run_agent,self.checkpoints.saver,require_final_approval)
 def close(self):self.checkpoints.close()
 def cases(self):return load_cases(self.cases_path)
 def case(self,case_id):
  case=next((x for x in self.cases() if x.case_id==case_id),None)
  if case is None:raise KeyError(f"Case not found: {case_id}")
  return case
 def _run_agent(self,case_id):
  state=self.agent_factory().investigate(self.case(case_id)); return {k:v for k,v in state.items() if k!="case_data"}
 def create(self,case_id):self.case(case_id); return self.store.create(case_id)
 def run(self,iid):
  record=self.store.get(iid); config={"configurable":{"thread_id":iid}}
  snapshot=self.graph.get_state(config)
  if snapshot.next and record["status"]=="WAITING_FOR_HUMAN":return self.detail(iid)
  self.store.status(iid,"RUNNING"); self.store.audit(iid,"AGENT","GRAPH_RUN",{"case_id":record["case_id"]})
  result=self.graph.invoke({"investigation_id":iid,"case_id":record["case_id"],"status":"RUNNING","human_feedback":[],"approval_status":"DRAFT","reanalysis_count":0},config)
  return self._sync(iid,result,config)
 def feedback(self,iid,payload:dict):
  value=HumanFeedback.model_validate(payload); record=self.store.get(iid)
  if record["status"]!="WAITING_FOR_HUMAN":raise ValueError("Investigation is not waiting for human feedback.")
  self.store.feedback(iid,value.action,value.comment,value.author_role,value.evidence); self.store.status(iid,"RESUMED")
  config={"configurable":{"thread_id":iid}}; result=self.graph.invoke(Command(resume=value.model_dump()),config); return self._sync(iid,result,config)
 def _sync(self,iid,result,config):
  snapshot=self.graph.get_state(config); waiting=bool(snapshot.next)
  if waiting:self.store.status(iid,"WAITING_FOR_HUMAN"); self.store.audit(iid,"AGENT","HUMAN_REVIEW_REQUESTED",{"next":list(snapshot.next)})
  else:
   approval=result.get("approval_status","AI_GENERATED"); self.store.status(iid,"COMPLETED",approval); report=result.get("agent_state",{}).get("final_report");
   if report:self.store.save_report(iid,report,approval,(result.get("human_feedback") or [{}])[-1].get("author_role")); self.store.audit(iid,"SYSTEM","INVESTIGATION_COMPLETED",{"approval_status":approval})
  return self.detail(iid)
 def detail(self,iid):
  record=self.store.get(iid); config={"configurable":{"thread_id":iid}}; snapshot=self.graph.get_state(config); values=snapshot.values if snapshot else {}; return {**record,"state":values,"pending_nodes":list(snapshot.next) if snapshot else [],"human_feedback":self.store.feedback_list(iid)}
 def report(self,iid):return self.store.report(iid)
 def audit(self,iid):return self.store.audit_list(iid)
 def list(self):return self.store.list()
