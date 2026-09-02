"""Validated human-review records and interrupt rules."""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel,Field
from fabsight.config import RCA_REVIEW_THRESHOLD,VISION_REVIEW_THRESHOLD

class HumanFeedback(BaseModel):
 action:str
 comment:str=Field(default="",max_length=4000)
 author_role:str=Field(default="PROCESS_ENGINEER",pattern="^(PROCESS_ENGINEER|QUALITY_ENGINEER)$")
 evidence:dict[str,Any]|None=None
 requested_analysis:str|None=None
 def model_post_init(self,__context):
  if self.action not in {"APPROVE","REJECT","ADD_EVIDENCE","REQUEST_REANALYSIS","COMMENT"}: raise ValueError("Unsupported engineer action.")

def review_reason(agent_state:dict[str,Any])->str:
 if agent_state.get("evidence_conflicts"): return "EVIDENCE_CONFLICT"
 vision=agent_state.get("vision_evidence") or {}
 if vision and vision.get("confidence",1)>=0 and vision.get("confidence",1)<VISION_REVIEW_THRESHOLD:return "LOW_CONFIDENCE"
 rca=(agent_state.get("rca_evidence") or {}).get("rca_prediction",{})
 if rca and rca.get("confidence",1)<RCA_REVIEW_THRESHOLD:return "LOW_CONFIDENCE"
 if agent_state.get("evidence_gaps"):return "MISSING_EVIDENCE"
 return "FINAL_REPORT_APPROVAL"

def review_request(iid:str,agent_state:dict[str,Any])->dict[str,Any]:
 return {"investigation_id":iid,"reason":review_reason(agent_state),"summary":{"process_risk":(agent_state.get("process_evidence") or {}).get("risk_level"),"vision_defect":(agent_state.get("vision_evidence") or {}).get("defect_class"),"vision_confidence":(agent_state.get("vision_evidence") or {}).get("confidence"),"simulated_rca":((agent_state.get("rca_evidence") or {}).get("rca_prediction") or {}).get("predicted_cause")},"questions":["Approve the AI-generated investigation draft?","Add clearly sourced engineer evidence?","Request a bounded reanalysis?"]}
