"""Global feature importance without unsupported physical interpretation."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "fabsight-matplotlib"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def feature_importance(model: Any, feature_names: list[str]) -> pd.DataFrame:
    """Return signed coefficients or nonnegative tree importance by feature."""
    if hasattr(model, "feature_importances_"):
        values = np.asarray(model.feature_importances_)
        kind = "random_forest_importance"
    elif hasattr(model, "coef_"):
        values = np.asarray(model.coef_)[0]
        kind = "logistic_coefficient"
    else:
        raise TypeError("Model does not expose supported feature importance.")
    if len(values) != len(feature_names):
        raise ValueError("Feature names do not align with model importance values.")
    frame = pd.DataFrame({"feature": feature_names, "value": values, "kind": kind})
    frame["absolute_value"] = frame["value"].abs()
    return frame.sort_values("absolute_value", ascending=False).reset_index(drop=True)


def save_feature_reports(
    models: dict[str, Any], feature_names: list[str], report_dir: Path, top_n: int = 15
) -> dict[str, list[dict[str, Any]]]:
    """Save machine-readable importance and a Random Forest top-feature plot."""
    report_dir.mkdir(parents=True, exist_ok=True)
    reports: dict[str, list[dict[str, Any]]] = {}
    for name, model in models.items():
        importance = feature_importance(model, feature_names)
        importance.to_csv(report_dir / f"{name}_feature_importance.csv", index=False)
        reports[name] = importance.head(top_n).to_dict(orient="records")
        if hasattr(model, "feature_importances_"):
            top = importance.head(top_n).sort_values("value")
            plt.figure(figsize=(8, 6))
            plt.barh(top["feature"], top["value"])
            plt.xlabel("Model importance")
            plt.title("Top anonymous Random Forest variables")
            plt.tight_layout()
            plt.savefig(report_dir / "random_forest_feature_importance.png", dpi=150)
            plt.close()
    return reports
