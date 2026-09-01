"""Build reproducible v0.5 synthetic multimodal manufacturing cases."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.config import (  # noqa: E402
    DEFAULT_CASE_COUNT,
    INTEGRATED_CASE_DIR,
    MULTIMODAL_REPORT_DIR,
)
from fabsight.integration.case_builder import CaseBuilder  # noqa: E402
from fabsight.integration.evidence import collect_process_candidates, collect_vision_candidates  # noqa: E402
from fabsight.integration.io import save_cases, save_summary, summarize_cases  # noqa: E402
from fabsight.integration.runtime import load_fab_tables  # noqa: E402
from fabsight.integration.validation import validate_cases  # noqa: E402
from fabsight.modeling import ProcessPredictor  # noqa: E402
from fabsight.vision import WaferPredictor  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build synthetic multimodal demo cases.")
    parser.add_argument("--count", type=int, default=DEFAULT_CASE_COUNT)
    args = parser.parse_args()
    try:
        fab_tables = load_fab_tables()
        process_candidates = collect_process_candidates(ProcessPredictor())
        vision_candidates = collect_vision_candidates(WaferPredictor())
        cases = CaseBuilder(fab_tables, process_candidates, vision_candidates).create_cases(args.count)
        errors = validate_cases(cases, fab_tables)
        if errors:
            raise ValueError("Generated cases failed validation:\n" + "\n".join(errors[:20]))
        save_cases(cases, INTEGRATED_CASE_DIR)
        summary = summarize_cases(cases)
        save_summary(summary, MULTIMODAL_REPORT_DIR)
    except (FileNotFoundError, TypeError, ValueError) as exc:
        print(f"FabSight could not build multimodal cases.\n\n{exc}", file=sys.stderr)
        return 1
    print("FabSight v0.5 - multimodal cases generated\n")
    print(f"Total cases: {summary['total_cases']}")
    print("\nEvidence status:")
    for name, count in summary["evidence_status"].items():
        print(f"  {name:12} {count}")
    print("\nProcess risk:")
    for name, count in summary["process_risk"].items():
        print(f"  {name:12} {count}")
    print("\nVision defects:")
    for name, count in summary["vision_defects"].items():
        print(f"  {name:12} {count}")
    print("\nDataset linkage: SYNTHETIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
