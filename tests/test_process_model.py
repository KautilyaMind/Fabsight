"""Fast offline tests for FabSight v0.3 training and reusable inference."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.modeling import ProcessPredictor, classify_risk, train_process_models  # noqa: E402


def _prepared_fixture(directory: Path) -> tuple[pd.DataFrame, pd.Series]:
    rng = np.random.default_rng(42)
    rows = 120
    columns = [f"feature_{number:03d}" for number in range(8)]
    X = pd.DataFrame(rng.normal(size=(rows, len(columns))), columns=columns)
    y = pd.Series(np.where(np.arange(rows) % 5 == 0, "FAIL", "PASS"), name="target")
    # Add a learnable pattern while retaining overlap between classes.
    X.loc[y == "FAIL", "feature_000"] += 1.4
    train_indices = np.arange(100)
    test_indices = np.arange(100, 120)
    directory.mkdir(parents=True)
    X.iloc[train_indices].to_csv(directory / "X_train.csv", index=False)
    y.iloc[train_indices].to_csv(directory / "y_train.csv", index=False)
    X.iloc[test_indices].to_csv(directory / "X_test.csv", index=False)
    y.iloc[test_indices].to_csv(directory / "y_test.csv", index=False)
    return X, y


def _train_fixture(tmp_path: Path) -> tuple[Path, Path, pd.DataFrame]:
    processed = tmp_path / "processed"
    model_dir = tmp_path / "models"
    X, _ = _prepared_fixture(processed)
    train_process_models(
        processed, model_dir, tmp_path / "reports", rf_estimators=20
    )
    return processed, model_dir, X


def test_training_completes_and_creates_artifacts(tmp_path: Path) -> None:
    processed, model_dir, _ = _train_fixture(tmp_path)
    assert (processed / "X_train.csv").is_file()
    assert {
        "logistic_regression.joblib",
        "random_forest.joblib",
        "selected_model.joblib",
        "model_metadata.json",
    } <= {path.name for path in model_dir.iterdir()}


def test_predictor_loads_and_returns_valid_result(tmp_path: Path) -> None:
    processed, model_dir, _ = _train_fixture(tmp_path)
    sample = pd.read_csv(processed / "X_test.csv").iloc[0]
    result = ProcessPredictor(model_dir).predict(sample)
    assert result["prediction"] in {"PASS", "FAIL"}
    assert 0 <= result["failure_probability"] <= 1
    assert result["risk_level"] in {"LOW", "MODERATE", "HIGH"}
    assert all(re.fullmatch(r"feature_\d{3}", name) for name in result["top_features"])


@pytest.mark.parametrize(
    ("probability", "expected"),
    [(0.0, "LOW"), (0.299, "LOW"), (0.30, "MODERATE"), (0.70, "MODERATE"), (0.701, "HIGH"), (1.0, "HIGH")],
)
def test_risk_classification(probability: float, expected: str) -> None:
    assert classify_risk(probability) == expected


def test_input_feature_validation_and_malformed_input(tmp_path: Path) -> None:
    processed, model_dir, _ = _train_fixture(tmp_path)
    sample = pd.read_csv(processed / "X_test.csv").iloc[0]
    predictor = ProcessPredictor(model_dir)
    with pytest.raises(ValueError, match="feature mismatch"):
        predictor.predict(sample.drop("feature_000"))
    malformed = sample.astype(object).copy()
    malformed["feature_000"] = "not-a-number"
    with pytest.raises(ValueError, match="nonnumeric"):
        predictor.predict(malformed)


def test_training_is_deterministic(tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    _prepared_fixture(processed)
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    train_process_models(processed, first_dir, tmp_path / "report1", rf_estimators=20)
    train_process_models(processed, second_dir, tmp_path / "report2", rf_estimators=20)
    X_test = pd.read_csv(processed / "X_test.csv")
    first = joblib.load(first_dir / "selected_model.joblib").predict_proba(X_test)
    second = joblib.load(second_dir / "selected_model.joblib").predict_proba(X_test)
    assert np.array_equal(first, second)
    first_metadata = json.loads((first_dir / "model_metadata.json").read_text())
    second_metadata = json.loads((second_dir / "model_metadata.json").read_text())
    assert first_metadata["selected_model"] == second_metadata["selected_model"]
