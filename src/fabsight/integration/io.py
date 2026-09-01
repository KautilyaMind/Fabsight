"""JSONL persistence and summary statistics for multimodal cases."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from fabsight.integration.case_schema import ManufacturingCase


def save_cases(cases: list[ManufacturingCase], output_dir: Path) -> None:
    """Save complete JSONL cases plus a compact inspection CSV."""
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "cases.jsonl").open("w", encoding="utf-8", newline="\n") as output:
        for case in cases:
            output.write(json.dumps(case.to_dict(), sort_keys=True) + "\n")
    rows = [
        {
            "case_id": case.case_id,
            "wafer_id": case.fab_context.wafer_id,
            "lot_id": case.fab_context.lot_id,
            "tool_id": case.fab_context.tool_id,
            "process_risk": case.process_evidence.risk_level,
            "defect_class": case.vision_evidence.defect_class,
            "evidence_status": case.evidence_status,
        }
        for case in cases
    ]
    pd.DataFrame(rows).to_csv(output_dir / "cases_summary.csv", index=False)


def load_cases(path: Path) -> list[ManufacturingCase]:
    """Load and type all JSONL case records."""
    if not path.is_file():
        raise FileNotFoundError(f"Case file not found: {path}")
    cases = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                cases.append(ManufacturingCase.from_dict(json.loads(line)))
            except (KeyError, TypeError, json.JSONDecodeError) as exc:
                raise ValueError(f"Invalid case JSON on line {line_number}: {exc}") from exc
    return cases


def summarize_cases(cases: list[ManufacturingCase]) -> dict[str, Any]:
    """Count actual integration outcomes without interpreting their causes."""
    return {
        "total_cases": len(cases),
        "evidence_status": dict(sorted(Counter(case.evidence_status for case in cases).items())),
        "process_risk": dict(sorted(Counter(case.process_evidence.risk_level for case in cases).items())),
        "vision_defects": dict(sorted(Counter(case.vision_evidence.defect_class for case in cases).items())),
        "pairing_strategy": cases[0].integration_metadata.pairing_strategy if cases else None,
        "synthetic_linkage_notice": (
            "The independent public process and wafer-map records are paired "
            "synthetically for an educational architecture demonstration."
        ),
    }


def save_summary(summary: dict[str, Any], report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "case_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    rows = []
    for category in ("evidence_status", "process_risk", "vision_defects"):
        rows.extend(
            {"category": category, "value": value, "count": count}
            for value, count in summary[category].items()
        )
    pd.DataFrame(rows).to_csv(report_dir / "case_summary.csv", index=False)
