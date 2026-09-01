"""Run one persisted FabSight v0.3 process-model prediction."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.config import SECOM_PROCESSED_DIR  # noqa: E402
from fabsight.modeling import ProcessPredictor  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict one prepared SECOM observation.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--row", type=int, help="Zero-based row in the prepared test CSV.")
    source.add_argument("--csv", type=Path, help="CSV containing exactly one processed row.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.row is not None:
            test_data = pd.read_csv(SECOM_PROCESSED_DIR / "X_test.csv")
            if args.row < 0 or args.row >= len(test_data):
                raise ValueError(f"Row must be between 0 and {len(test_data) - 1}.")
            sample = test_data.iloc[args.row]
            sample_label = str(args.row)
        else:
            sample = pd.read_csv(args.csv)
            sample_label = str(args.csv)
        result = ProcessPredictor().predict(sample)
    except (FileNotFoundError, TypeError, ValueError) as exc:
        print(f"FabSight prediction failed: {exc}", file=sys.stderr)
        return 1
    print("FabSight Process Intelligence\n")
    print(f"Sample: {sample_label}")
    print(f"Prediction: {result['prediction']}")
    print(f"Failure probability: {result['failure_probability']:.1%}")
    print(f"Risk: {result['risk_level']}\n")
    print("Top contributing anonymous variables:")
    for feature in result["top_features"]:
        print(f"  {feature}")
    print("\nImportant: feature meanings are unknown; model influence is not physical causality.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
