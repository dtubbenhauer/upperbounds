"""Tests for Pydantic experiment configuration models."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from upperbounds.config import (
    CheckpointConfig,
    RepositoryPaths,
    SearchConfig,
    TargetSelectionConfig,
)


def test_repository_paths_populates_conventional_directories(tmp_path) -> None:
    config = RepositoryPaths(repo_root=tmp_path)

    assert config.data_dir == tmp_path / "data"
    assert config.models_dir == tmp_path / "models"
    assert config.training_dir == tmp_path / "training_data"
    assert config.outputs_dir == tmp_path / "outputs"
    assert config.workbook_path == tmp_path / "data" / "unknotting.xlsx"


def test_target_selection_rejects_unknown_mode() -> None:
    with pytest.raises(ValidationError):
        TargetSelectionConfig(process_mode="unknown")


def test_search_config_validates_ranges() -> None:
    with pytest.raises(ValidationError):
        SearchConfig(backtrack_steps_min=9, backtrack_steps_max=8)

    with pytest.raises(ValidationError):
        SearchConfig(min_database_crossings=4, max_database_crossings=3)


def test_checkpoint_config_reads_upperbounds_environment(monkeypatch) -> None:
    monkeypatch.setenv(
        "UPPERBOUNDS_CHECKPOINT_ROOT",
        "gs://the-unknotters-checkpoints/upperbounds",
    )
    monkeypatch.setenv("UPPERBOUNDS_RUN_DATE", "2026-07-27")
    monkeypatch.setenv("UPPERBOUNDS_RUN_ID", "example")

    config = CheckpointConfig.from_env()

    assert config.checkpoint_root == (
        "gs://the-unknotters-checkpoints/upperbounds"
    )
    assert config.run_date == "2026-07-27"
    assert config.run_id == "example"


def test_repository_paths_accepts_explicit_directories(tmp_path) -> None:
    data_dir = Path(tmp_path / "custom-data")

    config = RepositoryPaths(repo_root=tmp_path, data_dir=data_dir)

    assert config.data_dir == data_dir
    assert config.workbook_path == data_dir / "unknotting.xlsx"
