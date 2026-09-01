"""Validate structure, references, and time ordering in FabSight v0.1 data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from fabsight.config import DATASET_FILES, SYNTHETIC_DATA_DIR

ID_COLUMNS = {
    "tools": "tool_id",
    "lots": "lot_id",
    "wafers": "wafer_id",
    "process_steps": "step_id",
    "process_events": "event_id",
    "maintenance": "maintenance_id",
    "alarms": "alarm_id",
}
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def _check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_dataset(tables: dict[str, pd.DataFrame]) -> list[str]:
    """Return validation errors; an empty list means the dataset is valid."""
    errors: list[str] = []
    expected_tables = {Path(name).stem for name in DATASET_FILES}
    missing_tables = expected_tables - tables.keys()
    if missing_tables:
        return [f"Missing tables: {', '.join(sorted(missing_tables))}"]

    for table_name, id_column in ID_COLUMNS.items():
        table = tables[table_name]
        _check(not table.empty, f"{table_name} is empty", errors)
        _check(not table.isna().any().any(), f"{table_name} has missing values", errors)
        _check(table[id_column].is_unique, f"{table_name}.{id_column} is not unique", errors)

    tools = set(tables["tools"]["tool_id"])
    lots = set(tables["lots"]["lot_id"])
    wafers = set(tables["wafers"]["wafer_id"])
    steps = set(tables["process_steps"]["step_id"])
    events = tables["process_events"]

    _check(set(tables["wafers"]["lot_id"]) <= lots, "Wafer lot reference is invalid", errors)
    _check(set(events["wafer_id"]) <= wafers, "Event wafer reference is invalid", errors)
    _check(set(events["lot_id"]) <= lots, "Event lot reference is invalid", errors)
    _check(set(events["tool_id"]) <= tools, "Event tool reference is invalid", errors)
    _check(set(events["step_id"]) <= steps, "Event step reference is invalid", errors)
    _check(set(tables["maintenance"]["tool_id"]) <= tools, "Maintenance tool reference is invalid", errors)
    _check(set(tables["alarms"]["tool_id"]) <= tools, "Alarm tool reference is invalid", errors)

    wafer_lot = tables["wafers"].set_index("wafer_id")["lot_id"]
    matching_lots = events["wafer_id"].map(wafer_lot).eq(events["lot_id"])
    _check(bool(matching_lots.all()), "Event lot does not match its wafer's lot", errors)

    event_starts = pd.to_datetime(
        events["start_timestamp"], format=TIMESTAMP_FORMAT, errors="coerce"
    )
    event_ends = pd.to_datetime(
        events["end_timestamp"], format=TIMESTAMP_FORMAT, errors="coerce"
    )
    _check(not event_starts.isna().any() and not event_ends.isna().any(), "Event timestamps are invalid", errors)
    _check(bool((event_ends > event_starts).all()), "An event ends before or at its start", errors)
    actual_duration = (event_ends - event_starts).dt.total_seconds()
    _check(bool(actual_duration.eq(events["duration_seconds"]).all()), "Event duration is inconsistent", errors)

    maintenance_starts = pd.to_datetime(
        tables["maintenance"]["start_timestamp"], format=TIMESTAMP_FORMAT
    )
    maintenance_ends = pd.to_datetime(
        tables["maintenance"]["end_timestamp"], format=TIMESTAMP_FORMAT
    )
    _check(bool((maintenance_ends > maintenance_starts).all()), "Maintenance time range is invalid", errors)

    step_order = tables["process_steps"].set_index("step_id")["step_order"]
    ordered_events = events.assign(_step_order=events["step_id"].map(step_order)).sort_values(
        ["wafer_id", "start_timestamp"]
    )
    expected_order = list(tables["process_steps"].sort_values("step_order")["step_order"])
    for wafer_id, group in ordered_events.groupby("wafer_id", sort=False):
        _check(group["_step_order"].tolist() == expected_order, f"Process order is invalid for {wafer_id}", errors)
        starts = pd.to_datetime(
            group["start_timestamp"], format=TIMESTAMP_FORMAT
        ).reset_index(drop=True)
        ends = pd.to_datetime(
            group["end_timestamp"], format=TIMESTAMP_FORMAT
        ).reset_index(drop=True)
        if len(group) > 1:
            _check(bool((starts.iloc[1:].reset_index(drop=True) >= ends.iloc[:-1].reset_index(drop=True)).all()), f"Process events overlap for {wafer_id}", errors)
    return errors


def validate_directory(data_dir: Path = SYNTHETIC_DATA_DIR, *, print_summary: bool = True) -> bool:
    """Load CSV files, validate them, and optionally print a readable summary."""
    missing = [name for name in DATASET_FILES if not (data_dir / name).exists()]
    if missing:
        if print_summary:
            print("FabSight synthetic dataset validation\n")
            print(f"Missing files: {', '.join(missing)}")
            print("\nDataset invalid.")
        return False

    tables = {Path(name).stem: pd.read_csv(data_dir / name) for name in DATASET_FILES}
    errors = validate_dataset(tables)
    if print_summary:
        print("FabSight synthetic dataset validation\n")
        for label, key in (
            ("Tools", "tools"), ("Lots", "lots"), ("Wafers", "wafers"),
            ("Process steps", "process_steps"), ("Process events", "process_events"),
            ("Maintenance", "maintenance"), ("Alarms", "alarms"),
        ):
            table_errors = [error for error in errors if key.replace("_", " ") in error.lower()]
            print(f"{label + ':':22} {'FAIL' if table_errors else 'PASS'}")
        print(f"{'Referential integrity:':22} {'FAIL' if errors else 'PASS'}")
        if errors:
            print("\nValidation errors:")
            for error in errors:
                print(f"- {error}")
            print("\nDataset invalid.")
        else:
            print("\nDataset valid.")
    return not errors


if __name__ == "__main__":
    raise SystemExit(0 if validate_directory() else 1)
