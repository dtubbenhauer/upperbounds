"""Repository path setup helpers for notebooks."""

from __future__ import annotations

import shutil
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from upperbounds.config import RepositoryPaths


class NotebookPathContext(BaseModel):
    """Notebook-compatible repository path context."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    repo_root: Path
    data_dir: Path
    models_dir: Path
    training_dir: Path
    outputs_dir: Path
    workbook_path: Path
    source_workbook_path: Path
    experiment_workbook_path: Path | None = None
    updated_workbook_path: Path | None = None

    def as_notebook_globals(self) -> dict[str, Path]:
        """Return legacy global names expected by current notebooks."""
        values = {
            "REPO_ROOT": self.repo_root,
            "DATA_DIR": self.data_dir,
            "MODELS_DIR": self.models_dir,
            "TRAINING_DIR": self.training_dir,
            "OUT_DIR": self.outputs_dir,
            "XLSX_PATH": self.workbook_path,
            "SOURCE_XLSX_PATH": self.source_workbook_path,
            "BASE": self.repo_root,
        }
        if self.experiment_workbook_path is not None:
            values["EXPERIMENT_XLSX_PATH"] = self.experiment_workbook_path
        if self.updated_workbook_path is not None:
            values["UPDATED_XLSX_PATH"] = self.updated_workbook_path
        return values

    def print_summary(self) -> None:
        """Print the path summary used by notebook setup cells."""
        print("REPO_ROOT:", self.repo_root)
        if self.source_workbook_path != self.workbook_path:
            print("Source   :", self.source_workbook_path)
        print("Workbook :", self.workbook_path)
        if self.updated_workbook_path is not None:
            print("Updated  :", self.updated_workbook_path)
        print("MODELS   :", self.models_dir)
        print("TRAINING :", self.training_dir)
        print("OUTPUTS  :", self.outputs_dir)


def find_repo_root(candidate_roots: list[Path] | None = None) -> Path:
    """Find the repository root from common notebook launch locations.

    Args:
        candidate_roots: Candidate roots to inspect. Defaults to current
            working directory and its parent.

    Returns:
        The first candidate containing a repository data/model/training folder.
    """
    candidates = candidate_roots or [Path.cwd(), Path.cwd().parent]
    for candidate in candidates:
        if (
            (candidate / "data").exists()
            or (candidate / "models").exists()
            or (candidate / "training_data").exists()
        ):
            return candidate
    return Path.cwd()


def prepare_notebook_paths(
    repo_root: Path | None = None,
    experiment_workbook_name: str | None = None,
    updated_workbook_suffix: str | None = None,
) -> NotebookPathContext:
    """Prepare repository paths and optional workbook aliases.

    Args:
        repo_root: Optional explicit repository root.
        experiment_workbook_name: Optional workbook copy name under outputs.
        updated_workbook_suffix: Optional suffix for an updated workbook path.

    Returns:
        A notebook-compatible path context.

    Raises:
        FileNotFoundError: If the source workbook does not exist.
    """
    paths = RepositoryPaths(repo_root=repo_root or find_repo_root())
    for folder in [
        paths.data_dir,
        paths.models_dir,
        paths.training_dir,
        paths.outputs_dir,
    ]:
        if folder is not None:
            folder.mkdir(parents=True, exist_ok=True)

    source_workbook_path = paths.workbook_path
    if not source_workbook_path.exists():
        raise FileNotFoundError(
            f"Missing workbook: {source_workbook_path}\n"
            "Place your database at repo-root/data/unknotting.xlsx"
        )

    workbook_path = source_workbook_path
    experiment_workbook_path = None
    if experiment_workbook_name is not None:
        if paths.outputs_dir is None:
            raise ValueError("outputs_dir must be configured")
        experiment_workbook_path = paths.outputs_dir / experiment_workbook_name
        if not experiment_workbook_path.exists():
            shutil.copy2(source_workbook_path, experiment_workbook_path)
            print("Created workbook copy:", experiment_workbook_path)
        else:
            print("Reusing workbook copy:", experiment_workbook_path)
        workbook_path = experiment_workbook_path

    updated_workbook_path = None
    if updated_workbook_suffix is not None:
        if paths.outputs_dir is None:
            raise ValueError("outputs_dir must be configured")
        updated_workbook_path = (
            paths.outputs_dir
            / f"{source_workbook_path.stem}_{updated_workbook_suffix}.xlsx"
        )

    if (
        paths.data_dir is None
        or paths.models_dir is None
        or paths.training_dir is None
        or paths.outputs_dir is None
    ):
        raise ValueError("repository paths were not fully initialized")

    return NotebookPathContext(
        repo_root=paths.repo_root,
        data_dir=paths.data_dir,
        models_dir=paths.models_dir,
        training_dir=paths.training_dir,
        outputs_dir=paths.outputs_dir,
        workbook_path=workbook_path,
        source_workbook_path=source_workbook_path,
        experiment_workbook_path=experiment_workbook_path,
        updated_workbook_path=updated_workbook_path,
    )
