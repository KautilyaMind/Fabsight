"""Long-lived SQLite LangGraph checkpointer connection."""
import sqlite3
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver

class CheckpointStore:
 def __init__(self,path:Path):
  path.parent.mkdir(parents=True,exist_ok=True); self.connection=sqlite3.connect(path,check_same_thread=False); self.saver=SqliteSaver(self.connection)
 def close(self): self.connection.close()

class PostgresCheckpointStore:
 """Long-lived LangGraph Postgres checkpointer for a cached cloud service."""
 def __init__(self,connection_string:str):
  try:
   from langgraph.checkpoint.postgres import PostgresSaver
  except ImportError as exc:
   raise RuntimeError("Install langgraph-checkpoint-postgres for cloud persistence.") from exc
  self._context=PostgresSaver.from_conn_string(connection_string)
  self.saver=self._context.__enter__()
  self.saver.setup()
 def close(self):self._context.__exit__(None,None,None)
