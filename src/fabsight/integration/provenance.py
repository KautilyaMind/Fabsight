"""Mandatory origin labels for independent evidence streams."""

from __future__ import annotations

from dataclasses import asdict, dataclass

VALID_SOURCE_TYPES = {"PUBLIC_DATASET", "SYNTHETIC", "MODEL_OUTPUT", "DERIVED"}


@dataclass(frozen=True)
class CaseProvenance:
    """Record the origin of each case section and its synthetic linkage."""

    fab_context: str = "SYNTHETIC"
    equipment_context: str = "SYNTHETIC"
    process_data: str = "PUBLIC_DATASET"
    process_prediction: str = "MODEL_OUTPUT"
    vision_data: str = "PUBLIC_DATASET"
    vision_prediction: str = "MODEL_OUTPUT"
    evidence_status: str = "DERIVED"
    dataset_linkage: str = "SYNTHETIC"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
