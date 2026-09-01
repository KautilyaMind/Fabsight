"""Leakage-safe preprocessing for train/test-ready SECOM files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from fabsight.config import RANDOM_SEED, SECOM_PROCESSED_DIR


def prepare_secom(
    data: pd.DataFrame,
    output_dir: Path = SECOM_PROCESSED_DIR,
    *,
    random_seed: int = RANDOM_SEED,
    test_size: float = 0.2,
    save_outputs: bool = True,
) -> dict[str, Any]:
    """Split first, learn preprocessing from training data, and optionally save it."""
    feature_columns = data.filter(regex=r"^feature_\d+$").columns.tolist()
    if not feature_columns:
        raise ValueError("No feature_NNN columns were found.")
    X = data[feature_columns]
    y = data["target"]
    train_indices, test_indices = train_test_split(
        data.index,
        test_size=test_size,
        random_state=random_seed,
        stratify=y,
    )
    X_train_raw = X.loc[train_indices]
    X_test_raw = X.loc[test_indices]
    y_train = y.loc[train_indices]
    y_test = y.loc[test_indices]

    all_missing = X_train_raw.columns[X_train_raw.isna().all()].tolist()
    constant = X_train_raw.columns[X_train_raw.nunique(dropna=True) <= 1].tolist()
    removed_columns = sorted(set(all_missing + constant))
    usable_columns = [column for column in feature_columns if column not in removed_columns]
    if not usable_columns:
        raise ValueError("No usable SECOM features remain after training-data checks.")

    # Both fit operations see training observations only; test values cannot affect them.
    pipeline = Pipeline(
        [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
    )
    train_values = pipeline.fit_transform(X_train_raw[usable_columns])
    test_values = pipeline.transform(X_test_raw[usable_columns])
    X_train = pd.DataFrame(train_values, columns=usable_columns, index=train_indices)
    X_test = pd.DataFrame(test_values, columns=usable_columns, index=test_indices)

    summary = {
        "original_sample_count": len(data),
        "original_feature_count": len(feature_columns),
        "all_missing_columns_removed": sorted(all_missing),
        "constant_columns_removed": sorted(set(constant) - set(all_missing)),
        "removed_columns": removed_columns,
        "removed_column_count": len(removed_columns),
        "remaining_feature_count": len(usable_columns),
        "train_size": len(train_indices),
        "test_size": len(test_indices),
        "class_distribution": y.value_counts().reindex(["PASS", "FAIL"], fill_value=0).to_dict(),
        "train_class_distribution": y_train.value_counts().reindex(["PASS", "FAIL"], fill_value=0).to_dict(),
        "test_class_distribution": y_test.value_counts().reindex(["PASS", "FAIL"], fill_value=0).to_dict(),
        "random_seed": random_seed,
        "test_fraction": test_size,
        "imputation": "median fitted on training data only",
        "scaling": "standard scaling fitted on imputed training data only",
        "target_encoding": {"original_-1": "PASS", "original_1": "FAIL"},
    }

    if save_outputs:
        output_dir.mkdir(parents=True, exist_ok=True)
        X_train.to_csv(output_dir / "X_train.csv", index=False)
        X_test.to_csv(output_dir / "X_test.csv", index=False)
        y_train.rename("target").to_csv(output_dir / "y_train.csv", index=False)
        y_test.rename("target").to_csv(output_dir / "y_test.csv", index=False)
        data.loc[train_indices, ["timestamp"]].to_csv(output_dir / "train_metadata.csv", index=False)
        data.loc[test_indices, ["timestamp"]].to_csv(output_dir / "test_metadata.csv", index=False)
        (output_dir / "preprocessing_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
        joblib.dump(pipeline, output_dir / "preprocessing_pipeline.joblib")
    return {
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train.reset_index(drop=True),
        "y_test": y_test.reset_index(drop=True),
        "pipeline": pipeline,
        "summary": summary,
    }
