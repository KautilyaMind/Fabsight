"""Shared configuration for FabSight data and modeling workflows."""

import os
from pathlib import Path

RANDOM_SEED = 42
NUMBER_OF_LOTS = 100
NUMBER_OF_TOOLS = 12

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def _env_path(name: str, default: Path) -> Path:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    value = Path(raw).expanduser()
    return value if value.is_absolute() else PROJECT_ROOT / value

SYNTHETIC_DATA_DIR = PROJECT_ROOT / "data" / "synthetic"
SECOM_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "secom"
SECOM_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "secom"
PROCESS_MODEL_DIR = PROJECT_ROOT / "models" / "process"
PROCESS_REPORT_DIR = PROJECT_ROOT / "reports" / "process_model"
WAFER_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "wafer_maps"
WAFER_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "wafer_maps"
VISION_MODEL_DIR = PROJECT_ROOT / "models" / "vision"
VISION_REPORT_DIR = PROJECT_ROOT / "reports" / "vision_model"
INTEGRATED_CASE_DIR = PROJECT_ROOT / "data" / "integrated" / "cases"
MULTIMODAL_REPORT_DIR = PROJECT_ROOT / "reports" / "multimodal_cases"
WAFER_IMAGE_SIZE = 32
VISION_LOW_CONFIDENCE_MAX = 0.60
VISION_HIGH_CONFIDENCE_MIN = 0.80
DEFAULT_CASE_COUNT = 500
CASE_CONSISTENCY_RATE = 0.70
CASE_PAIRING_STRATEGY = "risk_pattern_consistency_v1"
CASE_PAIRING_VERSION = "1.0"
KNOWLEDGE_RAW_DIR = PROJECT_ROOT / "data" / "knowledge" / "raw"
KNOWLEDGE_PROCESSED_DIR = _env_path("VECTOR_STORE_PATH", PROJECT_ROOT / "data" / "knowledge" / "processed")
EMBEDDING_MODEL_DIR = PROJECT_ROOT / "models" / "embeddings"
RETRIEVAL_REPORT_DIR = PROJECT_ROOT / "reports" / "retrieval"
RAG_REPORT_DIR = PROJECT_ROOT / "reports" / "rag"
AGENT_REPORT_DIR = PROJECT_ROOT / "reports" / "agent"
MAX_INVESTIGATION_ITERATIONS = 6
TELEMETRY_DATA_DIR = SYNTHETIC_DATA_DIR / "telemetry"
RCA_MODEL_DIR = PROJECT_ROOT / "models" / "rca"
RCA_REPORT_DIR = PROJECT_ROOT / "reports" / "rca"
DATABASE_DIR = _env_path("FABSIGHT_DATABASE_DIR", PROJECT_ROOT / "data" / "database")
FAB_DB_PATH = _env_path("FAB_DB_PATH", DATABASE_DIR / "fabsight.db")
CHECKPOINT_DB_PATH = _env_path("CHECKPOINT_DB_PATH", DATABASE_DIR / "checkpoints.db")
VISION_REVIEW_THRESHOLD = 0.60
RCA_REVIEW_THRESHOLD = 0.55
REQUIRE_FINAL_APPROVAL = True
DEFAULT_TELEMETRY_RUNS = 2000
TELEMETRY_READINGS_PER_RUN = 12
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
KNOWLEDGE_CHUNK_SIZE = 1000
KNOWLEDGE_CHUNK_OVERLAP = 150
KNOWLEDGE_BASE_VERSION = "1.0"

# Educational demonstration thresholds, not production process-control limits.
FAILURE_THRESHOLD = 0.50
LOW_RISK_MAX = 0.30
HIGH_RISK_MIN = 0.70

DATASET_FILES = (
    "tools.csv",
    "lots.csv",
    "wafers.csv",
    "process_steps.csv",
    "process_events.csv",
    "maintenance.csv",
    "alarms.csv",
)
