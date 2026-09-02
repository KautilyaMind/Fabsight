import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"src")]
import uvicorn
if __name__=="__main__":uvicorn.run("api.main:app",host="0.0.0.0",port=8000,reload=False)
