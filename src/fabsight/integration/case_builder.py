"""Build reproducible cases from synthetic fab and independent public evidence."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from fabsight.config import (
    CASE_CONSISTENCY_RATE,
    CASE_PAIRING_STRATEGY,
    CASE_PAIRING_VERSION,
    RANDOM_SEED,
)
from fabsight.integration.case_schema import (
    EquipmentContext,
    FabContext,
    IntegrationMetadata,
    ManufacturingCase,
    ProcessEvidence,
    VisionEvidence,
)
from fabsight.integration.pairing import evidence_status, pair_evidence
from fabsight.integration.provenance import CaseProvenance


class CaseBuilder:
    """Join evidence into synthetic demo cases while preserving provenance."""

    def __init__(
        self,
        fab_tables: dict[str, pd.DataFrame],
        process_candidates: list[dict[str, Any]],
        vision_candidates: list[dict[str, Any]],
        *,
        random_seed: int = RANDOM_SEED,
        consistency_rate: float = CASE_CONSISTENCY_RATE,
    ) -> None:
        self.tables = fab_tables
        self.process_candidates = process_candidates
        self.vision_candidates = vision_candidates
        self.random_seed = random_seed
        self.consistency_rate = consistency_rate
        self.rng = np.random.default_rng(random_seed)
        events = fab_tables["process_events"]
        if events.empty:
            raise ValueError("Synthetic process events are required.")
        self.step_names = fab_tables["process_steps"].set_index("step_id")["step_name"]
        self.tool_status = fab_tables["tools"].set_index("tool_id")["status"]
        self.alarms = fab_tables["alarms"].copy()
        self.alarms["_timestamp"] = pd.to_datetime(self.alarms["timestamp"]).astype("datetime64[ns]")
        self.maintenance = fab_tables["maintenance"].copy()
        self.maintenance["_end"] = pd.to_datetime(
            self.maintenance["end_timestamp"]
        ).astype("datetime64[ns]")
        # A source-derived timestamp keeps repeated generation reproducible.
        self.generation_timestamp = pd.to_datetime(events["end_timestamp"]).max().isoformat()

    def _equipment_context(self, tool_id: str, event_time: pd.Timestamp) -> EquipmentContext:
        recent_alarm_rows = self.alarms[
            (self.alarms["tool_id"] == tool_id)
            & (self.alarms["_timestamp"] <= event_time)
            & (self.alarms["_timestamp"] >= event_time - np.timedelta64(30, "D"))
        ].sort_values("_timestamp", ascending=False)
        recent_maintenance_rows = self.maintenance[
            (self.maintenance["tool_id"] == tool_id)
            & (self.maintenance["_end"] <= event_time)
        ].sort_values("_end", ascending=False).head(3)
        days_ago = None
        if not recent_maintenance_rows.empty:
            days_ago = int((event_time - recent_maintenance_rows.iloc[0]["_end"]).days)
        alarm_fields = ["alarm_id", "timestamp", "alarm_code", "severity", "message"]
        maintenance_fields = [
            "maintenance_id", "maintenance_type", "start_timestamp", "end_timestamp", "description"
        ]
        return EquipmentContext(
            tool_id=tool_id,
            tool_status=str(self.tool_status.loc[tool_id]),
            recent_alarm_count=len(recent_alarm_rows),
            recent_alarms=recent_alarm_rows[alarm_fields].head(10).to_dict(orient="records"),
            maintenance_days_ago=days_ago,
            recent_maintenance=recent_maintenance_rows[maintenance_fields].to_dict(orient="records"),
        )

    def create_case(self, sequence: int) -> ManufacturingCase:
        """Create one case with synthetic context and independently sourced evidence."""
        process, vision, intended = pair_evidence(
            self.rng,
            self.process_candidates,
            self.vision_candidates,
            self.consistency_rate,
        )
        events = self.tables["process_events"]
        event = events.iloc[int(self.rng.integers(0, len(events)))]
        event_time = pd.Timestamp(event["end_timestamp"]).as_unit("ns")
        status = evidence_status(process["risk_level"], vision["defect_class"])
        return ManufacturingCase(
            case_id=f"CASE-{sequence:05d}",
            created_at=self.generation_timestamp,
            fab_context=FabContext(
                wafer_id=event["wafer_id"],
                lot_id=event["lot_id"],
                tool_id=event["tool_id"],
                process_step=str(self.step_names.loc[event["step_id"]]),
                process_event_id=event["event_id"],
                timestamp=event["end_timestamp"],
            ),
            process_evidence=ProcessEvidence(
                secom_sample_id=process["sample_id"],
                prediction=process["prediction"],
                failure_probability=process["failure_probability"],
                risk_level=process["risk_level"],
                top_anonymous_features=process["top_features"],
            ),
            vision_evidence=VisionEvidence(
                wafer_dataset_sample_id=vision["sample_id"],
                defect_class=vision["defect_class"],
                confidence=vision["confidence"],
                confidence_level=vision["confidence_level"],
                top_predictions=vision["top_predictions"],
            ),
            equipment_context=self._equipment_context(event["tool_id"], event_time),
            evidence_status=status,
            provenance=CaseProvenance(),
            integration_metadata=IntegrationMetadata(
                pairing_strategy=CASE_PAIRING_STRATEGY,
                pairing_version=CASE_PAIRING_VERSION,
                random_seed=self.random_seed,
                case_generation_timestamp=self.generation_timestamp,
                intended_pairing=intended,
            ),
        )

    def create_cases(self, count: int) -> list[ManufacturingCase]:
        if count < 1:
            raise ValueError("Case count must be at least one.")
        return [self.create_case(sequence) for sequence in range(1, count + 1)]
