"""Download, inspect, and prepare labeled WM-811K wafer maps."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.config import WAFER_PROCESSED_DIR, WAFER_RAW_DIR  # noqa: E402
from fabsight.vision.load_wafer_data import (  # noqa: E402
    WaferDataError,
    download_wafer_data,
    inspect_wafer_dataset,
    load_wafer_dataset,
)
from fabsight.vision.preprocess_wafer_maps import prepare_wafer_data  # noqa: E402


def main() -> int:
    try:
        path = download_wafer_data(WAFER_RAW_DIR)
        dataset = load_wafer_dataset(path)
        inspection = inspect_wafer_dataset(dataset)
        result = prepare_wafer_data(dataset, WAFER_PROCESSED_DIR)
    except (FileNotFoundError, ValueError, WaferDataError) as exc:
        print(f"FabSight could not prepare wafer-map data.\n\n{exc}", file=sys.stderr)
        return 1
    summary = result["summary"]
    print("FabSight v0.4 - wafer-map preparation complete\n")
    print(f"Raw samples: {inspection['total_samples']}")
    print(f"Labeled usable samples: {inspection['labeled_usable_samples']}")
    print(f"Unlabeled samples: {inspection['unlabeled_samples']}")
    print(f"Unsupported-label samples: {inspection['invalid_label_samples']}")
    print(f"Malformed samples: {inspection['malformed_samples']}")
    print(f"Native dimension variants: {inspection['native_dimension_count']}\n")
    print("Actual labeled class distribution:")
    for name, count in inspection["class_counts"].items():
        print(f"  {name:12} {count}")
    print("\nSelected educational subset distribution:")
    for name, count in summary["selected_class_counts"].items():
        print(f"  {name:12} {count}")
    print(
        f"\nTrain/validation/test: {summary['train_size']}/"
        f"{summary['validation_size']}/{summary['test_size']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
