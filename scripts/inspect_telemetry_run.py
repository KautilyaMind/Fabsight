from __future__ import annotations
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
import pandas as pd  # noqa:E402
from fabsight.config import RCA_REPORT_DIR,TELEMETRY_DATA_DIR  # noqa:E402
from fabsight.rca.explain_rca import plot_run_trends,summarize_trends  # noqa:E402
if __name__=="__main__":
 p=argparse.ArgumentParser(); p.add_argument("--run",required=True,dest="run_id"); a=p.parse_args(); runs=pd.read_csv(TELEMETRY_DATA_DIR/"telemetry_runs.csv"); row=runs[runs.run_id==a.run_id]
 if row.empty: raise SystemExit(f"Run not found: {a.run_id}")
 readings=pd.read_csv(TELEMETRY_DATA_DIR/"telemetry_readings.csv"); readings=readings[readings.run_id==a.run_id]; trends=summarize_trends(readings); plot_run_trends(a.run_id,readings,RCA_REPORT_DIR/"trends")
 r=row.iloc[0]; print(f"FabSight Synthetic Telemetry\n\nRun: {a.run_id}\nTool: {r.tool_id}\nScenario: {r.scenario}\nSeverity: {r.severity}\nSynthetic ground truth: {r.ground_truth_cause}\n")
 for name,value in trends.items(): print(f"{name}: start={value['start']:.3f}, end={value['end']:.3f}, change={value['change']:.3f}")
 print("\nEvaluation-only ground truth. Arbitrary educational simulation scales, not production control limits.")
