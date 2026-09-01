"""Multiclass metrics, confusion matrix, and global feature importance."""
from __future__ import annotations
import json
import os,tempfile
from pathlib import Path
from typing import Any
os.environ.setdefault("MPLCONFIGDIR",str(Path(tempfile.gettempdir())/"fabsight-matplotlib"))
import joblib,matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt,pandas as pd
from sklearn.metrics import accuracy_score,classification_report,confusion_matrix,precision_recall_fscore_support
from fabsight.config import RCA_MODEL_DIR,RCA_REPORT_DIR

def evaluate_rca_model(runs:pd.DataFrame,features:pd.DataFrame,model_dir:Path=RCA_MODEL_DIR,report_dir:Path=RCA_REPORT_DIR)->dict[str,Any]:
    model=joblib.load(model_dir/"rca_model.joblib"); meta=json.loads((model_dir/"rca_model_metadata.json").read_text())
    ids=meta["splits"]["test"]; x=features.set_index("run_id").loc[ids,meta["feature_names"]]; y=runs.set_index("run_id").loc[ids,"ground_truth_cause"]; pred=model.predict(x)
    macro=precision_recall_fscore_support(y,pred,average="macro",zero_division=0); weighted=precision_recall_fscore_support(y,pred,average="weighted",zero_division=0)
    per_class=classification_report(y,pred,labels=meta["classes"],output_dict=True,zero_division=0)
    matrix=confusion_matrix(y,pred,labels=meta["classes"])
    importance=sorted(({"feature":f,"importance":float(v)} for f,v in zip(meta["feature_names"],model.feature_importances_,strict=True)),key=lambda x:x["importance"],reverse=True)
    report={"test_runs":len(ids),"accuracy":accuracy_score(y,pred),"macro_precision":macro[0],"macro_recall":macro[1],"macro_f1":macro[2],"weighted_f1":weighted[2],"classes":meta["classes"],"confusion_matrix":matrix.tolist(),"per_class":{c:per_class[c] for c in meta["classes"]},"top_feature_importances":importance[:20],"simulation_notice":"Metrics describe controlled synthetic scenarios, not real production RCA performance."}
    report_dir.mkdir(parents=True,exist_ok=True); (report_dir/"rca_evaluation.json").write_text(json.dumps(report,indent=2),encoding="utf-8"); pd.DataFrame(matrix,index=meta["classes"],columns=meta["classes"]).to_csv(report_dir/"confusion_matrix.csv")
    fig,ax=plt.subplots(figsize=(9,7)); image=ax.imshow(matrix,cmap="Blues"); ax.set_xticks(range(len(meta["classes"])),meta["classes"],rotation=45,ha="right"); ax.set_yticks(range(len(meta["classes"])),meta["classes"]); ax.set_xlabel("Predicted synthetic scenario"); ax.set_ylabel("Ground truth synthetic scenario"); fig.colorbar(image,ax=ax); fig.tight_layout(); fig.savefig(report_dir/"confusion_matrix.png",dpi=150); plt.close(fig)
    return report
