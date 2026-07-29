"""Workbook loading and column-identification helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from pydantic import BaseModel

from upperbounds.data.parsing import pick_first_existing


class WorkbookColumns(BaseModel):
    """Column names used by experiment notebooks."""

    knot_col: str
    pd_col: str
    u_col: str
    jones_col: str | None = None
    hfk_col: str | None = None
    strong_col: str | None = None

    def as_notebook_globals(self) -> dict[str, str | None]:
        """Return legacy global column names expected by notebooks."""
        values = {
            "knot_col": self.knot_col,
            "pd_col": self.pd_col,
            "u_col": self.u_col,
        }
        if self.jones_col is not None:
            values["jones_col"] = self.jones_col
        if self.hfk_col is not None:
            values["hfk_col"] = self.hfk_col
        if self.strong_col is not None:
            values["strong_col"] = self.strong_col
        return values

    def print_summary(self) -> None:
        """Print notebook-compatible column summary output."""
        print("Columns:")
        print("  knot_col :", self.knot_col)
        if self.jones_col is not None:
            print("  jones_col:", self.jones_col)
        print("  pd_col   :", self.pd_col)
        print("  u_col    :", self.u_col)
        if self.hfk_col is not None:
            print("  hfk_col  :", self.hfk_col)
        if self.strong_col is not None:
            print("  strong_col:", self.strong_col)


def load_workbook_with_columns(
    workbook_path: Path,
    include_jones: bool = True,
    include_hfk: bool = False,
    include_strong: bool = False,
) -> tuple[pd.DataFrame, WorkbookColumns]:
    """Load a workbook and identify expected notebook columns.

    Args:
        workbook_path: Excel workbook path.
        include_jones: Whether to identify/create the Jones-vector column.
        include_hfk: Whether to identify/create the HFK invariant key column.
        include_strong: Whether to identify/create the strong invariant column.

    Returns:
        The loaded DataFrame and identified column names.

    Raises:
        ValueError: If required knot, PD, or unknotting columns are missing.
    """
    df = pd.read_excel(workbook_path)

    knot_col = pick_first_existing(df, ["knot_id", "name", "knot", "id"])
    pd_col = pick_first_existing(
        df,
        ["pd_presentation", "pd_notation", "pd", "pd_code"],
    )
    u_col = pick_first_existing(df, ["unknotting_number", "unknotting", "u"])

    if knot_col is None or pd_col is None or u_col is None:
        raise ValueError(
            "Could not identify the required knot / PD / "
            "unknotting-number columns."
        )

    jones_col = None
    if include_jones:
        jones_col = pick_first_existing(
            df,
            ["jones_vector", "jones_polynomial_vector"],
        )
        if jones_col is None:
            jones_col = "jones_vector"
            df[jones_col] = None
            print(f"Created missing Jones column: {jones_col}")

    hfk_col = None
    if include_hfk:
        hfk_col = pick_first_existing(
            df,
            [
                "hfk_invariant_key",
                "strong_invariant_key",
                "floer_invariant_key",
            ],
        )
        if hfk_col is None:
            hfk_col = "hfk_invariant_key"
            df[hfk_col] = None
            print(f"Created missing HFK key column: {hfk_col}")

    strong_col = None
    if include_strong:
        strong_col = pick_first_existing(
            df,
            [
                "strong_invariant_key",
                "floer_invariant_key",
                "alex_sig_det_key",
            ],
        )
        if strong_col is None:
            strong_col = "strong_invariant_key"
            df[strong_col] = None
            print(f"Created missing strong-invariant column: {strong_col}")

    return df, WorkbookColumns(
        knot_col=knot_col,
        pd_col=pd_col,
        u_col=u_col,
        jones_col=jones_col,
        hfk_col=hfk_col,
        strong_col=strong_col,
    )
