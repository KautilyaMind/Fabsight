"""Non-fatal subsystem readiness checks with no secret disclosure."""
from pathlib import Path
from fabsight.config import CHECKPOINT_DB_PATH,FAB_DB_PATH,INTEGRATED_CASE_DIR,KNOWLEDGE_PROCESSED_DIR,PROCESS_MODEL_DIR,RCA_MODEL_DIR,VISION_MODEL_DIR
from fabsight.rag.config import LLMSettings
def startup_status()->dict:
 checks={"application_database":"READY" if FAB_DB_PATH.parent.exists() else "NOT_INITIALIZED","checkpoint_database":"READY" if CHECKPOINT_DB_PATH.parent.exists() else "NOT_INITIALIZED","synthetic_cases":"READY" if (INTEGRATED_CASE_DIR/"cases.jsonl").is_file() else "MISSING","process_model":"READY" if (PROCESS_MODEL_DIR/"selected_model.joblib").is_file() else "MISSING","vision_model":"READY" if (VISION_MODEL_DIR/"wafer_cnn.pt").is_file() else "MISSING","rca_model":"READY" if (RCA_MODEL_DIR/"rca_model.joblib").is_file() else "MISSING","knowledge_retrieval":"READY" if (KNOWLEDGE_PROCESSED_DIR/"knowledge.index").is_file() else "MISSING","llm":"READY" if LLMSettings.from_env().validation_error() is None else "NOT_CONFIGURED"}
 return {"status":"ok" if checks["application_database"]=="READY" else "degraded","version":"1.1","subsystems":checks,"mode":"full" if checks["llm"]=="READY" else "retrieval-only / demo"}
