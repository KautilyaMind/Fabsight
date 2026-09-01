"""Train a small class-weighted CNN on prepared wafer maps."""

from __future__ import annotations

import json
import random
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sklearn.metrics import f1_score
from torch import nn
from torch.utils.data import DataLoader, Dataset

from fabsight.config import (
    RANDOM_SEED,
    VISION_MODEL_DIR,
    WAFER_IMAGE_SIZE,
    WAFER_PROCESSED_DIR,
)


def set_reproducible_seeds(seed: int = RANDOM_SEED) -> None:
    """Seed Python, NumPy, and PyTorch and request deterministic CPU behavior."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)


class WaferArrayDataset(Dataset):
    """Convert stored uint8 die-state arrays to normalized CNN tensors."""

    def __init__(self, path: Path) -> None:
        if not path.is_file():
            raise FileNotFoundError(f"Prepared wafer split not found: {path}")
        with np.load(path) as data:
            self.images = data["images"].copy()
            self.labels = data["labels"].copy()

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        image = torch.from_numpy(self.images[index].astype(np.float32) / 2.0).unsqueeze(0)
        label = torch.tensor(self.labels[index], dtype=torch.long)
        return image, label


class WaferCNN(nn.Module):
    """A deliberately small two-block CNN for 32x32 single-channel wafer maps."""

    def __init__(self, number_of_classes: int) -> None:
        super().__init__()
        if number_of_classes < 2:
            raise ValueError("WaferCNN requires at least two classes.")
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.AdaptiveAvgPool2d((4, 4)),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(), nn.Linear(32 * 4 * 4, 64), nn.ReLU(), nn.Linear(64, number_of_classes)
        )

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(images))


def _epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer | None,
) -> tuple[float, float, float]:
    training = optimizer is not None
    model.train(training)
    losses: list[float] = []
    predictions: list[int] = []
    targets: list[int] = []
    for images, labels in loader:
        if training:
            optimizer.zero_grad()
        with torch.set_grad_enabled(training):
            logits = model(images)
            loss = criterion(logits, labels)
            if training:
                loss.backward()
                optimizer.step()
        losses.append(float(loss.detach()))
        predictions.extend(logits.argmax(dim=1).detach().tolist())
        targets.extend(labels.tolist())
    accuracy = float(np.mean(np.asarray(predictions) == np.asarray(targets)))
    macro_f1 = float(f1_score(targets, predictions, average="macro", zero_division=0))
    return float(np.mean(losses)), accuracy, macro_f1


def train_vision_model(
    processed_dir: Path = WAFER_PROCESSED_DIR,
    model_dir: Path = VISION_MODEL_DIR,
    *,
    epochs: int = 8,
    batch_size: int = 128,
    learning_rate: float = 0.001,
    random_seed: int = RANDOM_SEED,
) -> dict[str, Any]:
    """Train with class-weighted loss and select epochs by validation macro F1."""
    if epochs < 1:
        raise ValueError("Epochs must be at least one.")
    set_reproducible_seeds(random_seed)
    summary = json.loads(
        (processed_dir / "wafer_preprocessing_summary.json").read_text(encoding="utf-8")
    )
    classes = summary["classes"]
    train_data = WaferArrayDataset(processed_dir / "train.npz")
    validation_data = WaferArrayDataset(processed_dir / "validation.npz")
    generator = torch.Generator().manual_seed(random_seed)
    train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True, generator=generator)
    validation_loader = DataLoader(validation_data, batch_size=batch_size, shuffle=False)
    counts = np.bincount(train_data.labels, minlength=len(classes))
    weights = len(train_data) / (len(classes) * counts)
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32))
    model = WaferCNN(len(classes))
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    history = []
    best_f1 = -1.0
    best_state = None
    for epoch in range(1, epochs + 1):
        train_loss, train_accuracy, _ = _epoch(model, train_loader, criterion, optimizer)
        validation_loss, validation_accuracy, validation_f1 = _epoch(
            model, validation_loader, criterion, None
        )
        history.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                "validation_loss": validation_loss,
                "train_accuracy": train_accuracy,
                "validation_accuracy": validation_accuracy,
                "validation_macro_f1": validation_f1,
            }
        )
        if validation_f1 > best_f1:
            best_f1 = validation_f1
            best_state = deepcopy(model.state_dict())
    assert best_state is not None
    model.load_state_dict(best_state)
    model_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), model_dir / "wafer_cnn.pt")
    metadata = {
        "dataset": "public WM-811K wafer-map dataset",
        "training_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "classes": classes,
        "image_dimensions": [WAFER_IMAGE_SIZE, WAFER_IMAGE_SIZE],
        "random_seed": random_seed,
        "architecture": "Conv2d(1,16)-ReLU-Pool-Conv2d(16,32)-ReLU-Pool-AdaptivePool-Dense(64)-Softmax",
        "class_weighting": {name: float(weights[index]) for index, name in enumerate(classes)},
        "epochs_requested": epochs,
        "best_validation_macro_f1": best_f1,
        "training_history": history,
        "test_metrics": None,
        "limitations": [
            "Defect classes describe spatial patterns, not physical root causes.",
            "The public dataset may not represent every production environment.",
            "This educational model is not suitable for production quality-control decisions.",
            "No proprietary semiconductor manufacturing data is used.",
        ],
    }
    (model_dir / "vision_model_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata
