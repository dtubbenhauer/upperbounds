"""Tests for notebook path, workbook, and target helpers."""

from __future__ import annotations

import pandas as pd
import pytest

from upperbounds.io.paths import find_repo_root, prepare_notebook_paths
from upperbounds.io.workbook import load_workbook_with_columns
from upperbounds.pipeline.targets import (
    knot_crossing_and_number,
    select_targets,
)


def test_prepare_notebook_paths_sets_legacy_globals(tmp_path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (tmp_path / "models").mkdir()
    (tmp_path / "training_data").mkdir()
    (data_dir / "unknotting.xlsx").write_bytes(b"placeholder")

    context = prepare_notebook_paths(repo_root=tmp_path)

    values = context.as_notebook_globals()
    assert values["REPO_ROOT"] == tmp_path
    assert values["XLSX_PATH"] == data_dir / "unknotting.xlsx"
    assert values["BASE"] == tmp_path


def test_prepare_notebook_paths_can_create_experiment_copy(
    tmp_path,
) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    source = data_dir / "unknotting.xlsx"
    source.write_bytes(b"workbook")

    context = prepare_notebook_paths(
        repo_root=tmp_path,
        experiment_workbook_name="experiment.xlsx",
    )

    assert context.workbook_path == tmp_path / "outputs" / "experiment.xlsx"
    assert context.workbook_path.read_bytes() == b"workbook"


def test_find_repo_root_prefers_candidate_with_data(tmp_path) -> None:
    candidate = tmp_path / "repo"
    (candidate / "data").mkdir(parents=True)

    assert find_repo_root([tmp_path, candidate]) == candidate


def test_load_workbook_with_columns_creates_optional_columns(tmp_path) -> None:
    path = tmp_path / "unknotting.xlsx"
    df = pd.DataFrame(
        {
            "knot_id": ["3_1"],
            "pd_presentation": ["[[1,5,2,4]]"],
            "unknotting_number": [1],
        }
    )
    df.to_excel(path, index=False)

    loaded, columns = load_workbook_with_columns(path, include_hfk=True)

    assert columns.knot_col == "knot_id"
    assert columns.jones_col == "jones_vector"
    assert columns.hfk_col == "hfk_invariant_key"
    assert "jones_vector" in loaded.columns
    assert "hfk_invariant_key" in loaded.columns


def test_select_targets_supports_range_and_crossing_modes() -> None:
    df = pd.DataFrame(
        {
            "knot_id": ["3_1", "14_2", "14_1"],
            "unknotting_number": ["[1, 2]", "[1, 14]", 2],
        }
    )

    selected = select_targets(
        df,
        knot_col="knot_id",
        u_col="unknotting_number",
        process_mode="crossing_number",
        target_lower=1,
        target_upper=2,
        target_crossing_number=14,
    )

    assert [target["knot"] for target in selected.targets] == ["14_1", "14_2"]
    assert selected.bounds_targets == [
        {"row_index": 0, "knot": "3_1", "lower": 1, "upper": 2}
    ]


def test_select_targets_reports_missing_explicit_knots() -> None:
    df = pd.DataFrame({"knot_id": ["3_1"], "unknotting_number": [1]})

    with pytest.raises(ValueError, match="TARGET_KNOT_IDS not found"):
        select_targets(
            df,
            knot_col="knot_id",
            u_col="unknotting_number",
            process_mode="knot_ids",
            target_lower=1,
            target_upper=2,
            target_knot_ids=["4_1"],
        )


def test_knot_crossing_and_number_parses_standard_ids() -> None:
    assert knot_crossing_and_number("14_123") == (14, 123)
    assert knot_crossing_and_number("14a_123") == (14, 123)
    assert knot_crossing_and_number("not-a-knot") is None
