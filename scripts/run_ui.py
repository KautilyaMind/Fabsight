import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if __name__=="__main__":raise SystemExit(subprocess.call([sys.executable,"-m","streamlit","run",str(ROOT/"app"/"streamlit_app.py"),"--server.port=8501"]))
