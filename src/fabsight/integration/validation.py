"""Validate multimodal cases, references, probabilities, and provenance."""

from __future__ import annotations

import re

import pandas as pd

from fabsight.integration.case_schema import ManufacturingCase
from fabsight.integration.pairing import evidence_status
from fabsight.integration.provenance import VALID_SOURCE_TYPES


def validate_cases(
    cases: list[ManufacturingCase], fab_tables: dict[str, pd.DataFrame]
) -> list[str]:
    """Return clear validation errors; an empty list means all cases are valid."""
    errors: list[str] = []
    case_ids = [case.case_id for case in cases]
    if len(case_ids) != len(set(case_ids)):
        errors.append("Case IDs are not unique.")
    wafers = set(fab_tables["wafers"]["wafer_id"])
    lots = set(fab_tables["lots"]["lot_id"])
    tools = set(fab_tables["tools"]["tool_id"])
    events = fab_tables["process_events"].set_index("event_id")
    for case in cases:
        prefix = case.case_id
        context = case.fab_context
        if context.wafer_id not in wafers:
            errors.append(f"{prefix}: unknown synthetic wafer.")
        if context.lot_id not in lots:
            errors.append(f"{prefix}: unknown synthetic lot.")
        if context.tool_id not in tools:
            errors.append(f"{prefix}: unknown synthetic tool.")
        if context.process_event_id not in events.index:
            errors.append(f"{prefix}: unknown synthetic process event.")
        else:
            event = events.loc[context.process_event_id]
            if (
                event["wafer_id"] != context.wafer_id
                or event["lot_id"] != context.lot_id
                or event["tool_id"] != context.tool_id
            ):
                errors.append(f"{prefix}: fab context does not match its process event.")
        process = case.process_evidence
        if process.prediction not in {"PASS", "FAIL"}:
            errors.append(f"{prefix}: invalid process prediction.")
        if process.risk_level not in {"LOW", "MODERATE", "HIGH"}:
            errors.append(f"{prefix}: invalid process risk.")
        if not 0 <= process.failure_probability <= 1:
            errors.append(f"{prefix}: process probability is outside [0, 1].")
        if not process.top_anonymous_features or not all(
            re.fullmatch(r"feature_\d{3}", feature)
            for feature in process.top_anonymous_features
        ):
            errors.append(f"{prefix}: process feature names are not anonymous positional names.")
        vision = case.vision_evidence
        if not vision.defect_class:
            errors.append(f"{prefix}: vision defect class is missing.")
        if not 0 <= vision.confidence <= 1:
            errors.append(f"{prefix}: vision confidence is outside [0, 1].")
        if vision.confidence_level not in {"LOW", "MODERATE", "HIGH"}:
            errors.append(f"{prefix}: invalid vision confidence level.")
        if not vision.top_predictions or any(
            not 0 <= float(item.get("probability", -1)) <= 1
            or not item.get("class")
            for item in vision.top_predictions
        ):
            errors.append(f"{prefix}: invalid ranked vision predictions.")
        provenance = case.provenance.to_dict()
        if set(provenance.values()) - VALID_SOURCE_TYPES:
            errors.append(f"{prefix}: invalid provenance source type.")
        if provenance.get("dataset_linkage") != "SYNTHETIC":
            errors.append(f"{prefix}: dataset linkage must be SYNTHETIC.")
        expected_status = evidence_status(process.risk_level, vision.defect_class)
        if case.evidence_status != expected_status:
            errors.append(f"{prefix}: evidence status is inconsistent with its fields.")
        if case.equipment_context.tool_id != context.tool_id:
            errors.append(f"{prefix}: equipment tool does not match fab context.")
    return errors
