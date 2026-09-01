"""Offline tests for v0.5 synthetic multimodal case integration."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fabsight.integration.case_builder import CaseBuilder  # noqa: E402
from fabsight.integration.io import load_cases, save_cases, summarize_cases  # noqa: E402
from fabsight.integration.pairing import evidence_status  # noqa: E402
from fabsight.integration.validation import validate_cases  # noqa: E402


def _fab_tables() -> dict[str, pd.DataFrame]:
    return {
        "tools": pd.DataFrame(
            [{"tool_id": "ETCH-01", "tool_type": "ETCH", "tool_name": "Demo", "installation_date": "2020-01-01", "status": "ACTIVE"}]
        ),
        "lots": pd.DataFrame(
            [{"lot_id": "LOT-0001", "product_family": "DEMO", "wafer_count": 1, "start_timestamp": "2025-01-01 08:00:00", "priority": "STANDARD", "status": "COMPLETED"}]
        ),
        "wafers": pd.DataFrame(
            [{"wafer_id": "WAF-000001", "lot_id": "LOT-0001", "wafer_number": 1, "created_timestamp": "2025-01-01 08:00:00", "current_status": "COMPLETED"}]
        ),
        "process_steps": pd.DataFrame(
            [{"step_id": "STEP-04", "step_order": 4, "step_name": "ETCH", "step_category": "ETCH", "description": "Educational abstraction"}]
        ),
        "process_events": pd.DataFrame(
            [{"event_id": "EVT-00000001", "wafer_id": "WAF-000001", "lot_id": "LOT-0001", "step_id": "STEP-04", "tool_id": "ETCH-01", "start_timestamp": "2025-01-02 08:00:00", "end_timestamp": "2025-01-02 08:10:00", "duration_seconds": 600, "event_status": "COMPLETED"}]
        ),
        "maintenance": pd.DataFrame(
            [{"maintenance_id": "MNT-00001", "tool_id": "ETCH-01", "maintenance_type": "PREVENTIVE", "start_timestamp": "2024-12-20 08:00:00", "end_timestamp": "2024-12-20 09:00:00", "description": "Generic maintenance"}]
        ),
        "alarms": pd.DataFrame(
            [{"alarm_id": "ALM-00001", "tool_id": "ETCH-01", "timestamp": "2024-12-30 08:00:00", "alarm_code": "GENERAL_TOOL_WARNING", "severity": "WARNING", "message": "Synthetic notification"}]
        ),
    }


def _process_candidates() -> list[dict]:
    return [
        {"sample_id": "SECOM-TEST-000001", "prediction": "PASS", "failure_probability": 0.1, "risk_level": "LOW", "top_features": ["feature_001"]},
        {"sample_id": "SECOM-TEST-000002", "prediction": "FAIL", "failure_probability": 0.8, "risk_level": "HIGH", "top_features": ["feature_002"]},
    ]


def _vision_candidates() -> list[dict]:
    return [
        {"sample_id": "WM811K-000001", "defect_class": "NONE", "confidence": 0.7, "confidence_level": "MODERATE", "top_predictions": [{"class": "NONE", "probability": 0.7}]},
        {"sample_id": "WM811K-000002", "defect_class": "EDGE_RING", "confidence": 0.9, "confidence_level": "HIGH", "top_predictions": [{"class": "EDGE_RING", "probability": 0.9}]},
    ]


def _builder(seed: int = 42, rate: float = 0.7) -> CaseBuilder:
    return CaseBuilder(
        _fab_tables(), _process_candidates(), _vision_candidates(),
        random_seed=seed, consistency_rate=rate,
    )


def test_case_creation_schema_references_and_provenance() -> None:
    case = _builder().create_case(1)
    assert case.case_id == "CASE-00001"
    assert case.fab_context.wafer_id == "WAF-000001"
    assert 0 <= case.process_evidence.failure_probability <= 1
    assert 0 <= case.vision_evidence.confidence <= 1
    assert case.provenance.dataset_linkage == "SYNTHETIC"
    assert case.process_evidence.data_source_type == "PUBLIC_DATASET"
    assert case.vision_evidence.prediction_source_type == "MODEL_OUTPUT"
    assert validate_cases([case], _fab_tables()) == []


def test_case_ids_unique_and_generation_deterministic() -> None:
    first = _builder().create_cases(30)
    second = _builder().create_cases(30)
    assert len({case.case_id for case in first}) == 30
    assert [case.to_dict() for case in first] == [case.to_dict() for case in second]


def test_consistent_and_mixed_calculation() -> None:
    assert evidence_status("LOW", "NONE") == "CONSISTENT"
    assert evidence_status("HIGH", "EDGE_RING") == "CONSISTENT"
    assert evidence_status("LOW", "SCRATCH") == "MIXED"
    assert evidence_status("MODERATE", "NONE") == "MIXED"
    cases = _builder(rate=0.7).create_cases(100)
    assert {case.evidence_status for case in cases} == {"CONSISTENT", "MIXED"}


def test_cases_save_reload_and_summarize(tmp_path: Path) -> None:
    cases = _builder().create_cases(10)
    save_cases(cases, tmp_path)
    loaded = load_cases(tmp_path / "cases.jsonl")
    assert [case.to_dict() for case in loaded] == [case.to_dict() for case in cases]
    assert summarize_cases(loaded)["total_cases"] == 10


def test_invalid_case_fails_validation() -> None:
    case = _builder().create_case(1)
    invalid_process = replace(case.process_evidence, failure_probability=1.5)
    invalid_provenance = replace(case.provenance, dataset_linkage="PUBLIC_DATASET")
    invalid = replace(case, process_evidence=invalid_process, provenance=invalid_provenance)
    errors = validate_cases([invalid], _fab_tables())
    assert any("outside [0, 1]" in error for error in errors)
    assert any("linkage must be SYNTHETIC" in error for error in errors)


def test_physical_feature_names_are_rejected() -> None:
    case = _builder().create_case(1)
    invalid_process = replace(case.process_evidence, top_anonymous_features=["temperature"])
    errors = validate_cases([replace(case, process_evidence=invalid_process)], _fab_tables())
    assert any("anonymous positional names" in error for error in errors)


def test_empty_required_pairing_pool_fails_clearly() -> None:
    with pytest.raises(ValueError, match="required evidence pool is empty"):
        CaseBuilder(
            _fab_tables(), [_process_candidates()[0]], [_vision_candidates()[0]],
            consistency_rate=0.0,
        ).create_case(1)
