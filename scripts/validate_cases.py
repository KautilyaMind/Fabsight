"""Validate saved v0.5 cases and all synthetic fab references."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.config import INTEGRATED_CASE_DIR  # noqa: E402
from fabsight.integration.io import load_cases  # noqa: E402
from fabsight.integration.runtime import load_fab_tables  # noqa: E402
from fabsight.integration.validation import validate_cases  # noqa: E402


def main() -> int:
    try:
        cases = load_cases(INTEGRATED_CASE_DIR / "cases.jsonl")
        errors = validate_cases(cases, load_fab_tables())
    except (FileNotFoundError, ValueError) as exc:
        print(f"FabSight case validation could not run.\n\n{exc}", file=sys.stderr)
        return 1
    print("FabSight v0.5 multimodal case validation\n")
    print(f"Cases: {len(cases)}")
    if errors:
        print("Status: FAIL\n")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Unique case IDs: PASS")
    print("Synthetic references: PASS")
    print("Evidence schemas: PASS")
    print("Probability ranges: PASS")
    print("Anonymous feature names: PASS")
    print("Provenance: PASS")
    print("Synthetic dataset linkage: PASS")
    print("\nDataset valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
