"""Train and persist a simple Random Forest synthetic RCA classifier."""
from __future__ import annotations
import json
from pathlib import Path
import joblib,pandas as pd
from sklearn.ensemble import RandomForestClassifier
from fabsight.config import RANDOM_SEED,RCA_MODEL_DIR
from fabsight.rca.feature_engineering import feature_columns,split_run_ids

def train_rca_model(runs:pd.DataFrame,features:pd.DataFrame,model_dir:Path=RCA_MODEL_DIR)->dict:
    splits=split_run_ids(runs); labels=runs.set_index("run_id")["ground_truth_cause"]
    columns=feature_columns(features); indexed=features.set_index("run_id")
    model=RandomForestClassifier(n_estimators=220,max_depth=14,min_samples_leaf=2,class_weight="balanced",random_state=RANDOM_SEED,n_jobs=-1)
    model.fit(indexed.loc[splits["train"],columns],labels.loc[splits["train"]])
    model_dir.mkdir(parents=True,exist_ok=True); joblib.dump(model,model_dir/"rca_model.joblib")
    train_frame=indexed.loc[splits["train"],columns]
    metadata={"model_type":"RandomForestClassifier","feature_names":columns,"classes":model.classes_.tolist(),"splits":splits,"random_seed":RANDOM_SEED,"feature_reference":{"mean":{k:float(v) for k,v in train_frame.mean().items()},"std":{k:float(v) for k,v in train_frame.std(ddof=0).replace(0,1).items()}},"target":"ground_truth_cause","target_usage":"evaluation only; excluded from model inputs","source_type":"MODEL_OUTPUT"}
    (model_dir/"rca_model_metadata.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    return metadata
