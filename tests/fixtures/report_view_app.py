"""Fixture app for report presentation tests."""
from app.report_view import render_report

render_report({
    "approval_status": "APPROVED",
    "generated_at": "2026-10-08T12:00:00Z",
    "report": {
        "title": "FabSight Investigation Report",
        "investigation_id": "INV-000001",
        "case_id": "CASE-00001",
        "approval_status": "APPROVED",
        "confidence": "MODERATE",
        "case_summary": {"process_step": "LITHOGRAPHY", "evidence_status": "MIXED"},
        "process_findings": {"prediction": "FAIL", "failure_probability": 0.72, "risk_level": "HIGH"},
        "vision_findings": {"defect_class": "EDGE_RING", "confidence": 0.81, "confidence_level": "HIGH"},
        "simulated_rca_result": {"predicted_cause": "THERMAL_DRIFT", "confidence": 0.64, "severity": "MEDIUM"},
        "equipment_context": {"tool_id": "LITHO-01", "tool_status": "ACTIVE", "recent_alarm_count": 1},
        "investigation_hypotheses": [{"statement": "Review thermal drift.", "status": "HYPOTHESIS", "confidence": "MODERATE"}],
        "additional_data_needed": ["Named process telemetry"],
        "limitations": ["No physical root cause is confirmed."],
        "provenance": {"process_data": "PUBLIC_DATASET"},
    },
})
