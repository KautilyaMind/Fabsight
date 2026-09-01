"""Reusable probability inference for a persisted FabSight process model."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

import joblib
import numpy as np
import pandas as pd

from fabsight.config import HIGH_RISK_MIN, LOW_RISK_MAX, PROCESS_MODEL_DIR


def classify_risk(
    failure_probability: float,
    low_max: float = LOW_RISK_MAX,
    high_min: float = HIGH_RISK_MIN,
) -> str:
    """Convert probability to demonstration-only LOW, MODERATE, or HIGH risk."""
    if not 0 <= failure_probability <= 1:
        raise ValueError("Failure probability must be between 0 and 1.")
    if not 0 <= low_max <= high_min <= 1:
        raise ValueError("Risk thresholds must satisfy 0 <= low <= high <= 1.")
    if failure_probability < low_max:
        return "LOW"
    if failure_probability > high_min:
        return "HIGH"
    return "MODERATE"


class ProcessPredictor:
    """Load a persisted model and return structured PASS/FAIL probability output."""

    def __init__(self, model_dir: Path = PROCESS_MODEL_DIR) -> None:
        metadata_path = model_dir / "model_metadata.json"
        model_path = model_dir / "selected_model.joblib"
        if not metadata_path.is_file() or not model_path.is_file():
            raise FileNotFoundError("Process model artifacts are missing. Run the training script first.")
        self.metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.feature_names: list[str] = self.metadata["feature_names"]
        if not all(re.fullmatch(r"feature_\d{3}", name) for name in self.feature_names):
            raise ValueError("Model metadata contains non-anonymous feature names.")
        self.model = joblib.load(model_path)
        self.threshold = float(self.metadata["classification_threshold"])

    def _to_frame(self, sample: pd.DataFrame | pd.Series | Mapping[str, float]) -> pd.DataFrame:
        if isinstance(sample, pd.DataFrame):
            if len(sample) != 1:
                raise ValueError("Prediction input must contain exactly one row.")
            frame = sample.copy()
        elif isinstance(sample, pd.Series):
            frame = sample.to_frame().T
        elif isinstance(sample, Mapping):
            frame = pd.DataFrame([sample])
        else:
            raise TypeError("Sample must be a one-row DataFrame, Series, or mapping.")
        missing = sorted(set(self.feature_names) - set(frame.columns))
        extra = sorted(set(frame.columns) - set(self.feature_names))
        if missing or extra:
            raise ValueError(
                f"Input feature mismatch: expected {len(self.feature_names)} features; "
                f"missing {len(missing)}, extra {len(extra)}."
            )
        ordered = frame[self.feature_names].apply(pd.to_numeric, errors="coerce")
        if ordered.isna().any().any():
            raise ValueError("Prediction input contains missing or nonnumeric values.")
        return ordered

    def _top_features(self, sample: pd.DataFrame, top_n: int) -> list[str]:
        values = sample.iloc[0].to_numpy(dtype=float)
        if hasattr(self.model, "coef_"):
            influence = np.abs(np.asarray(self.model.coef_)[0] * values)
        elif hasattr(self.model, "feature_importances_"):
            influence = np.asarray(self.model.feature_importances_) * np.abs(values)
        else:
            influence = np.abs(values)
        order = np.argsort(influence)[::-1][:top_n]
        return [self.feature_names[index] for index in order]

    def predict(self, sample: pd.DataFrame | pd.Series | Mapping[str, float], top_n: int = 5) -> dict[str, Any]:
        """Return class, FAIL probability, risk, and anonymous contributors."""
        frame = self._to_frame(sample)
        fail_index = list(self.model.classes_).index("FAIL")
        probability = float(self.model.predict_proba(frame)[0, fail_index])
        return {
            "prediction": "FAIL" if probability >= self.threshold else "PASS",
            "failure_probability": probability,
            "risk_level": classify_risk(probability),
            "top_features": self._top_features(frame, top_n),
        }
