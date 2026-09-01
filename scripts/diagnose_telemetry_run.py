from __future__ import annotations
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
import pandas as pd  # noqa:E402
from fabsight.config import TELEMETRY_DATA_DIR  # noqa:E402
from fabsight.rca import RCAPredictor  # noqa:E402
if __name__=="__main__":
 p=argparse.ArgumentParser(); p.add_argument("--run",required=True,dest="run_id"); a=p.parse_args(); runs=pd.read_csv(TELEMETRY_DATA_DIR/"telemetry_runs.csv"); features=pd.read_csv(TELEMETRY_DATA_DIR/"telemetry_features.csv"); row=runs[runs.run_id==a.run_id]
 if row.empty: raise SystemExit(f"Run not found: {a.run_id}")
 result=RCAPredictor().predict(features[features.run_id==a.run_id]); truth=row.iloc[0].ground_truth_cause
 print(f"FabSight Synthetic RCA Model\n\nPredicted cause: {result['predicted_cause']}\nModel confidence: {result['confidence']:.1%}\nSynthetic ground truth: {truth}\nPrediction: {'CORRECT' if truth==result['predicted_cause'] else 'INCORRECT'}\n\nTop contributors:")
 for i,x in enumerate(result["top_contributors"],1): print(f"{i}. {x['feature']} ({x['importance']:.4f})")
 print("\nThis is a synthetic educational RCA scenario, not a real production-process diagnosis.")
