"""Operational v1.0 persistence, interrupt/resume, API, and audit tests."""
from __future__ import annotations
import json,sqlite3,sys
from pathlib import Path
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"src")]
from api.main import app  # noqa:E402
from fabsight.integration.io import save_cases  # noqa:E402
from fabsight.services import InvestigationService  # noqa:E402
from test_knowledge_retrieval import _case  # noqa:E402

class MockAgent:
 def investigate(self,case):
  return {"case_id":case.case_id,"process_evidence":{"risk_level":"HIGH"},"vision_evidence":{"defect_class":"EDGE_RING","confidence":.92},"rca_evidence":None,"equipment_evidence":{"provenance":"SYNTHETIC"},"knowledge_evidence":[{"source_file":"reference.md","source_type":"PUBLIC_REFERENCE","chunk_id":"c1"}],"observations":["Evidence reviewed."],"hypotheses":[{"statement":"Investigation hypothesis","status":"HYPOTHESIS"}],"evidence_gaps":[],"evidence_conflicts":[],"confidence":"MODERATE","iteration_count":4,"tool_history":[{"tool_name":"analyze_process","success":True}],"trace":["load_case","analyze_process","generate_final_report"],"provenance":case.provenance.to_dict(),"final_report":{"case_id":case.case_id,"limitations":["Educational simulation."],"approval_status":"AI_GENERATED"}}
def make_service(tmp_path):
 cases=tmp_path/"cases";save_cases([_case()],cases);return InvestigationService(tmp_path/"fab.db",tmp_path/"checkpoints.db",MockAgent,cases/"cases.jsonl")
def test_create_interrupt_resume_persist_and_restart(tmp_path):
 service=make_service(tmp_path); created=service.create("CASE-00001"); iid=created["investigation_id"]; assert iid.startswith("INV-")
 paused=service.run(iid); assert paused["status"]=="WAITING_FOR_HUMAN" and paused["pending_nodes"]==["request_human_review"]
 assert paused["state"]["agent_state"]["process_evidence"] and paused["state"]["agent_state"]["vision_evidence"]
 with sqlite3.connect(tmp_path/"checkpoints.db") as c: assert c.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0]>0
 completed=service.feedback(iid,{"action":"APPROVE","comment":"Approve the educational report.","author_role":"PROCESS_ENGINEER"}); assert completed["status"]=="COMPLETED"
 report=service.report(iid); assert report["approval_status"]=="APPROVED" and report["report"]["human_feedback"][0]["provenance"]=="HUMAN_PROVIDED"
 assert service.audit(iid) and service.store.feedback_list(iid)[0]["action"]=="APPROVE";service.close()
 restarted=InvestigationService(tmp_path/"fab.db",tmp_path/"checkpoints.db",MockAgent,tmp_path/"cases"/"cases.jsonl"); assert restarted.detail(iid)["status"]=="COMPLETED" and restarted.report(iid)["report"]["case_id"]=="CASE-00001";restarted.close()
def test_rejected_report_remains_stored(tmp_path):
 s=make_service(tmp_path);iid=s.create("CASE-00001")["investigation_id"];s.run(iid);result=s.feedback(iid,{"action":"REJECT","comment":"Insufficient evidence.","author_role":"QUALITY_ENGINEER"});assert result["approval_status"]=="REJECTED";saved=s.report(iid);assert saved["approval_status"]=="REJECTED" and saved["report"]["investigation_hypotheses"][0]["status"]=="REJECTED_BY_HUMAN";s.close()
def test_waiting_investigation_resumes_after_restart(tmp_path):
 s=make_service(tmp_path);iid=s.create("CASE-00001")["investigation_id"];paused=s.run(iid);assert paused["status"]=="WAITING_FOR_HUMAN";s.close()
 resumed=InvestigationService(tmp_path/"fab.db",tmp_path/"checkpoints.db",MockAgent,tmp_path/"cases"/"cases.jsonl");done=resumed.feedback(iid,{"action":"APPROVE","comment":"Resume after restart.","author_role":"PROCESS_ENGINEER"});assert done["status"]=="COMPLETED" and resumed.report(iid)["approval_status"]=="APPROVED";resumed.close()
def test_invalid_feedback_and_case_are_clear(tmp_path):
 s=make_service(tmp_path)
 try:s.create("missing")
 except KeyError as exc:assert "Case not found" in str(exc)
 else:raise AssertionError
 iid=s.create("CASE-00001")["investigation_id"]
 try:s.feedback(iid,{"action":"APPROVE"})
 except ValueError as exc:assert "not waiting" in str(exc)
 else:raise AssertionError
 s.close()
def test_api_endpoints(tmp_path):
 s=make_service(tmp_path);app.state.service=s;client=TestClient(app);health=client.get("/health").json();assert health["version"]=="1.0" and "subsystems" in health;assert client.get("/cases").status_code==200
 created=client.post("/investigations",json={"case_id":"CASE-00001"});assert created.status_code==201;iid=created.json()["investigation_id"]
 assert client.post(f"/investigations/{iid}/run").json()["status"]=="WAITING_FOR_HUMAN";assert client.post(f"/investigations/{iid}/feedback",json={"action":"APPROVE","comment":"ok"}).json()["status"]=="COMPLETED";assert client.get(f"/investigations/{iid}/report").status_code==200;assert client.get(f"/investigations/{iid}/audit").json();assert client.get("/cases/bad").status_code==404;s.close()
def test_ground_truth_and_secrets_absent(tmp_path):
 s=make_service(tmp_path);iid=s.create("CASE-00001")["investigation_id"];state=s.run(iid);serialized=json.dumps(state,default=str);assert "ground_truth_cause" not in serialized and "GOOGLE_API_KEY" not in serialized;s.close()
