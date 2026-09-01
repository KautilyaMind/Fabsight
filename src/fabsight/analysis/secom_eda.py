"""Beginner-friendly exploratory checks for anonymized SECOM variables."""

from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_secom(data: pd.DataFrame) -> dict[str, Any]:
    """Calculate a compact quality report without assigning feature meanings."""
    features = data.filter(regex=r"^feature_\d+$")
    missing_by_feature = features.isna().mean().sort_values(ascending=False)
    non_missing = features.count()
    unique_counts = features.nunique(dropna=True)
    constant = unique_counts[unique_counts <= 1].index.tolist()
    near_constant = []
    for column in features.columns:
        if non_missing[column] and unique_counts[column] > 1:
            largest_share = features[column].value_counts(dropna=True).iloc[0] / non_missing[column]
            if largest_share >= 0.99:
                near_constant.append(column)
    duplicate_mask = features.T.duplicated()
    duplicate_columns = features.columns[duplicate_mask].tolist()
    class_counts = data["target"].value_counts().reindex(["PASS", "FAIL"], fill_value=0)
    return {
        "samples": len(data),
        "features": features.shape[1],
        "class_counts": class_counts.to_dict(),
        "class_percentages": (class_counts / len(data) * 100).round(2).to_dict(),
        "total_missing": int(features.isna().sum().sum()),
        "missing_percentage": round(float(features.isna().mean().mean() * 100), 4),
        "highest_missing_rates": {
            key: round(float(value * 100), 2)
            for key, value in missing_by_feature.head(10).items()
        },
        "entirely_missing_columns": missing_by_feature[missing_by_feature == 1].index.tolist(),
        "excessive_missing_columns": missing_by_feature[missing_by_feature >= 0.5].index.tolist(),
        "constant_columns": constant,
        "near_constant_columns": near_constant,
        "duplicate_columns": duplicate_columns,
        "minimum_value": float(features.min(skipna=True).min(skipna=True)),
        "maximum_value": float(features.max(skipna=True).max(skipna=True)),
    }


def print_secom_report(report: dict[str, Any]) -> None:
    """Print the EDA results in approachable language."""
    counts = report["class_counts"]
    percentages = report["class_percentages"]
    fail_share = percentages["FAIL"]
    imbalance = "Severe" if fail_share < 10 else "Moderate" if fail_share < 25 else "Limited"
    print("FabSight v0.2 - SECOM analysis\n")
    print(f"Samples: {report['samples']}")
    print(f"Raw process variables: {report['features']}\n")
    print(f"PASS: {counts['PASS']} ({percentages['PASS']:.2f}%)")
    print(f"FAIL: {counts['FAIL']} ({percentages['FAIL']:.2f}%)")
    print(f"Class imbalance: {imbalance}\n")
    print(
        f"Missing values: {report['total_missing']} "
        f"({report['missing_percentage']:.4f}%)"
    )
    print(f"Entirely missing columns: {len(report['entirely_missing_columns'])}")
    print(f"Constant columns: {len(report['constant_columns'])}")
    print(f"Near-constant columns: {len(report['near_constant_columns'])}")
    print(f"Duplicate columns: {len(report['duplicate_columns'])}")
    print(f"Columns with at least 50% missing: {len(report['excessive_missing_columns'])}")
    print(
        f"Observed numerical range: {report['minimum_value']} to "
        f"{report['maximum_value']}\n"
    )
    print("Features with the highest missing rates:")
    for column, percentage in report["highest_missing_rates"].items():
        print(f"  {column}: {percentage:.2f}%")
    print("\nImportant note:")
    print("SECOM features are anonymized.")
    print("Their physical sensor or measurement meanings are unknown.")
