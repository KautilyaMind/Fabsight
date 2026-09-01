"""Shared configuration for FabSight data and modeling workflows."""

from pathlib import Path

RANDOM_SEED = 42
NUMBER_OF_LOTS = 100
NUMBER_OF_TOOLS = 12

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_DATA_DIR = PROJECT_ROOT / "data" / "synthetic"
SECOM_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "secom"
SECOM_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "secom"
PROCESS_MODEL_DIR = PROJECT_ROOT / "models" / "process"
PROCESS_REPORT_DIR = PROJECT_ROOT / "reports" / "process_model"

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
