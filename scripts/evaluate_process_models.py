"""Evaluate persisted FabSight v0.3 models against the untouched test split."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.config import PROCESS_MODEL_DIR, PROCESS_REPORT_DIR, SECOM_PROCESSED_DIR  # noqa: E402
from fabsight.modeling.evaluate_process_model import evaluate_saved_models  # noqa: E402


def main() -> int:
    try:
        report = evaluate_saved_models(SECOM_PROCESSED_DIR, PROCESS_MODEL_DIR, PROCESS_REPORT_DIR)
    except (FileNotFoundError, ValueError) as exc:
        print(f"FabSight could not evaluate process models.\n\n{exc}", file=sys.stderr)
        return 1
    print("FabSight v0.3 - untouched test-set evaluation\n")
    print("Model                   Accuracy  FAIL precision  FAIL recall  FAIL F1  ROC-AUC")
    for name, result in report["models"].items():
        metrics = result["metrics"]
        print(
            f"{name:23} {metrics['accuracy']:8.3f}  {metrics['precision_fail']:14.3f}  "
            f"{metrics['recall_fail']:11.3f}  {metrics['f1_fail']:7.3f}  {metrics['roc_auc']:7.3f}"
        )
        matrix = metrics["confusion_matrix"]
        print(f"  confusion [[PASS->PASS, PASS->FAIL], [FAIL->PASS, FAIL->FAIL]]: {matrix}")
        print("  threshold  FAIL precision  FAIL recall")
        for row in result["threshold_analysis"]:
            print(f"    {row['threshold']:.2f}          {row['precision_fail']:.3f}        {row['recall_fail']:.3f}")
    print("\nLower thresholds tend to catch more FAIL cases but create more false alarms.")
    print("These are educational thresholds, not production control limits.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
