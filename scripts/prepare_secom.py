"""Download, load, and preprocess SECOM for FabSight v0.2."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.config import SECOM_PROCESSED_DIR, SECOM_RAW_DIR  # noqa: E402
from fabsight.data.download_secom import SecomDownloadError, download_secom  # noqa: E402
from fabsight.data.load_secom import load_secom  # noqa: E402
from fabsight.data.preprocess_secom import prepare_secom  # noqa: E402


def main() -> int:
    try:
        download_secom(SECOM_RAW_DIR)
        data = load_secom(SECOM_RAW_DIR)
        result = prepare_secom(data, SECOM_PROCESSED_DIR)
    except (SecomDownloadError, FileNotFoundError, ValueError) as exc:
        print(f"FabSight could not prepare SECOM.\n\n{exc}", file=sys.stderr)
        return 1
    summary = result["summary"]
    print("FabSight v0.2 - SECOM preparation complete\n")
    print(f"Samples: {summary['original_sample_count']}")
    print(f"Original features: {summary['original_feature_count']}")
    print(f"Columns removed: {summary['removed_column_count']}")
    print(f"Remaining features: {summary['remaining_feature_count']}")
    print(f"Train rows: {summary['train_size']}")
    print(f"Test rows: {summary['test_size']}")
    print(f"\nOutput: {SECOM_PROCESSED_DIR.relative_to(PROJECT_ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
