"""Target-row selection helpers for experiment notebooks."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict

from upperbounds.data.parsing import parse_unknotting_entry


_KNOT_ORDER_RE = re.compile(r"^(\d+)(?:[a-zA-Z])?_(\d+)$")


def normalize_knot_id(knot: Any) -> str:
    """Normalize a workbook knot identifier."""
    return str(knot).strip()


def knot_crossing_and_number(knot_name: Any) -> tuple[int, int] | None:
    """Parse a knot id into crossing number and within-crossing index.

    Args:
        knot_name: Knot id such as `14_123`.

    Returns:
        `(crossing_number, knot_number)`, or `None` if the id is not parseable.
    """
    match = _KNOT_ORDER_RE.match(str(knot_name).strip())
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


class TargetSelectionResult(BaseModel):
    """Notebook-compatible target selection outputs."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    all_range_targets: list[dict[str, Any]]
    bounds_targets: list[dict[str, Any]]
    neq_targets: list[dict[str, Any]]
    crossing_targets: list[dict[str, Any]]
    targets: list[dict[str, Any]]

    def as_notebook_globals(self) -> dict[str, list[dict[str, Any]]]:
        """Return legacy global target names expected by notebooks."""
        return {
            "all_range_targets": self.all_range_targets,
            "bounds_targets": self.bounds_targets,
            "neq_targets": self.neq_targets,
            "crossing_targets": self.crossing_targets,
            "targets": self.targets,
        }


def select_targets(
    df: pd.DataFrame,
    knot_col: str,
    u_col: str,
    process_mode: str,
    target_lower: int,
    target_upper: int,
    start_index: int = 0,
    end_index: int | None = None,
    first_n: int = 100,
    target_crossing_number: int | None = None,
    target_knot_ids: list[str] | tuple[str, ...] = (),
) -> TargetSelectionResult:
    """Build target lists and select the active run targets.

    Args:
        df: Workbook DataFrame.
        knot_col: Knot id column name.
        u_col: Unknotting-number column name.
        process_mode: Selection mode used by current notebooks.
        target_lower: Lower bound used by bounds-equality modes.
        target_upper: Upper bound used by bounds-equality modes.
        start_index: Slice start index.
        end_index: Slice end index.
        first_n: Number of rows for `first_n` mode.
        target_crossing_number: Crossing number for `crossing_number` mode.
        target_knot_ids: Explicit knot ids for `knot_ids` mode.

    Returns:
        A target selection result with legacy notebook target lists.

    Raises:
        ValueError: If `process_mode` is unknown or explicit knot ids are
            invalid/missing.
    """
    all_range_targets = []
    crossing_targets = []

    for index, row in df.iterrows():
        knot_name = row.get(knot_col)
        unknotting = parse_unknotting_entry(row.get(u_col))
        if unknotting["kind"] == "range":
            all_range_targets.append(
                {
                    "row_index": int(index),
                    "knot": knot_name,
                    "lower": int(unknotting["lower"]),
                    "upper": int(unknotting["upper"]),
                }
            )

        knot_order = knot_crossing_and_number(knot_name)
        if (
            target_crossing_number is not None
            and knot_order is not None
            and knot_order[0] == target_crossing_number
            and unknotting["upper"] is not None
        ):
            crossing_targets.append(
                {
                    "row_index": int(index),
                    "knot": knot_name,
                    "lower": (
                        None
                        if unknotting["lower"] is None
                        else int(unknotting["lower"])
                    ),
                    "upper": int(unknotting["upper"]),
                    "knot_number": int(knot_order[1]),
                }
            )

    crossing_targets.sort(key=lambda target: target["knot_number"])
    bounds_targets = [
        target
        for target in all_range_targets
        if target["lower"] == target_lower and target["upper"] == target_upper
    ]
    neq_targets = list(all_range_targets)

    if process_mode == "all":
        targets = list(all_range_targets)
    elif process_mode == "first_n":
        targets = list(all_range_targets[:first_n])
    elif process_mode == "slice":
        targets = list(all_range_targets[start_index:end_index])
    elif process_mode == "bounds_eq":
        targets = list(bounds_targets)
    elif process_mode == "bounds_eq_slice":
        targets = list(bounds_targets[start_index:end_index])
    elif process_mode == "bounds_neq":
        targets = list(neq_targets)
    elif process_mode == "bounds_neq_slice":
        targets = list(neq_targets[start_index:end_index])
    elif process_mode == "crossing_number":
        targets = list(crossing_targets[start_index:end_index])
    elif process_mode == "knot_ids":
        targets = _targets_for_knot_ids(df, knot_col, u_col, target_knot_ids)
    else:
        raise ValueError(f"Unknown PROCESS_MODE: {process_mode}")

    return TargetSelectionResult(
        all_range_targets=all_range_targets,
        bounds_targets=bounds_targets,
        neq_targets=neq_targets,
        crossing_targets=crossing_targets,
        targets=targets,
    )


def print_target_summary(
    selection: TargetSelectionResult,
    target_lower: int,
    target_upper: int,
    target_crossing_number: int | None = None,
) -> None:
    """Print notebook-compatible target selection summary output."""
    print(
        "All range-valued unknotting rows (all [a,b] with a != b):",
        len(selection.all_range_targets),
    )
    if target_crossing_number is not None:
        print(
            f"Rows with crossing number {target_crossing_number}:",
            len(selection.crossing_targets),
        )
        if selection.crossing_targets:
            print(
                "First crossing target:",
                selection.crossing_targets[0]["knot"],
            )
            print(
                "Last crossing target :",
                selection.crossing_targets[-1]["knot"],
            )
    print(
        f"Rows with unknotting range [{target_lower},{target_upper}]:",
        len(selection.bounds_targets),
    )
    print(
        "Rows with non-exact unknotting range [a,b], a != b:",
        len(selection.neq_targets),
    )
    print("Selected targets:", len(selection.targets))


def _targets_for_knot_ids(
    df: pd.DataFrame,
    knot_col: str,
    u_col: str,
    target_knot_ids: list[str] | tuple[str, ...],
) -> list[dict[str, Any]]:
    wanted = {normalize_knot_id(knot) for knot in target_knot_ids}
    targets = []
    for index, row in df.iterrows():
        knot_name = normalize_knot_id(row.get(knot_col))
        if knot_name not in wanted:
            continue
        unknotting = parse_unknotting_entry(row.get(u_col))
        if unknotting["upper"] is None:
            raise ValueError(
                f"Target {knot_name} has no usable upper bound: "
                f"{row.get(u_col)!r}"
            )
        targets.append(
            {
                "row_index": int(index),
                "knot": row.get(knot_col),
                "lower": (
                    int(unknotting["lower"])
                    if unknotting["lower"] is not None
                    else None
                ),
                "upper": int(unknotting["upper"]),
            }
        )

    missing = wanted - {normalize_knot_id(target["knot"]) for target in targets}
    if missing:
        raise ValueError(
            f"TARGET_KNOT_IDS not found in workbook: {sorted(missing)}"
        )
    return targets
