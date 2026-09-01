"""Collect reusable predictor outputs as independent evidence candidates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from fabsight.config import SECOM_PROCESSED_DIR, WAFER_PROCESSED_DIR
from fabsight.modeling import ProcessPredictor
from fabsight.vision import WaferPredictor


def collect_process_candidates(
    predictor: ProcessPredictor,
    processed_dir: Path = SECOM_PROCESSED_DIR,
) -> list[dict[str, Any]]:
    """Run ProcessPredictor over prepared test rows without attaching physical meaning."""
    features = pd.read_csv(processed_dir / "X_test.csv")
    return [
        {"sample_id": f"SECOM-TEST-{index:06d}", **predictor.predict(row)}
        for index, (_, row) in enumerate(features.iterrows())
    ]


def collect_vision_candidates(
    predictor: WaferPredictor,
    processed_dir: Path = WAFER_PROCESSED_DIR,
) -> list[dict[str, Any]]:
    """Run WaferPredictor over prepared test maps while preserving source indices."""
    with np.load(processed_dir / "test.npz") as data:
        images = data["images"]
        source_indices = data["source_indices"]
    return [
        {
            "sample_id": f"WM811K-{int(source_index):06d}",
            **predictor.predict(image),
        }
        for image, source_index in zip(images, source_indices, strict=True)
    ]
