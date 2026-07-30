"""Tests for shared RL runtime helpers."""

from __future__ import annotations

import pandas as pd
import pytest

from upperbounds.rl.runtime import (
    EnvCfg,
    clean_pd_lines,
    default_local_training_files,
    default_model_path_candidates,
    find_existing_model_path,
    load_or_train_ppo_model,
    make_sb3_load_custom_objects,
    parse_link_strict,
    read_first_col_local,
    workbook_pd_lines,
)


def test_default_model_path_candidates_preserve_order(
    tmp_path,
) -> None:
    models_dir = tmp_path / "models"
    outputs_dir = tmp_path / "outputs"

    assert default_model_path_candidates(models_dir, outputs_dir) == [
        models_dir / "best_model.zip",
        models_dir / "ppo_knot_rl_spherogram_continued.zip",
        outputs_dir / "best_model.zip",
    ]


def test_default_local_training_files_preserve_notebook_order(tmp_path) -> None:
    training_dir = tmp_path / "training"
    data_dir = tmp_path / "data"

    assert default_local_training_files(training_dir, data_dir)[:2] == [
        training_dir / "hard_unknots.csv",
        training_dir / "very_hard_unknots.csv",
    ]


def test_find_existing_model_path_returns_first_existing(
    tmp_path,
) -> None:
    missing = tmp_path / "missing.zip"
    existing = tmp_path / "best_model.zip"
    existing.write_text("model")

    assert find_existing_model_path([missing, existing]) == existing


def test_make_sb3_load_custom_objects_returns_constant_schedule() -> None:
    custom_objects = make_sb3_load_custom_objects(default_lr=0.125)

    assert custom_objects["learning_rate"] == 0.125
    assert custom_objects["lr_schedule"](0.5) == 0.125


def test_parse_link_strict_accepts_pd_list() -> None:
    link = parse_link_strict("[[1,5,2,4],[3,1,4,6],[5,3,6,2]]")

    assert len(link.crossings) == 3


def test_clean_pd_lines_filters_invalid_entries() -> None:
    lines = ["not a pd", "[[1,5,2,4],[3,1,4,6],[5,3,6,2]]"]

    assert clean_pd_lines(lines) == [lines[1]]


def test_read_first_col_local_reads_csv_rows(tmp_path) -> None:
    csv_path = tmp_path / "training.csv"
    csv_path.write_text("pd,meta\none,a\ntwo,b\n")

    assert read_first_col_local(str(csv_path)) == ["one", "two"]


def test_workbook_pd_lines_serializes_valid_pd_rows() -> None:
    df = pd.DataFrame(
        {
            "pd": [
                "[[1,5,2,4],[3,1,4,6],[5,3,6,2]]",
                None,
            ]
        }
    )

    assert workbook_pd_lines(df, "pd") == [
        "[[1, 5, 2, 4], [3, 1, 4, 6], [5, 3, 6, 2]]"
    ]


def test_env_cfg_validates_max_steps() -> None:
    with pytest.raises(ValueError):
        EnvCfg(max_steps=0)


def test_load_or_train_raises_without_model_when_training_disabled(
    tmp_path,
) -> None:
    with pytest.raises(FileNotFoundError):
        load_or_train_ppo_model(
            model_path_candidates=[tmp_path / "missing.zip"],
            train_if_model_missing=False,
            train_steps_if_needed=1,
            cfg=EnvCfg(max_steps=1),
            local_extra_files=[],
            df=pd.DataFrame({"pd": []}),
            pd_col="pd",
            seed=0,
            output_model_path=tmp_path / "best_model.zip",
        )
