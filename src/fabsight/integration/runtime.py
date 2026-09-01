"""Load existing v0.1–v0.4 artifacts for case generation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from fabsight.config import DATASET_FILES, SYNTHETIC_DATA_DIR


def load_fab_tables(data_dir: Path = SYNTHETIC_DATA_DIR) -> dict[str, pd.DataFrame]:
    """Load the v0.1 synthetic tables needed for integration and validation."""
    missing = [name for name in DATASET_FILES if not (data_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing synthetic fab files: {', '.join(missing)}")
    return {Path(name).stem: pd.read_csv(data_dir / name) for name in DATASET_FILES}
