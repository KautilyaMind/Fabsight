"""Offline tests for the FabSight v0.2 SECOM pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.data.load_secom import load_secom  # noqa: E402
from fabsight.data.preprocess_secom import prepare_secom  # noqa: E402


def _write_fixture(raw_dir: Path, rows: int = 40) -> None:
    raw_dir.mkdir(parents=True)
    labels = np.array([-1] * 32 + [1] * 8)
    feature_rows = []
    for index in range(rows):
        missing_value = "NaN" if index % 5 == 0 else str(index % 7)
        feature_rows.append(f"{index * 0.5} {missing_value} NaN 7")
    (raw_dir / "secom.data").write_text("\n".join(feature_rows), encoding="utf-8")
    label_rows = [
        f"{label} {(index % 28) + 1:02d}/01/2025 12:00:00"
        for index, label in enumerate(labels)
    ]
    (raw_dir / "secom_labels.data").write_text("\n".join(label_rows), encoding="utf-8")


def test_loader_returns_aligned_expected_structure(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    _write_fixture(raw_dir)
    data = load_secom(raw_dir)
    assert data.shape == (40, 6)
    assert data.columns.tolist() == [
        "feature_000", "feature_001", "feature_002", "feature_003", "timestamp", "target"
    ]
    assert data["feature_000"].iloc[-1] == 19.5
    assert set(data["target"]) == {"PASS", "FAIL"}


def test_loader_rejects_misaligned_rows(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    _write_fixture(raw_dir)
    with (raw_dir / "secom_labels.data").open("a", encoding="utf-8") as labels:
        labels.write("\n-1 01/02/2025 12:00:00")
    try:
        load_secom(raw_dir)
    except ValueError as exc:
        assert "alignment" in str(exc)
    else:
        raise AssertionError("Misaligned SECOM files should fail.")


def test_preprocessing_removes_unusable_columns_and_missing_values(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    _write_fixture(raw_dir)
    result = prepare_secom(load_secom(raw_dir), tmp_path / "processed")
    assert result["summary"]["removed_columns"] == ["feature_002", "feature_003"]
    assert not result["X_train"].isna().any().any()
    assert not result["X_test"].isna().any().any()


def test_split_is_reproducible_and_stratified(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    _write_fixture(raw_dir)
    data = load_secom(raw_dir)
    first = prepare_secom(data, save_outputs=False)
    second = prepare_secom(data, save_outputs=False)
    pd.testing.assert_frame_equal(first["X_train"], second["X_train"])
    assert first["summary"]["train_class_distribution"] == {"PASS": 26, "FAIL": 6}
    assert first["summary"]["test_class_distribution"] == {"PASS": 6, "FAIL": 2}


def test_scaler_fits_training_data_only(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    _write_fixture(raw_dir)
    result = prepare_secom(load_secom(raw_dir), save_outputs=False)
    scaler = result["pipeline"].named_steps["scaler"]
    assert np.allclose(result["X_train"].mean().to_numpy(), 0.0, atol=1e-12)
    assert len(scaler.mean_) == result["summary"]["remaining_feature_count"]


def test_processed_files_exist_and_metadata_is_readable(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    output_dir = tmp_path / "processed"
    _write_fixture(raw_dir)
    prepare_secom(load_secom(raw_dir), output_dir)
    expected = {
        "X_train.csv", "X_test.csv", "y_train.csv", "y_test.csv",
        "train_metadata.csv", "test_metadata.csv", "preprocessing_summary.json",
        "preprocessing_pipeline.joblib",
    }
    assert expected == {path.name for path in output_dir.iterdir()}
    summary = json.loads((output_dir / "preprocessing_summary.json").read_text())
    assert summary["random_seed"] == 42
