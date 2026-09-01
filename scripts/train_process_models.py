"""Train and persist FabSight v0.3 SECOM process models."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.modeling.train_process_model import train_process_models  # noqa: E402


def main() -> int:
    try:
        metadata = train_process_models()
    except (FileNotFoundError, ValueError) as exc:
        print(f"FabSight could not train process models.\n\n{exc}", file=sys.stderr)
        return 1
    print("FabSight v0.3 - process-model training complete\n")
    for name, metrics in metadata["validation_metrics"].items():
        print(
            f"{name:22} FAIL recall={metrics['recall_fail']:.3f}  "
            f"FAIL F1={metrics['f1_fail']:.3f}  ROC-AUC={metrics['roc_auc']:.3f}"
        )
    print(f"\nSelected from training-only validation: {metadata['selected_model']}")
    print("Selection prioritizes FAIL recall, then FAIL F1 and ROC-AUC.")
    print("Run the evaluation script once for untouched test-set results.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
