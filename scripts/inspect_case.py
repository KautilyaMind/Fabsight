"""Print one saved multimodal case in beginner-friendly form."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.config import INTEGRATED_CASE_DIR  # noqa: E402
from fabsight.integration.io import load_cases  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect one FabSight multimodal case.")
    parser.add_argument("--case", required=True, dest="case_id")
    args = parser.parse_args()
    try:
        cases = load_cases(INTEGRATED_CASE_DIR / "cases.jsonl")
        case = next((item for item in cases if item.case_id == args.case_id), None)
        if case is None:
            raise ValueError(f"Case not found: {args.case_id}")
    except (FileNotFoundError, ValueError) as exc:
        print(f"FabSight could not inspect the case.\n\n{exc}", file=sys.stderr)
        return 1
    print("FabSight Multimodal Case\n")
    print(f"Case: {case.case_id}\n")
    print("Synthetic Fab Context")
    print("---------------------")
    print(f"Wafer: {case.fab_context.wafer_id}")
    print(f"Lot: {case.fab_context.lot_id}")
    print(f"Tool: {case.fab_context.tool_id}")
    print(f"Step: {case.fab_context.process_step}\n")
    print("Process Evidence")
    print("----------------")
    print(f"Prediction: {case.process_evidence.prediction}")
    print(f"Failure probability: {case.process_evidence.failure_probability:.1%}")
    print(f"Risk: {case.process_evidence.risk_level}\n")
    print("Vision Evidence")
    print("---------------")
    print(f"Defect: {case.vision_evidence.defect_class}")
    print(f"Confidence: {case.vision_evidence.confidence:.1%}")
    print(f"Confidence level: {case.vision_evidence.confidence_level}\n")
    print("Equipment Context")
    print("-----------------")
    print(f"Tool status: {case.equipment_context.tool_status}")
    print(f"Recent alarms: {case.equipment_context.recent_alarm_count}")
    age = case.equipment_context.maintenance_days_ago
    print(f"Maintenance age: {age if age is not None else 'not available'} days\n")
    print(f"Evidence status: {case.evidence_status}")
    print("Dataset linkage: SYNTHETIC\n")
    print("Important:")
    print("The process and wafer-map records originate from independent public datasets.")
    print("Their linkage inside this case is synthetic and does not establish causality.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
