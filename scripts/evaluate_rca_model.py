from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
import pandas as pd  # noqa:E402
from fabsight.config import TELEMETRY_DATA_DIR  # noqa:E402
from fabsight.rca.evaluate_rca_model import evaluate_rca_model  # noqa:E402
if __name__=="__main__": print(json.dumps(evaluate_rca_model(pd.read_csv(TELEMETRY_DATA_DIR/"telemetry_runs.csv"),pd.read_csv(TELEMETRY_DATA_DIR/"telemetry_features.csv")),indent=2))
