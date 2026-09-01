"""Trend summaries and separate telemetry figures."""
from __future__ import annotations
import os,tempfile
from pathlib import Path
os.environ.setdefault("MPLCONFIGDIR",str(Path(tempfile.gettempdir())/"fabsight-matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt,pandas as pd
from fabsight.simulation.telemetry_schema import SIGNALS

def summarize_trends(readings:pd.DataFrame)->dict:
    ordered=readings.sort_values("elapsed_seconds"); return {signal:{"start":float(ordered[signal].iloc[0]),"end":float(ordered[signal].iloc[-1]),"change":float(ordered[signal].iloc[-1]-ordered[signal].iloc[0])} for signal in SIGNALS}
def plot_run_trends(run_id:str,readings:pd.DataFrame,output_dir:Path)->list[Path]:
    output_dir.mkdir(parents=True,exist_ok=True); paths=[]
    for signal in SIGNALS:
        fig,ax=plt.subplots(figsize=(7,4)); ax.plot(readings["elapsed_seconds"],readings[signal],marker="o"); ax.set(xlabel="Elapsed seconds",ylabel=f"{signal} (arbitrary simulation scale)",title=f"{run_id}: {signal}"); fig.tight_layout(); path=output_dir/f"{run_id}_{signal}.png"; fig.savefig(path,dpi=140); plt.close(fig); paths.append(path)
    return paths
