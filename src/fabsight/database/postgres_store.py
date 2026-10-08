"""PostgreSQL application records for the single-service cloud profile."""
from __future__ import annotations
import json
from typing import Any
from fabsight.database.store import VALID_ACTIONS,VALID_STATUSES,now

class PostgresInvestigationStore:
 def __init__(self,connection_string:str):
  try:
   from psycopg_pool import ConnectionPool
  except ImportError as exc:
   raise RuntimeError("Install psycopg[binary,pool] for cloud persistence.") from exc
  self.pool=ConnectionPool(connection_string,kwargs={"autocommit":True},open=True)
  self._init()
 def _init(self):
  statements=(
   "CREATE SEQUENCE IF NOT EXISTS investigation_number_seq",
   "CREATE TABLE IF NOT EXISTS investigations(investigation_id TEXT PRIMARY KEY,case_id TEXT NOT NULL,status TEXT NOT NULL,approval_status TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,completed_at TEXT)",
   "CREATE TABLE IF NOT EXISTS human_feedback(id BIGSERIAL PRIMARY KEY,investigation_id TEXT NOT NULL,action TEXT NOT NULL,author_role TEXT NOT NULL,comment TEXT NOT NULL,evidence_json TEXT,timestamp TEXT NOT NULL)",
   "CREATE TABLE IF NOT EXISTS audit_events(event_id BIGSERIAL PRIMARY KEY,investigation_id TEXT NOT NULL,timestamp TEXT NOT NULL,actor_type TEXT NOT NULL,action TEXT NOT NULL,details_json TEXT NOT NULL)",
   "CREATE TABLE IF NOT EXISTS reports(investigation_id TEXT NOT NULL,revision INTEGER NOT NULL,report_json TEXT NOT NULL,approval_status TEXT NOT NULL,generated_at TEXT NOT NULL,reviewed_by_role TEXT,review_timestamp TEXT,PRIMARY KEY(investigation_id,revision))",
  )
  with self.pool.connection() as c:
   for statement in statements:c.execute(statement)
 def _rows(self,query:str,params:tuple=())->list[dict[str,Any]]:
  from psycopg.rows import dict_row
  with self.pool.connection() as c:return list(c.execute(query,params,row_factory=dict_row).fetchall())
 def create(self,case_id:str)->dict[str,Any]:
  with self.pool.connection() as c:
   number=c.execute("SELECT nextval('investigation_number_seq')").fetchone()[0];iid=f"INV-{number:06d}";stamp=now();c.execute("INSERT INTO investigations VALUES(%s,%s,%s,%s,%s,%s,NULL)",(iid,case_id,"CREATED","DRAFT",stamp,stamp))
  self.audit(iid,"SYSTEM","INVESTIGATION_CREATED",{"case_id":case_id});return self.get(iid)
 def get(self,iid:str)->dict[str,Any]:
  rows=self._rows("SELECT * FROM investigations WHERE investigation_id=%s",(iid,))
  if not rows:raise KeyError(f"Investigation not found: {iid}")
  return rows[0]
 def list(self):return self._rows("SELECT * FROM investigations ORDER BY created_at DESC")
 def status(self,iid:str,status:str,approval:str|None=None):
  if status not in VALID_STATUSES:raise ValueError("Invalid investigation status.")
  completed=now() if status=="COMPLETED" else None
  with self.pool.connection() as c:c.execute("UPDATE investigations SET status=%s,approval_status=COALESCE(%s,approval_status),updated_at=%s,completed_at=COALESCE(%s,completed_at) WHERE investigation_id=%s",(status,approval,now(),completed,iid))
 def feedback(self,iid:str,action:str,comment:str,author_role:str="PROCESS_ENGINEER",evidence:dict|None=None):
  if action not in VALID_ACTIONS:raise ValueError("Invalid engineer action.")
  with self.pool.connection() as c:c.execute("INSERT INTO human_feedback(investigation_id,action,author_role,comment,evidence_json,timestamp) VALUES(%s,%s,%s,%s,%s,%s)",(iid,action,author_role,comment,json.dumps(evidence) if evidence else None,now()))
  self.audit(iid,"HUMAN",action,{"author_role":author_role,"comment":comment,"evidence":evidence,"provenance":"HUMAN_PROVIDED"})
 def feedback_list(self,iid:str):return self._rows("SELECT * FROM human_feedback WHERE investigation_id=%s ORDER BY id",(iid,))
 def audit(self,iid:str,actor:str,action:str,details:dict):
  with self.pool.connection() as c:c.execute("INSERT INTO audit_events(investigation_id,timestamp,actor_type,action,details_json) VALUES(%s,%s,%s,%s,%s)",(iid,now(),actor,action,json.dumps(details,default=str)))
 def audit_list(self,iid:str):return self._rows("SELECT * FROM audit_events WHERE investigation_id=%s ORDER BY event_id",(iid,))
 def save_report(self,iid:str,report:dict,approval:str="AI_GENERATED",reviewed_by:str|None=None):
  with self.pool.connection() as c:
   rev=c.execute("SELECT COALESCE(MAX(revision),0)+1 FROM reports WHERE investigation_id=%s",(iid,)).fetchone()[0];c.execute("INSERT INTO reports VALUES(%s,%s,%s,%s,%s,%s,%s)",(iid,rev,json.dumps(report,default=str),approval,now(),reviewed_by,now() if reviewed_by else None))
 def report(self,iid:str):
  rows=self._rows("SELECT * FROM reports WHERE investigation_id=%s ORDER BY revision DESC LIMIT 1",(iid,))
  if not rows:raise KeyError("Report is not available.")
  value=rows[0];value["report"]=json.loads(value.pop("report_json"));return value
 def close(self):self.pool.close()
