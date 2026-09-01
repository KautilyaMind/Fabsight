"""Resize labeled wafer maps and create reproducible stratified splits."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from sklearn.model_selection import train_test_split

from fabsight.config import RANDOM_SEED, WAFER_IMAGE_SIZE, WAFER_PROCESSED_DIR
from fabsight.vision.load_wafer_data import WaferDataset, inspect_wafer_dataset


def resize_wafer_map(wafer_map: np.ndarray, image_size: int = WAFER_IMAGE_SIZE) -> np.ndarray:
    """Resize discrete die states with nearest-neighbor interpolation."""
    array = np.asarray(wafer_map)
    if array.ndim != 2 or array.size == 0:
        raise ValueError("A wafer map must be a non-empty two-dimensional array.")
    if not np.isin(array, [0, 1, 2]).all():
        raise ValueError("Wafer maps may contain only die-state values 0, 1, and 2.")
    image = Image.fromarray(array.astype(np.uint8), mode="L")
    resized = image.resize((image_size, image_size), resample=Image.Resampling.NEAREST)
    return np.asarray(resized, dtype=np.uint8)


def _cap_classes(
    dataset: WaferDataset, max_per_class: int | None, random_seed: int
) -> tuple[list[np.ndarray], list[str], list[int]]:
    rng = np.random.default_rng(random_seed)
    labels_array = np.asarray(dataset.labels)
    selected: list[int] = []
    for label in sorted(set(dataset.labels)):
        candidates = np.flatnonzero(labels_array == label)
        if max_per_class is not None and len(candidates) > max_per_class:
            candidates = rng.choice(candidates, size=max_per_class, replace=False)
        selected.extend(candidates.tolist())
    selected = sorted(selected)
    return (
        [dataset.maps[index] for index in selected],
        [dataset.labels[index] for index in selected],
        [dataset.source_indices[index] for index in selected],
    )


def prepare_wafer_data(
    dataset: WaferDataset,
    output_dir: Path = WAFER_PROCESSED_DIR,
    *,
    image_size: int = WAFER_IMAGE_SIZE,
    max_per_class: int | None = 2000,
    random_seed: int = RANDOM_SEED,
    save_outputs: bool = True,
) -> dict[str, Any]:
    """Resize maps and make 70/15/15 stratified train/validation/test splits."""
    maps, labels, source_indices = _cap_classes(dataset, max_per_class, random_seed)
    class_names = sorted(set(labels))
    if any(labels.count(name) < 3 for name in class_names):
        raise ValueError("Each class needs at least three samples for stratified splitting.")
    encoded = np.asarray([class_names.index(label) for label in labels], dtype=np.int64)
    images = np.stack([resize_wafer_map(item, image_size) for item in maps])
    source = np.asarray(source_indices, dtype=np.int64)
    indices = np.arange(len(images))
    train_indices, remainder_indices = train_test_split(
        indices, test_size=0.30, random_state=random_seed, stratify=encoded
    )
    validation_indices, test_indices = train_test_split(
        remainder_indices,
        test_size=0.50,
        random_state=random_seed,
        stratify=encoded[remainder_indices],
    )
    split_indices = {
        "train": train_indices,
        "validation": validation_indices,
        "test": test_indices,
    }
    summary = inspect_wafer_dataset(dataset)
    summary.update(
        {
            "selected_labeled_samples": len(images),
            "image_size": [image_size, image_size],
            "classes": class_names,
            "class_to_index": {name: index for index, name in enumerate(class_names)},
            "selected_class_counts": {
                name: int((encoded == index).sum()) for index, name in enumerate(class_names)
            },
            "train_size": len(train_indices),
            "validation_size": len(validation_indices),
            "test_size": len(test_indices),
            "random_seed": random_seed,
            "max_per_class": max_per_class,
            "normalization": "die-state values divided by 2.0 during tensor loading",
            "resize": "nearest-neighbor to preserve discrete die states",
            "augmentation": "none; spatial geometry is preserved",
        }
    )
    if save_outputs:
        output_dir.mkdir(parents=True, exist_ok=True)
        for split_name, split in split_indices.items():
            np.savez_compressed(
                output_dir / f"{split_name}.npz",
                images=images[split],
                labels=encoded[split],
                source_indices=source[split],
            )
        (output_dir / "wafer_preprocessing_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
    return {"images": images, "labels": encoded, "splits": split_indices, "summary": summary}
