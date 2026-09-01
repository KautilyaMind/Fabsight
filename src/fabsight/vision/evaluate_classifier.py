"""Final multiclass evaluation for the persisted wafer-map CNN."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "fabsight-matplotlib"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from torch.utils.data import DataLoader

from fabsight.config import VISION_MODEL_DIR, VISION_REPORT_DIR, WAFER_PROCESSED_DIR
from fabsight.vision.train_classifier import WaferArrayDataset, WaferCNN


def evaluate_vision_model(
    processed_dir: Path = WAFER_PROCESSED_DIR,
    model_dir: Path = VISION_MODEL_DIR,
    report_dir: Path = VISION_REPORT_DIR,
    *,
    batch_size: int = 256,
) -> dict[str, Any]:
    """Evaluate the saved best-validation model once on the final test split."""
    metadata_path = model_dir / "vision_model_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    classes = metadata["classes"]
    model = WaferCNN(len(classes))
    model.load_state_dict(torch.load(model_dir / "wafer_cnn.pt", map_location="cpu", weights_only=True))
    model.eval()
    test_data = WaferArrayDataset(processed_dir / "test.npz")
    loader = DataLoader(test_data, batch_size=batch_size, shuffle=False)
    predictions: list[int] = []
    targets: list[int] = []
    with torch.no_grad():
        for images, labels in loader:
            predictions.extend(model(images).argmax(dim=1).tolist())
            targets.extend(labels.tolist())
    precision, recall, f1, support = precision_recall_fscore_support(
        targets, predictions, labels=list(range(len(classes))), zero_division=0
    )
    _, _, macro_f1, _ = precision_recall_fscore_support(
        targets, predictions, average="macro", zero_division=0
    )
    _, _, weighted_f1, _ = precision_recall_fscore_support(
        targets, predictions, average="weighted", zero_division=0
    )
    matrix = confusion_matrix(targets, predictions, labels=list(range(len(classes))))
    metrics = {
        "accuracy": float(accuracy_score(targets, predictions)),
        "macro_precision": float(np.mean(precision)),
        "macro_recall": float(np.mean(recall)),
        "macro_f1": float(macro_f1),
        "weighted_f1": float(weighted_f1),
        "per_class": {
            name: {
                "precision": float(precision[index]),
                "recall": float(recall[index]),
                "f1": float(f1[index]),
                "support": int(support[index]),
            }
            for index, name in enumerate(classes)
        },
        "confusion_matrix": matrix.tolist(),
    }
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "vision_evaluation.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    figure, axis = plt.subplots(figsize=(10, 9))
    ConfusionMatrixDisplay(matrix, display_labels=classes).plot(
        ax=axis, cmap="Blues", colorbar=False, xticks_rotation=45
    )
    axis.set_title("Wafer CNN confusion matrix")
    figure.tight_layout()
    figure.savefig(report_dir / "vision_confusion_matrix.png", dpi=150)
    plt.close(figure)
    history = metadata["training_history"]
    epochs = [row["epoch"] for row in history]
    figure, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(epochs, [row["train_loss"] for row in history], label="train")
    axes[0].plot(epochs, [row["validation_loss"] for row in history], label="validation")
    axes[0].set_title("Loss")
    axes[0].legend()
    axes[1].plot(epochs, [row["train_accuracy"] for row in history], label="train")
    axes[1].plot(epochs, [row["validation_accuracy"] for row in history], label="validation")
    axes[1].set_title("Accuracy")
    axes[1].legend()
    figure.tight_layout()
    figure.savefig(report_dir / "vision_training_history.png", dpi=150)
    plt.close(figure)
    metadata["test_metrics"] = metrics
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metrics
