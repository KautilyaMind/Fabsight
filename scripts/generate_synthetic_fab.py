"""Command-line entry point for FabSight v0.1 data generation."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fabsight.config import SYNTHETIC_DATA_DIR  # noqa: E402
from fabsight.generators import generate_and_save  # noqa: E402
from fabsight.validation import validate_directory  # noqa: E402


def main() -> int:
    tables = generate_and_save()
    print("FabSight v0.1 synthetic fab generated successfully.\n")
    for label, key in (
        ("tools", "tools"), ("lots", "lots"), ("wafers", "wafers"),
        ("process events", "process_events"),
        ("maintenance records", "maintenance"), ("alarms", "alarms"),
    ):
        print(f"{len(tables[key]):>6} {label}")
    print(f"\nOutput:\n{SYNTHETIC_DATA_DIR.relative_to(PROJECT_ROOT)}/\n")
    return 0 if validate_directory(SYNTHETIC_DATA_DIR) else 1


if __name__ == "__main__":
    raise SystemExit(main())
