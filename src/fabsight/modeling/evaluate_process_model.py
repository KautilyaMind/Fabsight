"""Metrics and plots for binary PASS/FAIL process-quality models."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import joblib
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "fabsight-matplotlib"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from fabsight.config import FAILURE_THRESHOLD, PROCESS_MODEL_DIR, PROCESS_REPORT_DIR

MODEL_FILES = {
    "logistic_regression": "logistic_regression.joblib",
    "random_forest": "random_forest.joblib",
}


def evaluate_predictions(
    y_true: pd.Series,
    fail_probabilities: Any,
    threshold: float = FAILURE_THRESHOLD,
) -> dict[str, Any]:
    """Calculate metrics with FAIL treated as the positive class."""
    predicted = pd.Series(
        ["FAIL" if probability >= threshold else "PASS" for probability in fail_probabilities]
    )
    truth = pd.Series(y_true).reset_index(drop=True)
    matrix = confusion_matrix(truth, predicted, labels=["PASS", "FAIL"])
    return {
        "threshold": threshold,
        "accuracy": float(accuracy_score(truth, predicted)),
        "precision_fail": float(precision_score(truth, predicted, pos_label="FAIL", zero_division=0)),
        "recall_fail": float(recall_score(truth, predicted, pos_label="FAIL", zero_division=0)),
        "f1_fail": float(f1_score(truth, predicted, pos_label="FAIL", zero_division=0)),
        "roc_auc": float(roc_auc_score((truth == "FAIL").astype(int), fail_probabilities)),
        "confusion_matrix": matrix.tolist(),
    }


def threshold_analysis(y_true: pd.Series, probabilities: Any) -> list[dict[str, float]]:
    """Show the educational precision/recall trade-off at fixed thresholds."""
    return [
        {
            "threshold": threshold,
            "precision_fail": evaluate_predictions(y_true, probabilities, threshold)["precision_fail"],
            "recall_fail": evaluate_predictions(y_true, probabilities, threshold)["recall_fail"],
        }
        for threshold in (0.30, 0.40, 0.50, 0.60, 0.70)
    ]


def _fail_probabilities(model: Any, X: pd.DataFrame) -> Any:
    fail_index = list(model.classes_).index("FAIL")
    return model.predict_proba(X)[:, fail_index]


def _save_confusion_plot(name: str, metrics: dict[str, Any], report_dir: Path) -> None:
    display = ConfusionMatrixDisplay(
        confusion_matrix=np.asarray(metrics["confusion_matrix"]),
        display_labels=["PASS", "FAIL"],
    )
    display.plot(cmap="Blues", colorbar=False)
    plt.title(f"{name.replace('_', ' ').title()} confusion matrix")
    plt.tight_layout()
    plt.savefig(report_dir / f"{name}_confusion_matrix.png", dpi=150)
    plt.close()


def _save_comparison_plot(results: dict[str, Any], report_dir: Path) -> None:
    comparison = pd.DataFrame(
        {
            name: {
                "FAIL precision": values["metrics"]["precision_fail"],
                "FAIL recall": values["metrics"]["recall_fail"],
                "FAIL F1": values["metrics"]["f1_fail"],
                "ROC-AUC": values["metrics"]["roc_auc"],
            }
            for name, values in results.items()
        }
    ).T
    comparison.plot(kind="bar", ylim=(0, 1), figsize=(8, 5))
    plt.ylabel("Score")
    plt.title("SECOM process-model comparison")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(report_dir / "model_comparison.png", dpi=150)
    plt.close()


def _save_roc_plot(models: dict[str, Any], X: pd.DataFrame, y: pd.Series, report_dir: Path) -> None:
    truth = (y == "FAIL").astype(int)
    for name, model in models.items():
        probabilities = _fail_probabilities(model, X)
        false_positive_rate, true_positive_rate, _ = roc_curve(truth, probabilities)
        auc = roc_auc_score(truth, probabilities)
        plt.plot(false_positive_rate, true_positive_rate, label=f"{name} ({auc:.3f})")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
    plt.xlabel("False-positive rate")
    plt.ylabel("True-positive rate")
    plt.title("SECOM process-model ROC curves")
    plt.legend()
    plt.tight_layout()
    plt.savefig(report_dir / "roc_curves.png", dpi=150)
    plt.close()


def evaluate_saved_models(
    processed_dir: Path,
    model_dir: Path = PROCESS_MODEL_DIR,
    report_dir: Path = PROCESS_REPORT_DIR,
) -> dict[str, Any]:
    """Evaluate persisted models once against the untouched v0.2 test set."""
    X_test = pd.read_csv(processed_dir / "X_test.csv")
    y_test = pd.read_csv(processed_dir / "y_test.csv")["target"]
    models = {name: joblib.load(model_dir / filename) for name, filename in MODEL_FILES.items()}
    results: dict[str, Any] = {}
    report_dir.mkdir(parents=True, exist_ok=True)
    for name, model in models.items():
        probabilities = _fail_probabilities(model, X_test)
        metrics = evaluate_predictions(y_test, probabilities)
        results[name] = {
            "metrics": metrics,
            "threshold_analysis": threshold_analysis(y_test, probabilities),
        }
        _save_confusion_plot(name, metrics, report_dir)
    _save_comparison_plot(results, report_dir)
    _save_roc_plot(models, X_test, y_test, report_dir)
    payload = {
        "models": results,
        "limitations": [
            "SECOM features are anonymized and their physical meanings are unknown.",
            "Predictions describe statistical patterns, not physical root causes.",
            "This educational demonstration is not suitable for production process control.",
            "No proprietary semiconductor manufacturing data is used.",
        ],
    }
    (report_dir / "model_comparison.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    rows = [dict(model=name, **values["metrics"]) for name, values in results.items()]
    pd.DataFrame(rows).drop(columns="confusion_matrix").to_csv(
        report_dir / "model_comparison.csv", index=False
    )
    return payload
