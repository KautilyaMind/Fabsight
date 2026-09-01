"""Print exploratory information about the raw UCI SECOM data."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.analysis import analyze_secom, print_secom_report  # noqa: E402
from fabsight.config import SECOM_RAW_DIR  # noqa: E402
from fabsight.data.download_secom import SecomDownloadError, download_secom  # noqa: E402
from fabsight.data.load_secom import load_secom  # noqa: E402


def main() -> int:
    try:
        download_secom(SECOM_RAW_DIR)
        print_secom_report(analyze_secom(load_secom(SECOM_RAW_DIR)))
    except (SecomDownloadError, FileNotFoundError, ValueError) as exc:
        print(f"FabSight could not analyze SECOM.\n\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
