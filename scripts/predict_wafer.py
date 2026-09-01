"""Predict the spatial defect class of one wafer-map file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.vision.wafer_predictor import WaferPredictor, load_wafer_input  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify one wafer map.")
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = WaferPredictor().predict(load_wafer_input(args.input))
    except (FileNotFoundError, TypeError, ValueError) as exc:
        print(f"FabSight wafer prediction failed: {exc}", file=sys.stderr)
        return 1
    print("FabSight Wafer Vision\n")
    print(f"Prediction: {result['defect_class']}")
    print(f"Confidence: {result['confidence']:.1%}")
    print(f"Confidence level: {result['confidence_level']}\n")
    print("Top predictions:")
    for item in result["top_predictions"]:
        print(f"  {item['class']:12} {item['probability']:.1%}")
    print("\nThe class describes a spatial pattern, not a proven physical root cause.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
