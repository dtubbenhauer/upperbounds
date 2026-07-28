"""Pydantic configuration models for upperbounds experiments."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from upperbounds.io.checkpoints import DEFAULT_CHECKPOINT_ROOT


ProcessMode = Literal[
    "all",
    "first_n",
    "slice",
    "bounds_eq",
    "bounds_eq_slice",
    "bounds_neq",
    "bounds_neq_slice",
    "crossing_number",
    "knot_ids",
]


class RepositoryPaths(BaseModel):
    """Filesystem paths used by notebook experiments."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    repo_root: Path = Field(default_factory=Path.cwd)
    data_dir: Path | None = None
    models_dir: Path | None = None
    training_dir: Path | None = None
    outputs_dir: Path | None = None
    workbook_name: str = "unknotting.xlsx"

    @field_validator("repo_root")
    @classmethod
    def expand_repo_root(cls, value: Path) -> Path:
        """Expand and resolve the repository root path."""
        return value.expanduser().resolve()

    def model_post_init(self, __context: object) -> None:
        """Populate conventional child directories."""
        if self.data_dir is None:
            self.data_dir = self.repo_root / "data"
        if self.models_dir is None:
            self.models_dir = self.repo_root / "models"
        if self.training_dir is None:
            self.training_dir = self.repo_root / "training_data"
        if self.outputs_dir is None:
            self.outputs_dir = self.repo_root / "outputs"

    @property
    def workbook_path(self) -> Path:
        """Return the configured workbook path."""
        if self.data_dir is None:
            return self.repo_root / "data" / self.workbook_name
        return self.data_dir / self.workbook_name


class TargetSelectionConfig(BaseModel):
    """Target-row selection settings for an experiment run."""

    process_mode: ProcessMode = "slice"
    target_lower: int = 1
    target_upper: int = 2
    target_crossing_number: int = 14
    target_knot_ids: tuple[str, ...] = ()
    start_index: int = Field(default=0, ge=0)
    end_index: int | None = Field(default=10, ge=0)
    first_n: int = Field(default=100, ge=1)

    @field_validator("target_upper")
    @classmethod
    def validate_target_upper(cls, value: int) -> int:
        """Validate target upper bounds are non-negative."""
        if value < 0:
            raise ValueError("target_upper must be non-negative")
        return value


class SearchConfig(BaseModel):
    """Search and reducer settings shared by notebook variants."""

    num_variants_per_knot: int = Field(default=12, ge=1)
    backtrack_steps_min: int = Field(default=6, ge=0)
    backtrack_steps_max: int = Field(default=8, ge=0)
    riii_steps_max: int = Field(default=20, ge=0)
    unknotter_episodes_per_flip: int = Field(default=1, ge=1)
    unknotter_max_steps: int = Field(default=500, ge=1)
    max_flips_per_variant: int | None = Field(default=None, ge=1)
    min_database_crossings: int = Field(default=1, ge=0)
    max_database_crossings: int = Field(default=13, ge=0)

    @field_validator("backtrack_steps_max")
    @classmethod
    def validate_backtrack_range(cls, value: int, info) -> int:
        """Validate backtrack max is at least backtrack min."""
        minimum = info.data.get("backtrack_steps_min")
        if minimum is not None and value < minimum:
            raise ValueError(
                "backtrack_steps_max must be >= backtrack_steps_min"
            )
        return value

    @field_validator("max_database_crossings")
    @classmethod
    def validate_database_crossings(cls, value: int, info) -> int:
        """Validate max database crossings against min database crossings."""
        minimum = info.data.get("min_database_crossings")
        if minimum is not None and value < minimum:
            raise ValueError(
                "max_database_crossings must be >= min_database_crossings"
            )
        return value


class TrainingConfig(BaseModel):
    """Model loading and optional training settings."""

    train_if_model_missing: bool = True
    train_steps_if_needed: int = Field(default=20_000, ge=1)
    model_path_candidates: tuple[Path, ...] = ()


class CheckpointConfig(BaseModel):
    """Checkpoint destination settings."""

    checkpoint_root: str = DEFAULT_CHECKPOINT_ROOT
    run_date: str | None = None
    run_id: str | None = None

    @classmethod
    def from_env(cls) -> "CheckpointConfig":
        """Build checkpoint config from upperbounds environment variables."""
        return cls(
            checkpoint_root=os.environ.get(
                "UPPERBOUNDS_CHECKPOINT_ROOT", DEFAULT_CHECKPOINT_ROOT
            ),
            run_date=os.environ.get("UPPERBOUNDS_RUN_DATE") or None,
            run_id=os.environ.get("UPPERBOUNDS_RUN_ID") or None,
        )


class ExperimentConfig(BaseModel):
    """Top-level experiment configuration."""

    paths: RepositoryPaths = Field(default_factory=RepositoryPaths)
    target: TargetSelectionConfig = Field(default_factory=TargetSelectionConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    checkpoints: CheckpointConfig = Field(default_factory=CheckpointConfig)
    save_after_each_target: bool = True
    save_every_knot: bool = True
    write_updated_copy: bool = False
    make_timestamped_backup: bool = False
