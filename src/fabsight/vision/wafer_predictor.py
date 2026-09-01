"""Reusable structured inference for wafer-map spatial-pattern classification."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image

from fabsight.config import (
    VISION_HIGH_CONFIDENCE_MIN,
    VISION_LOW_CONFIDENCE_MAX,
    VISION_MODEL_DIR,
    WAFER_IMAGE_SIZE,
)
from fabsight.vision.preprocess_wafer_maps import resize_wafer_map
from fabsight.vision.train_classifier import WaferCNN


def confidence_level(
    confidence: float,
    low_max: float = VISION_LOW_CONFIDENCE_MAX,
    high_min: float = VISION_HIGH_CONFIDENCE_MIN,
) -> str:
    """Interpret confidence using configurable demonstration-only bands."""
    if not 0 <= confidence <= 1:
        raise ValueError("Confidence must be between 0 and 1.")
    if not 0 <= low_max <= high_min <= 1:
        raise ValueError("Confidence thresholds must satisfy 0 <= low <= high <= 1.")
    if confidence < low_max:
        return "LOW"
    if confidence > high_min:
        return "HIGH"
    return "MODERATE"


def load_wafer_input(path: Path) -> np.ndarray:
    """Load one numeric `.npy` wafer map or grayscale image file."""
    if not path.is_file():
        raise FileNotFoundError(f"Wafer input not found: {path}")
    if path.suffix.lower() == ".npy":
        array = np.load(path, allow_pickle=False)
    elif path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}:
        image = Image.open(path).convert("L")
        pixels = np.asarray(image)
        # Ordinary display images are quantized into the three expected die states.
        array = np.digitize(pixels, bins=[85, 170]).astype(np.uint8)
    else:
        raise ValueError("Input must be a .npy wafer map or supported grayscale image.")
    return np.asarray(array)


class WaferPredictor:
    """Load the persisted CNN and return class probabilities for one wafer map."""

    def __init__(self, model_dir: Path = VISION_MODEL_DIR) -> None:
        metadata_path = model_dir / "vision_model_metadata.json"
        weights_path = model_dir / "wafer_cnn.pt"
        if not metadata_path.is_file() or not weights_path.is_file():
            raise FileNotFoundError("Vision model artifacts are missing. Run training first.")
        self.metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.classes: list[str] = self.metadata["classes"]
        self.model = WaferCNN(len(self.classes))
        self.model.load_state_dict(torch.load(weights_path, map_location="cpu", weights_only=True))
        self.model.eval()

    def predict(self, wafer_map: np.ndarray, top_n: int = 3) -> dict[str, Any]:
        """Return predicted spatial class, confidence, band, and ranked classes."""
        resized = resize_wafer_map(wafer_map, WAFER_IMAGE_SIZE)
        tensor = torch.from_numpy(resized.astype(np.float32) / 2.0).unsqueeze(0).unsqueeze(0)
        with torch.no_grad():
            probabilities = torch.softmax(self.model(tensor), dim=1)[0].numpy()
        order = np.argsort(probabilities)[::-1][: min(top_n, len(self.classes))]
        confidence = float(probabilities[order[0]])
        return {
            "defect_class": self.classes[order[0]],
            "confidence": confidence,
            "confidence_level": confidence_level(confidence),
            "top_predictions": [
                {"class": self.classes[index], "probability": float(probabilities[index])}
                for index in order
            ],
        }
