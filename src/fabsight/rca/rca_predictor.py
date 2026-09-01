"""Reusable inference without exposing synthetic ground truth."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any,Mapping
import joblib,numpy as np,pandas as pd
from fabsight.config import RCA_MODEL_DIR
from fabsight.rca.feature_engineering import engineer_run_features

class RCAPredictor:
    def __init__(self,model_dir:Path=RCA_MODEL_DIR)->None:
        self.model=joblib.load(model_dir/"rca_model.joblib"); self.metadata=json.loads((model_dir/"rca_model_metadata.json").read_text()); self.feature_names=self.metadata["feature_names"]
        self.model.n_jobs=1
    def _frame(self,run:pd.DataFrame|Mapping[str,float],run_metadata:pd.DataFrame|None=None)->pd.DataFrame:
        if isinstance(run,Mapping): frame=pd.DataFrame([run])
        elif isinstance(run,pd.DataFrame) and set(self.feature_names)<=set(run.columns): frame=run.iloc[[0]].copy()
        elif isinstance(run,pd.DataFrame) and run_metadata is not None: frame=engineer_run_features(run_metadata,run)
        else: raise ValueError("Provide engineered features or telemetry readings plus safe run metadata.")
        forbidden={"ground_truth_cause","scenario","ground_truth_provenance"}&set(frame.columns)
        if forbidden: frame=frame.drop(columns=list(forbidden))
        missing=set(self.feature_names)-set(frame.columns)
        if missing: raise ValueError(f"Missing RCA features: {sorted(missing)}")
        return frame[self.feature_names]
    def predict(self,run:pd.DataFrame|Mapping[str,float],run_metadata:pd.DataFrame|None=None,top_n:int=5)->dict[str,Any]:
        frame=self._frame(run,run_metadata); probabilities=self.model.predict_proba(frame)[0]; index=int(np.argmax(probabilities)); predicted=str(self.model.classes_[index])
        reference=self.metadata.get("feature_reference",{}); means=reference.get("mean",{}); stds=reference.get("std",{})
        deviation=np.asarray([abs(float(frame.iloc[0][name])-means.get(name,0.0))/max(stds.get(name,1.0),1e-12) for name in self.feature_names])
        local_scores=self.model.feature_importances_*(.25+deviation)
        ranked=np.argsort(local_scores)[::-1][:top_n]
        severity="HIGH" if probabilities[index]>=.8 else "MODERATE" if probabilities[index]>=.55 else "LOW"
        total=float(local_scores.sum()) or 1.0
        return {"predicted_cause":predicted,"confidence":float(probabilities[index]),"severity":severity,"class_probabilities":{str(c):float(p) for c,p in zip(self.model.classes_,probabilities,strict=True)},"top_contributors":[{"feature":self.feature_names[i],"importance":float(local_scores[i]/total)} for i in ranked],"source_type":"MODEL_OUTPUT","input_source_type":"SYNTHETIC_TELEMETRY","simulation_only":True,"explanation_method":"global forest importance weighted by run-level standardized deviation"}
