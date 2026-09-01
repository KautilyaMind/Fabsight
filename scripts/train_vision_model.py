"""Train the small FabSight v0.4 wafer-map CNN."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.vision.train_classifier import train_vision_model  # noqa: E402


def main() -> int:
    try:
        metadata = train_vision_model()
    except (FileNotFoundError, ValueError) as exc:
        print(f"FabSight could not train the vision model.\n\n{exc}", file=sys.stderr)
        return 1
    print("FabSight v0.4 - wafer CNN training complete\n")
    print("Epoch  Train loss  Validation loss  Train accuracy  Validation accuracy  Validation macro F1")
    for row in metadata["training_history"]:
        print(
            f"{row['epoch']:5}  {row['train_loss']:10.4f}  {row['validation_loss']:15.4f}  "
            f"{row['train_accuracy']:14.3f}  {row['validation_accuracy']:19.3f}  "
            f"{row['validation_macro_f1']:19.3f}"
        )
    print(f"\nBest validation macro F1: {metadata['best_validation_macro_f1']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
