"""Evaluate the saved wafer CNN against its final test split."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.vision.evaluate_classifier import evaluate_vision_model  # noqa: E402


def main() -> int:
    try:
        metrics = evaluate_vision_model()
    except (FileNotFoundError, ValueError) as exc:
        print(f"FabSight could not evaluate the vision model.\n\n{exc}", file=sys.stderr)
        return 1
    print("FabSight v0.4 - final wafer CNN test evaluation\n")
    print(f"Accuracy:        {metrics['accuracy']:.3f}")
    print(f"Macro precision: {metrics['macro_precision']:.3f}")
    print(f"Macro recall:    {metrics['macro_recall']:.3f}")
    print(f"Macro F1:        {metrics['macro_f1']:.3f}")
    print(f"Weighted F1:     {metrics['weighted_f1']:.3f}\n")
    print("Class          Precision  Recall  F1     Support")
    for name, values in metrics["per_class"].items():
        print(
            f"{name:14} {values['precision']:9.3f}  {values['recall']:6.3f}  "
            f"{values['f1']:5.3f}  {values['support']:7}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
