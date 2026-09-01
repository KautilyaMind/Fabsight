"""Readable run-level features derived without ground-truth leakage."""
from __future__ import annotations
import numpy as np,pandas as pd
from sklearn.model_selection import train_test_split
from fabsight.config import RANDOM_SEED
from fabsight.simulation.telemetry_schema import SIGNALS

GROUND_TRUTH_COLUMNS={"scenario","ground_truth_cause","ground_truth_provenance","severity","simulation_notice"}
def _slope(x:pd.Series,y:pd.Series)->float:
    return float(np.polyfit(x.to_numpy(float),y.to_numpy(float),1)[0]) if len(x)>1 else 0.0
def engineer_run_features(runs:pd.DataFrame,readings:pd.DataFrame)->pd.DataFrame:
    required={"run_id","elapsed_seconds",*SIGNALS}; missing=required-set(readings.columns)
    if missing: raise ValueError(f"Missing telemetry reading columns: {sorted(missing)}")
    rows=[]
    for run_id,group in readings.sort_values(["run_id","elapsed_seconds"]).groupby("run_id",sort=False):
        row={"run_id":run_id}
        for signal in SIGNALS:
            row[f"{signal}_mean"]=float(group[signal].mean()); row[f"{signal}_std"]=float(group[signal].std(ddof=0)); row[f"{signal}_min"]=float(group[signal].min()); row[f"{signal}_max"]=float(group[signal].max()); row[f"{signal}_range"]=row[f"{signal}_max"]-row[f"{signal}_min"]; row[f"{signal}_slope"]=_slope(group["elapsed_seconds"],group[signal])
        rows.append(row)
    features=pd.DataFrame(rows)
    safe_run_columns=[x for x in ("run_id","process_duration","tool_age_cycles","alarm_rate") if x in runs]
    return features.merge(runs[safe_run_columns],on="run_id",validate="one_to_one")

def feature_columns(frame:pd.DataFrame)->list[str]: return [c for c in frame.columns if c!="run_id" and c not in GROUND_TRUTH_COLUMNS]
def split_run_ids(runs:pd.DataFrame,seed:int=RANDOM_SEED)->dict[str,list[str]]:
    train,temp=train_test_split(runs,test_size=.30,random_state=seed,stratify=runs["ground_truth_cause"])
    validation,test=train_test_split(temp,test_size=.50,random_state=seed,stratify=temp["ground_truth_cause"])
    return {"train":train["run_id"].tolist(),"validation":validation["run_id"].tolist(),"test":test["run_id"].tolist()}
