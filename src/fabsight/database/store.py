"""SQLite application records separate from LangGraph checkpoint internals."""
from __future__ import annotations
import json,sqlite3
from datetime import datetime,timezone
from pathlib import Path
from typing import Any

VALID_STATUSES={"CREATED","RUNNING","WAITING_FOR_HUMAN","RESUMED","COMPLETED","FAILED","CANCELLED"}
VALID_ACTIONS={"APPROVE","REJECT","ADD_EVIDENCE","REQUEST_REANALYSIS","COMMENT"}
def now()->str:return datetime.now(timezone.utc).isoformat()

class InvestigationStore:
 def __init__(self,path:Path):
  path.parent.mkdir(parents=True,exist_ok=True); self.path=path; self._init()
 def connect(self):
  connection=sqlite3.connect(self.path); connection.row_factory=sqlite3.Row; return connection
 def _init(self):
  with self.connect() as c:
   c.executescript("""CREATE TABLE IF NOT EXISTS investigations(investigation_id TEXT PRIMARY KEY,case_id TEXT NOT NULL,status TEXT NOT NULL,approval_status TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,completed_at TEXT);CREATE TABLE IF NOT EXISTS human_feedback(id INTEGER PRIMARY KEY AUTOINCREMENT,investigation_id TEXT NOT NULL,action TEXT NOT NULL,author_role TEXT NOT NULL,comment TEXT NOT NULL,evidence_json TEXT,timestamp TEXT NOT NULL);CREATE TABLE IF NOT EXISTS audit_events(event_id INTEGER PRIMARY KEY AUTOINCREMENT,investigation_id TEXT NOT NULL,timestamp TEXT NOT NULL,actor_type TEXT NOT NULL,action TEXT NOT NULL,details_json TEXT NOT NULL);CREATE TABLE IF NOT EXISTS reports(investigation_id TEXT NOT NULL,revision INTEGER NOT NULL,report_json TEXT NOT NULL,approval_status TEXT NOT NULL,generated_at TEXT NOT NULL,reviewed_by_role TEXT,review_timestamp TEXT,PRIMARY KEY(investigation_id,revision));""")
 def create(self,case_id:str)->dict[str,Any]:
  with self.connect() as c:
   number=c.execute("SELECT COALESCE(MAX(CAST(SUBSTR(investigation_id,5) AS INTEGER)),0)+1 FROM investigations").fetchone()[0]; iid=f"INV-{number:06d}"; stamp=now(); c.execute("INSERT INTO investigations VALUES(?,?,?,?,?,?,NULL)",(iid,case_id,"CREATED","DRAFT",stamp,stamp));
  self.audit(iid,"SYSTEM","INVESTIGATION_CREATED",{"case_id":case_id}); return self.get(iid)
 def get(self,iid:str)->dict[str,Any]:
  with self.connect() as c: row=c.execute("SELECT * FROM investigations WHERE investigation_id=?",(iid,)).fetchone()
  if not row: raise KeyError(f"Investigation not found: {iid}")
  return dict(row)
 def list(self)->list[dict[str,Any]]:
  with self.connect() as c:return [dict(x) for x in c.execute("SELECT * FROM investigations ORDER BY created_at DESC")]
 def status(self,iid:str,status:str,approval:str|None=None):
  if status not in VALID_STATUSES: raise ValueError("Invalid investigation status.")
  completed=now() if status=="COMPLETED" else None
  with self.connect() as c:c.execute("UPDATE investigations SET status=?,approval_status=COALESCE(?,approval_status),updated_at=?,completed_at=COALESCE(?,completed_at) WHERE investigation_id=?",(status,approval,now(),completed,iid))
 def feedback(self,iid:str,action:str,comment:str,author_role:str="PROCESS_ENGINEER",evidence:dict|None=None):
  if action not in VALID_ACTIONS: raise ValueError("Invalid engineer action.")
  stamp=now(); payload=json.dumps(evidence) if evidence else None
  with self.connect() as c:c.execute("INSERT INTO human_feedback(investigation_id,action,author_role,comment,evidence_json,timestamp) VALUES(?,?,?,?,?,?)",(iid,action,author_role,comment,payload,stamp))
  self.audit(iid,"HUMAN",action,{"author_role":author_role,"comment":comment,"evidence":evidence,"provenance":"HUMAN_PROVIDED"})
 def feedback_list(self,iid:str):
  with self.connect() as c:return [dict(x) for x in c.execute("SELECT * FROM human_feedback WHERE investigation_id=? ORDER BY id",(iid,))]
 def audit(self,iid:str,actor:str,action:str,details:dict):
  with self.connect() as c:c.execute("INSERT INTO audit_events(investigation_id,timestamp,actor_type,action,details_json) VALUES(?,?,?,?,?)",(iid,now(),actor,action,json.dumps(details,default=str)))
 def audit_list(self,iid:str):
  with self.connect() as c:return [dict(x) for x in c.execute("SELECT * FROM audit_events WHERE investigation_id=? ORDER BY event_id",(iid,))]
 def save_report(self,iid:str,report:dict,approval:str="AI_GENERATED",reviewed_by:str|None=None):
  with self.connect() as c:
   rev=c.execute("SELECT COALESCE(MAX(revision),0)+1 FROM reports WHERE investigation_id=?",(iid,)).fetchone()[0]; c.execute("INSERT INTO reports VALUES(?,?,?,?,?,?,?)",(iid,rev,json.dumps(report,default=str),approval,now(),reviewed_by,now() if reviewed_by else None))
 def report(self,iid:str):
  with self.connect() as c:row=c.execute("SELECT * FROM reports WHERE investigation_id=? ORDER BY revision DESC LIMIT 1",(iid,)).fetchone()
  if not row: raise KeyError("Report is not available.")
  value=dict(row); value["report"]=json.loads(value.pop("report_json")); return value
