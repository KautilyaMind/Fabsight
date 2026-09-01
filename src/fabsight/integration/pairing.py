"""Configurable synthetic pairing for independent process and vision evidence."""

from __future__ import annotations

from typing import Any

import numpy as np


def evidence_status(process_risk: str, defect_class: str) -> str:
    """Describe agreement without asserting causality or physical correlation."""
    process_abnormal = process_risk in {"MODERATE", "HIGH"}
    vision_abnormal = defect_class != "NONE"
    return "CONSISTENT" if process_abnormal == vision_abnormal else "MIXED"


def _choose(rng: np.random.Generator, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    if not candidates:
        raise ValueError("The requested evidence candidate pool is empty.")
    return candidates[int(rng.integers(0, len(candidates)))]


def pair_evidence(
    rng: np.random.Generator,
    process_candidates: list[dict[str, Any]],
    vision_candidates: list[dict[str, Any]],
    consistency_rate: float,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Choose a coherent or conflicting demonstration pair without causal claims."""
    if not 0 <= consistency_rate <= 1:
        raise ValueError("Consistency rate must be between 0 and 1.")
    low_process = [item for item in process_candidates if item["risk_level"] == "LOW"]
    elevated_process = [item for item in process_candidates if item["risk_level"] != "LOW"]
    no_pattern = [item for item in vision_candidates if item["defect_class"] == "NONE"]
    defect_pattern = [item for item in vision_candidates if item["defect_class"] != "NONE"]
    intended = "CONSISTENT" if rng.random() < consistency_rate else "MIXED"
    normal_pair = rng.random() < 0.5
    if intended == "CONSISTENT":
        process_pool, vision_pool = (
            (low_process, no_pattern) if normal_pair else (elevated_process, defect_pattern)
        )
    else:
        process_pool, vision_pool = (
            (low_process, defect_pattern) if normal_pair else (elevated_process, no_pattern)
        )
    # A clear failure is preferable to silently fabricating a different strategy.
    if not process_pool or not vision_pool:
        raise ValueError(
            f"Cannot create {intended} cases because a required evidence pool is empty."
        )
    process = _choose(rng, process_pool)
    vision = _choose(rng, vision_pool)
    return process, vision, intended
