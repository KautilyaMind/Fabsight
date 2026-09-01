"""Focused tests for the FabSight v0.1 synthetic dataset."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fabsight.config import DATASET_FILES, RANDOM_SEED  # noqa: E402
from fabsight.generators import generate_and_save  # noqa: E402
from fabsight.validation import validate_dataset  # noqa: E402


def _hash_files(directory: Path) -> dict[str, str]:
    return {
        name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
        for name in DATASET_FILES
    }


def test_generated_files_exist(tmp_path: Path) -> None:
    generate_and_save(tmp_path)
    assert all((tmp_path / name).is_file() for name in DATASET_FILES)


def test_ids_foreign_keys_and_mandatory_values(tmp_path: Path) -> None:
    tables = generate_and_save(tmp_path)
    assert validate_dataset(tables) == []
    for table in tables.values():
        assert not table.isna().any().any()


def test_each_wafer_has_expected_process_order(tmp_path: Path) -> None:
    tables = generate_and_save(tmp_path)
    events = tables["process_events"]
    step_order = tables["process_steps"].set_index("step_id")["step_order"]
    observed = events.assign(order=events["step_id"].map(step_order)).groupby("wafer_id")["order"].apply(list)
    assert observed.apply(lambda values: values == [1, 2, 3, 4, 5, 6, 7]).all()


def test_generated_csvs_are_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    generate_and_save(first, seed=RANDOM_SEED)
    generate_and_save(second, seed=RANDOM_SEED)
    assert _hash_files(first) == _hash_files(second)


def test_lot_wafer_counts_match(tmp_path: Path) -> None:
    tables = generate_and_save(tmp_path)
    actual = tables["wafers"].groupby("lot_id").size()
    expected = tables["lots"].set_index("lot_id")["wafer_count"]
    pd.testing.assert_series_equal(actual, expected, check_names=False)
