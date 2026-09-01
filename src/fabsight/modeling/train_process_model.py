"""Train two class-weighted SECOM process-quality baselines."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from fabsight.config import (
    FAILURE_THRESHOLD,
    PROCESS_MODEL_DIR,
    PROCESS_REPORT_DIR,
    RANDOM_SEED,
    SECOM_PROCESSED_DIR,
)
from fabsight.explainability import save_feature_reports
from fabsight.modeling.evaluate_process_model import evaluate_predictions


def build_models(random_seed: int = RANDOM_SEED, rf_estimators: int = 200) -> dict[str, Any]:
    """Create the two intentionally simple, class-weighted baseline models."""
    return {
        "logistic_regression": LogisticRegression(
            class_weight="balanced", max_iter=2000, random_state=random_seed
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=rf_estimators,
            class_weight="balanced",
            min_samples_leaf=2,
            random_state=random_seed,
            # One worker avoids platform-level floating aggregation differences.
            n_jobs=1,
        ),
    }


def _probabilities(model: Any, X: pd.DataFrame) -> Any:
    return model.predict_proba(X)[:, list(model.classes_).index("FAIL")]


def select_model(validation_metrics: dict[str, dict[str, Any]]) -> str:
    """Prefer FAIL recall, then FAIL F1 and ROC-AUC; never rank by accuracy alone."""
    return max(
        validation_metrics,
        key=lambda name: (
            validation_metrics[name]["recall_fail"],
            validation_metrics[name]["f1_fail"],
            validation_metrics[name]["roc_auc"],
        ),
    )


def train_process_models(
    processed_dir: Path = SECOM_PROCESSED_DIR,
    model_dir: Path = PROCESS_MODEL_DIR,
    report_dir: Path = PROCESS_REPORT_DIR,
    *,
    random_seed: int = RANDOM_SEED,
    rf_estimators: int = 200,
) -> dict[str, Any]:
    """Select on a training-only validation split, refit, and persist both models."""
    X_train = pd.read_csv(processed_dir / "X_train.csv")
    y_train = pd.read_csv(processed_dir / "y_train.csv")["target"]
    development_indices, validation_indices = train_test_split(
        X_train.index,
        test_size=0.2,
        random_state=random_seed,
        stratify=y_train,
    )
    model_templates = build_models(random_seed, rf_estimators)
    validation_metrics: dict[str, dict[str, Any]] = {}
    for name, template in model_templates.items():
        candidate = clone(template).fit(
            X_train.loc[development_indices], y_train.loc[development_indices]
        )
        validation_metrics[name] = evaluate_predictions(
            y_train.loc[validation_indices], _probabilities(candidate, X_train.loc[validation_indices])
        )

    selected_name = select_model(validation_metrics)
    model_dir.mkdir(parents=True, exist_ok=True)
    fitted_models = {}
    for name, template in model_templates.items():
        model = clone(template).fit(X_train, y_train)
        fitted_models[name] = model
        joblib.dump(model, model_dir / f"{name}.joblib")
    joblib.dump(fitted_models[selected_name], model_dir / "selected_model.joblib")

    importance = save_feature_reports(fitted_models, X_train.columns.tolist(), report_dir)
    metadata = {
        "dataset_version": "UCI SECOM prepared by FabSight v0.2",
        "training_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "random_seed": random_seed,
        "feature_count": X_train.shape[1],
        "feature_names": X_train.columns.tolist(),
        "training_rows": len(X_train),
        "model_types": {
            "logistic_regression": "class-weighted LogisticRegression",
            "random_forest": "class-weighted RandomForestClassifier",
        },
        "validation_metrics": validation_metrics,
        "selected_model": selected_name,
        "selection_rule": "highest validation FAIL recall, then FAIL F1, then ROC-AUC",
        "classification_threshold": FAILURE_THRESHOLD,
        "preprocessing_artifact_reference": "data/processed/secom/preprocessing_pipeline.joblib",
        "top_anonymous_features": importance,
        "limitations": [
            "SECOM feature meanings are unknown.",
            "Model associations do not establish physical causality.",
            "This is an educational demonstration, not production process control.",
        ],
    }
    (model_dir / "model_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata
