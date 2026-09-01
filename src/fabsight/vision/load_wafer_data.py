"""Download, load, normalize, and inspect public WM-811K wafer maps."""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

from fabsight.config import WAFER_RAW_DIR

DATASET_PAGE = "https://www.kaggle.com/datasets/qingyi/wm811k-wafer-map"
DOWNLOAD_URL = "https://www.kaggle.com/api/v1/datasets/download/qingyi/wm811k-wafer-map"
EXPECTED_FILENAMES = ("LSWMD.pkl", "WM811K.pkl")

LABEL_MAP = {
    "center": "CENTER",
    "donut": "DONUT",
    "edge-loc": "EDGE_LOCAL",
    "edge_loc": "EDGE_LOCAL",
    "edge-ring": "EDGE_RING",
    "edge_ring": "EDGE_RING",
    "loc": "LOCAL",
    "local": "LOCAL",
    "random": "RANDOM",
    "scratch": "SCRATCH",
    "near-full": "NEAR_FULL",
    "near_full": "NEAR_FULL",
    "none": "NONE",
}


class WaferDataError(RuntimeError):
    """Raised when the public wafer-map data cannot be obtained or interpreted."""


@dataclass(frozen=True)
class WaferDataset:
    """Usable labeled maps plus quality counts from the raw dataset."""

    maps: list[np.ndarray]
    labels: list[str]
    source_indices: list[int]
    total_samples: int
    unlabeled_samples: int
    invalid_label_samples: int
    malformed_samples: int


def manual_download_instructions(raw_dir: Path = WAFER_RAW_DIR) -> str:
    """Return exact manual setup instructions when public download is unavailable."""
    return (
        "Download the public WM-811K Wafer Map dataset from:\n"
        f"{DATASET_PAGE}\n"
        "Extract LSWMD.pkl (or WM811K.pkl) and place it in:\n"
        f"{raw_dir.resolve()}"
    )


def find_dataset_file(raw_dir: Path = WAFER_RAW_DIR) -> Path | None:
    """Find one supported cached pickle filename."""
    for filename in EXPECTED_FILENAMES:
        path = raw_dir / filename
        if path.is_file():
            return path
    return None


def download_wafer_data(
    raw_dir: Path = WAFER_RAW_DIR, *, force: bool = False, timeout: int = 120
) -> Path:
    """Cache the public archive; never silently substitute another dataset."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    existing = find_dataset_file(raw_dir)
    if existing and not force:
        return existing
    try:
        with requests.get(DOWNLOAD_URL, stream=True, timeout=timeout) as response:
            response.raise_for_status()
            with tempfile.TemporaryDirectory(prefix="fabsight-wm811k-") as temp_name:
                archive_path = Path(temp_name) / "wm811k.zip"
                with archive_path.open("wb") as destination:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            destination.write(chunk)
                with zipfile.ZipFile(archive_path) as archive:
                    candidates = [
                        member
                        for member in archive.infolist()
                        if not member.is_dir()
                        and Path(member.filename).name in EXPECTED_FILENAMES
                    ]
                    if not candidates:
                        raise WaferDataError("The public archive contained no supported pickle file.")
                    member = candidates[0]
                    target = raw_dir / Path(member.filename).name
                    with archive.open(member) as source, target.open("wb") as output:
                        shutil.copyfileobj(source, output)
                    return target
    except (requests.RequestException, OSError, zipfile.BadZipFile) as exc:
        raise WaferDataError(
            f"Automatic WM-811K download failed: {exc}\n\n"
            f"{manual_download_instructions(raw_dir)}"
        ) from exc


def _unwrap_label(value: Any) -> str | None:
    """Unwrap the nested arrays used by the common WM-811K pickle."""
    while isinstance(value, (list, tuple, np.ndarray, pd.Series)):
        array = np.asarray(value, dtype=object).reshape(-1)
        if array.size == 0:
            return None
        value = array[0]
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    text = str(value).strip().lower()
    return text or None


def normalize_label(value: Any) -> str | None:
    """Map an actual supported source label to a clean internal class name."""
    label = _unwrap_label(value)
    if label is None:
        return None
    return LABEL_MAP.get(label)


def load_wafer_dataset(path: Path) -> WaferDataset:
    """Load labeled usable maps and retain counts of excluded records."""
    if not path.is_file():
        raise FileNotFoundError(f"Wafer dataset file not found: {path}")
    frame = pd.read_pickle(path)
    required = {"waferMap", "failureType"}
    if not required <= set(frame.columns):
        raise WaferDataError(f"Dataset must contain columns: {sorted(required)}")
    maps: list[np.ndarray] = []
    labels: list[str] = []
    indices: list[int] = []
    unlabeled = 0
    invalid_labels = 0
    malformed = 0
    for index, row in frame.iterrows():
        raw_label = _unwrap_label(row["failureType"])
        if raw_label is None:
            unlabeled += 1
            continue
        label = LABEL_MAP.get(raw_label)
        if label is None:
            invalid_labels += 1
            continue
        wafer_map = np.asarray(row["waferMap"])
        if wafer_map.ndim != 2 or wafer_map.size == 0 or not np.isin(wafer_map, [0, 1, 2]).all():
            malformed += 1
            continue
        maps.append(wafer_map.astype(np.uint8, copy=False))
        labels.append(label)
        indices.append(int(index) if isinstance(index, (int, np.integer)) else len(indices))
    if not maps:
        raise WaferDataError("No labeled usable wafer maps were found.")
    return WaferDataset(
        maps, labels, indices, len(frame), unlabeled, invalid_labels, malformed
    )


def inspect_wafer_dataset(dataset: WaferDataset) -> dict[str, Any]:
    """Summarize label quality, class imbalance, and native dimensions."""
    counts = pd.Series(dataset.labels).value_counts().sort_index().to_dict()
    dimensions = pd.Series([f"{item.shape[0]}x{item.shape[1]}" for item in dataset.maps])
    return {
        "total_samples": dataset.total_samples,
        "labeled_usable_samples": len(dataset.maps),
        "unlabeled_samples": dataset.unlabeled_samples,
        "invalid_label_samples": dataset.invalid_label_samples,
        "malformed_samples": dataset.malformed_samples,
        "class_counts": counts,
        "classes": sorted(counts),
        "native_dimension_count": int(dimensions.nunique()),
        "most_common_dimensions": dimensions.value_counts().head(10).to_dict(),
        "imbalance_ratio_max_to_min": round(max(counts.values()) / min(counts.values()), 2),
    }
