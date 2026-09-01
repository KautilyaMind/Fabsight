"""Generate the deterministic FabSight v0.1 synthetic fab dataset.

All entities are fictional educational simulation data. They do not represent
Micron equipment, products, recipes, alarms, or operating procedures.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from fabsight.config import NUMBER_OF_LOTS, RANDOM_SEED, SYNTHETIC_DATA_DIR

BASE_TIME = datetime(2025, 1, 1, 8, 0, 0)
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

TOOL_SPECS = (
    ("CLEAN-01", "CLEAN", "AquaClean Alpha"),
    ("CLEAN-02", "CLEAN", "AquaClean Beta"),
    ("DEP-01", "DEPOSITION", "FilmForge One"),
    ("DEP-02", "DEPOSITION", "FilmForge Two"),
    ("LITHO-01", "LITHO", "PatternStar One"),
    ("LITHO-02", "LITHO", "PatternStar Two"),
    ("ETCH-01", "ETCH", "EtchCraft One"),
    ("ETCH-02", "ETCH", "EtchCraft Two"),
    ("IMPLANT-01", "IMPLANT", "IonPath One"),
    ("CMP-01", "CMP", "PlanarPro One"),
    ("CMP-02", "CMP", "PlanarPro Two"),
    ("INSP-01", "INSPECTION", "ViewCheck One"),
)

STEP_SPECS = (
    ("STEP-01", 1, "CLEAN", "CLEAN"),
    ("STEP-02", 2, "DEPOSITION", "DEPOSITION"),
    ("STEP-03", 3, "LITHOGRAPHY", "LITHO"),
    ("STEP-04", 4, "ETCH", "ETCH"),
    ("STEP-05", 5, "IMPLANT", "IMPLANT"),
    ("STEP-06", 6, "CMP", "CMP"),
    ("STEP-07", 7, "INSPECTION", "INSPECTION"),
)


def _format_timestamp(value: datetime) -> str:
    return value.strftime(TIMESTAMP_FORMAT)


def _generate_tools(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for tool_id, tool_type, tool_name in TOOL_SPECS:
        installed = datetime(2019, 1, 1) + timedelta(days=int(rng.integers(0, 1825)))
        rows.append(
            {
                "tool_id": tool_id,
                "tool_type": tool_type,
                "tool_name": tool_name,
                "installation_date": installed.date().isoformat(),
                "status": rng.choice(["ACTIVE", "MAINTENANCE"], p=[0.92, 0.08]),
            }
        )
    return pd.DataFrame(rows)


def _generate_lots(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for number in range(1, NUMBER_OF_LOTS + 1):
        start = BASE_TIME + timedelta(hours=int(rng.integers(0, 24 * 30)))
        rows.append(
            {
                "lot_id": f"LOT-{number:04d}",
                "product_family": rng.choice(
                    ["DEMO_MEMORY_A", "DEMO_MEMORY_B", "DEMO_MEMORY_C"]
                ),
                "wafer_count": int(rng.integers(10, 26)),
                "start_timestamp": _format_timestamp(start),
                "priority": rng.choice(["STANDARD", "EXPEDITE"], p=[0.9, 0.1]),
                "status": rng.choice(
                    ["IN_PROCESS", "COMPLETED", "ON_HOLD"], p=[0.2, 0.75, 0.05]
                ),
            }
        )
    return pd.DataFrame(rows)


def _generate_wafers(lots: pd.DataFrame) -> pd.DataFrame:
    rows = []
    wafer_sequence = 1
    for lot in lots.itertuples(index=False):
        lot_start = datetime.strptime(lot.start_timestamp, TIMESTAMP_FORMAT)
        for wafer_number in range(1, lot.wafer_count + 1):
            rows.append(
                {
                    "wafer_id": f"WAF-{wafer_sequence:06d}",
                    "lot_id": lot.lot_id,
                    "wafer_number": wafer_number,
                    "created_timestamp": _format_timestamp(
                        lot_start + timedelta(minutes=wafer_number - 1)
                    ),
                    "current_status": lot.status,
                }
            )
            wafer_sequence += 1
    return pd.DataFrame(rows)


def _generate_process_steps() -> pd.DataFrame:
    description_template = (
        "Simplified educational abstraction of the {name} stage; no production "
        "recipe or proprietary procedure is represented."
    )
    return pd.DataFrame(
        [
            {
                "step_id": step_id,
                "step_order": order,
                "step_name": name,
                "step_category": category,
                "description": description_template.format(name=name.lower()),
            }
            for step_id, order, name, category in STEP_SPECS
        ]
    )


def _generate_process_events(
    rng: np.random.Generator, wafers: pd.DataFrame
) -> pd.DataFrame:
    tools_by_type: dict[str, list[str]] = {}
    for tool_id, tool_type, _ in TOOL_SPECS:
        tools_by_type.setdefault(tool_type, []).append(tool_id)

    rows = []
    event_sequence = 1
    for wafer in wafers.itertuples(index=False):
        current_time = datetime.strptime(wafer.created_timestamp, TIMESTAMP_FORMAT)
        current_time += timedelta(minutes=int(rng.integers(5, 31)))
        for step_id, _, _, category in STEP_SPECS:
            # Durations and statuses are independent random workflow values in v0.1.
            duration = int(rng.integers(300, 3601))
            end_time = current_time + timedelta(seconds=duration)
            rows.append(
                {
                    "event_id": f"EVT-{event_sequence:08d}",
                    "wafer_id": wafer.wafer_id,
                    "lot_id": wafer.lot_id,
                    "step_id": step_id,
                    "tool_id": rng.choice(tools_by_type[category]),
                    "start_timestamp": _format_timestamp(current_time),
                    "end_timestamp": _format_timestamp(end_time),
                    "duration_seconds": duration,
                    "event_status": rng.choice(
                        ["COMPLETED", "WARNING", "FAILED"], p=[0.94, 0.04, 0.02]
                    ),
                }
            )
            event_sequence += 1
            current_time = end_time + timedelta(minutes=int(rng.integers(5, 61)))
    return pd.DataFrame(rows)


def _generate_maintenance(rng: np.random.Generator) -> pd.DataFrame:
    descriptions = {
        "PREVENTIVE": "Routine preventive maintenance",
        "CORRECTIVE": "General corrective maintenance",
        "CALIBRATION": "Sensor calibration check",
        "INSPECTION": "General equipment inspection",
    }
    rows = []
    sequence = 1
    for tool_id, _, _ in TOOL_SPECS:
        for _ in range(int(rng.integers(1, 4))):
            maintenance_type = rng.choice(list(descriptions))
            start = BASE_TIME + timedelta(hours=int(rng.integers(0, 24 * 60)))
            end = start + timedelta(minutes=int(rng.integers(30, 241)))
            rows.append(
                {
                    "maintenance_id": f"MNT-{sequence:05d}",
                    "tool_id": tool_id,
                    "maintenance_type": maintenance_type,
                    "start_timestamp": _format_timestamp(start),
                    "end_timestamp": _format_timestamp(end),
                    "description": descriptions[maintenance_type],
                }
            )
            sequence += 1
    return pd.DataFrame(rows).sort_values("start_timestamp").reset_index(drop=True)


def _generate_alarms(rng: np.random.Generator) -> pd.DataFrame:
    alarm_messages = {
        "TEMP_MONITOR_WARNING": "Synthetic temperature monitor notification",
        "PRESSURE_MONITOR_WARNING": "Synthetic pressure monitor notification",
        "PROCESS_TIMEOUT": "Synthetic process timeout notification",
        "GENERAL_TOOL_WARNING": "Synthetic general tool notification",
    }
    rows = []
    for sequence in range(1, 31):
        code = rng.choice(list(alarm_messages))
        timestamp = BASE_TIME + timedelta(minutes=int(rng.integers(0, 60 * 24 * 60)))
        rows.append(
            {
                "alarm_id": f"ALM-{sequence:05d}",
                "tool_id": TOOL_SPECS[int(rng.integers(0, len(TOOL_SPECS)))][0],
                "timestamp": _format_timestamp(timestamp),
                "alarm_code": code,
                "severity": rng.choice(["INFO", "WARNING", "CRITICAL"], p=[0.5, 0.4, 0.1]),
                "message": alarm_messages[code],
            }
        )
    return pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)


def generate_dataset(seed: int = RANDOM_SEED) -> dict[str, pd.DataFrame]:
    """Build all v0.1 tables in memory using one deterministic random stream."""
    rng = np.random.default_rng(seed)
    tools = _generate_tools(rng)
    lots = _generate_lots(rng)
    wafers = _generate_wafers(lots)
    return {
        "tools": tools,
        "lots": lots,
        "wafers": wafers,
        "process_steps": _generate_process_steps(),
        "process_events": _generate_process_events(rng, wafers),
        "maintenance": _generate_maintenance(rng),
        "alarms": _generate_alarms(rng),
    }


def generate_and_save(
    output_dir: Path = SYNTHETIC_DATA_DIR, seed: int = RANDOM_SEED
) -> dict[str, pd.DataFrame]:
    """Generate all tables and save them as CSV files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tables = generate_dataset(seed)
    for table_name, table in tables.items():
        table.to_csv(output_dir / f"{table_name}.csv", index=False, lineterminator="\n")
    return tables
