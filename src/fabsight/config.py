"""Shared configuration for the FabSight v0.1 data generator."""

from pathlib import Path

RANDOM_SEED = 42
NUMBER_OF_LOTS = 100
NUMBER_OF_TOOLS = 12

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_DATA_DIR = PROJECT_ROOT / "data" / "synthetic"

DATASET_FILES = (
    "tools.csv",
    "lots.csv",
    "wafers.csv",
    "process_steps.csv",
    "process_events.csv",
    "maintenance.csv",
    "alarms.csv",
)
