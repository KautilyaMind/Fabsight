"""Dependency-free structured schema for a synthetic multimodal case."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from fabsight.integration.provenance import CaseProvenance


@dataclass(frozen=True)
class FabContext:
    wafer_id: str
    lot_id: str
    tool_id: str
    process_step: str
    process_event_id: str
    timestamp: str
    source_type: str = "SYNTHETIC"


@dataclass(frozen=True)
class ProcessEvidence:
    secom_sample_id: str
    prediction: str
    failure_probability: float
    risk_level: str
    top_anonymous_features: list[str]
    data_source_type: str = "PUBLIC_DATASET"
    prediction_source_type: str = "MODEL_OUTPUT"
    dataset: str = "SECOM"


@dataclass(frozen=True)
class VisionEvidence:
    wafer_dataset_sample_id: str
    defect_class: str
    confidence: float
    confidence_level: str
    top_predictions: list[dict[str, Any]]
    data_source_type: str = "PUBLIC_DATASET"
    prediction_source_type: str = "MODEL_OUTPUT"
    dataset: str = "WM811K"


@dataclass(frozen=True)
class EquipmentContext:
    tool_id: str
    tool_status: str
    recent_alarm_count: int
    recent_alarms: list[dict[str, Any]]
    maintenance_days_ago: int | None
    recent_maintenance: list[dict[str, Any]]
    source_type: str = "SYNTHETIC"


@dataclass(frozen=True)
class IntegrationMetadata:
    pairing_strategy: str
    pairing_version: str
    random_seed: int
    case_generation_timestamp: str
    intended_pairing: str
    linkage_notice: str = (
        "Independent public evidence records are linked synthetically for an "
        "educational software-architecture demonstration."
    )
    source_type: str = "DERIVED"


@dataclass(frozen=True)
class TelemetryEvidence:
    run_id: str
    source_type: str = "SYNTHETIC_TELEMETRY"
    readings_file: str | None = None
    rca_prediction: dict[str, Any] | None = None
    trend_summary: dict[str, Any] | None = None
    simulation_notice: str = "Synthetic educational telemetry; not a real production-process diagnosis."


@dataclass(frozen=True)
class ManufacturingCase:
    case_id: str
    created_at: str
    fab_context: FabContext
    process_evidence: ProcessEvidence
    vision_evidence: VisionEvidence
    equipment_context: EquipmentContext
    evidence_status: str
    provenance: CaseProvenance
    integration_metadata: IntegrationMetadata
    telemetry_evidence: TelemetryEvidence | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ManufacturingCase":
        """Rebuild a strongly typed case loaded from JSON."""
        return cls(
            case_id=value["case_id"],
            created_at=value["created_at"],
            fab_context=FabContext(**value["fab_context"]),
            process_evidence=ProcessEvidence(**value["process_evidence"]),
            vision_evidence=VisionEvidence(**value["vision_evidence"]),
            equipment_context=EquipmentContext(**value["equipment_context"]),
            evidence_status=value["evidence_status"],
            provenance=CaseProvenance(**value["provenance"]),
            integration_metadata=IntegrationMetadata(**value["integration_metadata"]),
            telemetry_evidence=TelemetryEvidence(**value["telemetry_evidence"]) if value.get("telemetry_evidence") else None,
        )
