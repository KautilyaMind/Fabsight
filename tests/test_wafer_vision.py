"""Lightweight offline tests for the standalone v0.4 wafer vision path."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.vision.load_wafer_data import load_wafer_dataset, normalize_label  # noqa: E402
from fabsight.vision.preprocess_wafer_maps import prepare_wafer_data, resize_wafer_map  # noqa: E402
from fabsight.vision.train_classifier import WaferCNN  # noqa: E402
from fabsight.vision.wafer_predictor import WaferPredictor, confidence_level  # noqa: E402


def _map(seed: int, size: int = 12) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(0, 3, size=(size, size), dtype=np.uint8)


def _pickle_fixture(path: Path) -> None:
    labels = ["Center", "Donut", "Edge-Loc"]
    rows = []
    for class_index, label in enumerate(labels):
        for item in range(10):
            rows.append({"waferMap": _map(class_index * 20 + item), "failureType": np.array([[label]])})
    rows.append({"waferMap": _map(99), "failureType": np.array([])})
    rows.append({"waferMap": _map(100), "failureType": np.array([["invented"]])})
    rows.append({"waferMap": np.array([1, 2, 3]), "failureType": np.array([["Center"]])})
    pd.DataFrame(rows).to_pickle(path)


def test_dataset_loads_labels_normalize_and_invalid_are_handled(tmp_path: Path) -> None:
    path = tmp_path / "LSWMD.pkl"
    _pickle_fixture(path)
    dataset = load_wafer_dataset(path)
    assert len(dataset.maps) == 30
    assert dataset.unlabeled_samples == 1
    assert dataset.invalid_label_samples == 1
    assert dataset.malformed_samples == 1
    assert normalize_label(np.array([["Edge-Ring"]])) == "EDGE_RING"
    assert normalize_label("invented") is None


def test_preprocessing_shape_and_reproducible_splits(tmp_path: Path) -> None:
    path = tmp_path / "LSWMD.pkl"
    _pickle_fixture(path)
    dataset = load_wafer_dataset(path)
    first = prepare_wafer_data(dataset, save_outputs=False)
    second = prepare_wafer_data(dataset, save_outputs=False)
    assert first["images"].shape == (30, 32, 32)
    for split in ("train", "validation", "test"):
        assert np.array_equal(first["splits"][split], second["splits"][split])


def test_resize_rejects_malformed_map() -> None:
    with pytest.raises(ValueError, match="two-dimensional"):
        resize_wafer_map(np.array([0, 1, 2]))
    with pytest.raises(ValueError, match="values 0, 1, and 2"):
        resize_wafer_map(np.array([[0, 4], [1, 2]]))


def test_cnn_forward_pass_and_probabilities() -> None:
    model = WaferCNN(3)
    logits = model(torch.zeros((2, 1, 32, 32)))
    probabilities = torch.softmax(logits, dim=1)
    assert logits.shape == (2, 3)
    assert torch.allclose(probabilities.sum(dim=1), torch.ones(2))


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0.59, "LOW"), (0.60, "MODERATE"), (0.80, "MODERATE"), (0.81, "HIGH")],
)
def test_confidence_bands(value: float, expected: str) -> None:
    assert confidence_level(value) == expected


def test_saved_model_reloads_and_predicts_valid_class(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    classes = ["CENTER", "DONUT", "EDGE_LOCAL"]
    model = WaferCNN(len(classes))
    torch.save(model.state_dict(), model_dir / "wafer_cnn.pt")
    (model_dir / "vision_model_metadata.json").write_text(
        json.dumps({"classes": classes}), encoding="utf-8"
    )
    result = WaferPredictor(model_dir).predict(_map(4))
    assert result["defect_class"] in classes
    assert 0 <= result["confidence"] <= 1
    assert abs(sum(item["probability"] for item in result["top_predictions"]) - 1) < 1e-6
