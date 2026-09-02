"""Long-lived SQLite LangGraph checkpointer connection."""
import sqlite3
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver

class CheckpointStore:
 def __init__(self,path:Path):
  path.parent.mkdir(parents=True,exist_ok=True); self.connection=sqlite3.connect(path,check_same_thread=False); self.saver=SqliteSaver(self.connection)
 def close(self): self.connection.close()
