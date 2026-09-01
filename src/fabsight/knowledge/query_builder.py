"""Build concise technical queries from a structured ManufacturingCase."""

from __future__ import annotations

from fabsight.integration.case_schema import ManufacturingCase


def build_case_query(case: ManufacturingCase) -> str:
    """Select useful technical concepts without dumping case JSON or asserting cause."""
    step = case.fab_context.process_step.lower().replace("_", " ")
    defect = case.vision_evidence.defect_class.lower().replace("_", " ")
    risk_phrase = {
        "LOW": "stable process monitoring",
        "MODERATE": "process variation investigation",
        "HIGH": "abnormal process monitoring",
    }[case.process_evidence.risk_level]
    agreement = (
        "corroborating inspection evidence"
        if case.evidence_status == "CONSISTENT"
        else "conflicting evidence investigation"
    )
    return (
        f"semiconductor {step} {risk_phrase} {defect} wafer pattern "
        f"inspection {agreement} equipment maintenance alarms"
    )
