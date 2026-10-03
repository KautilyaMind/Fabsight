import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"src")]
import uvicorn

def api_port()->int:
 raw=os.getenv("PORT","8000")
 try:port=int(raw)
 except ValueError as exc:raise ValueError("PORT must be an integer.") from exc
 if not 1<=port<=65535:raise ValueError("PORT must be between 1 and 65535.")
 return port

if __name__=="__main__":uvicorn.run("api.main:app",host="0.0.0.0",port=api_port(),reload=False)
