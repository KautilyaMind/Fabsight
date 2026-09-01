from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
import pandas as pd  # noqa:E402
from fabsight.config import TELEMETRY_DATA_DIR  # noqa:E402
from fabsight.rca.feature_engineering import engineer_run_features  # noqa:E402
from fabsight.rca.train_rca_model import train_rca_model  # noqa:E402
if __name__=="__main__":
 runs=pd.read_csv(TELEMETRY_DATA_DIR/"telemetry_runs.csv"); readings=pd.read_csv(TELEMETRY_DATA_DIR/"telemetry_readings.csv"); features=engineer_run_features(runs,readings); metadata=train_rca_model(runs,features); features.to_csv(TELEMETRY_DATA_DIR/"telemetry_features.csv",index=False); print(f"Trained {metadata['model_type']} on {len(metadata['splits']['train'])} runs with {len(metadata['feature_names'])} named synthetic features.")
