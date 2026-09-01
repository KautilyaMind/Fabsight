"""Load the two aligned raw files that form the UCI SECOM dataset."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from fabsight.config import SECOM_RAW_DIR
from fabsight.data.download_secom import REQUIRED_FILES, manual_download_instructions

LABEL_MAP = {-1: "PASS", 1: "FAIL"}


def load_secom(raw_dir: Path = SECOM_RAW_DIR) -> pd.DataFrame:
    """Return features, timestamps, and readable PASS/FAIL targets in one frame.

    UCI encodes passing observations as -1 and failing observations as 1. Feature
    identities are anonymous, so neutral positional names are assigned.
    """
    feature_path, label_path = (raw_dir / name for name in REQUIRED_FILES)
    if not feature_path.is_file() or not label_path.is_file():
        raise FileNotFoundError(
            "Required SECOM files are not available.\n\n"
            + manual_download_instructions(raw_dir)
        )

    features = pd.read_csv(feature_path, sep=r"\s+", header=None, na_values="NaN")
    features.columns = [f"feature_{number:03d}" for number in range(features.shape[1])]
    labels = pd.read_csv(
        label_path,
        sep=r"\s+",
        header=None,
        names=["original_target", "date", "time"],
    )
    if len(features) != len(labels):
        raise ValueError(
            f"SECOM alignment error: {len(features)} feature rows and "
            f"{len(labels)} label rows."
        )
    unknown_labels = set(labels["original_target"].dropna().unique()) - LABEL_MAP.keys()
    if unknown_labels:
        raise ValueError(f"Unexpected SECOM target values: {sorted(unknown_labels)}")

    timestamps = pd.to_datetime(
        labels["date"] + " " + labels["time"],
        format="%d/%m/%Y %H:%M:%S",
        errors="raise",
    )
    result = features.copy()
    result["timestamp"] = timestamps
    result["target"] = labels["original_target"].map(LABEL_MAP)
    return result
