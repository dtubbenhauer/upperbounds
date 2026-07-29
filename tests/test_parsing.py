"""Tests for shared workbook parsing helpers."""

from __future__ import annotations

import pandas as pd

from upperbounds.data.parsing import (
    canon_coeff_key,
    canon_coeff_key_mirror,
    ensure_minmax_coeffs,
    format_unknotting,
    normalize_invariant_key_cell,
    parse_pd_cell,
    parse_unknotting_entry,
    parse_vector_cell,
    pick_first_existing,
)


def test_pick_first_existing_is_case_insensitive() -> None:
    df = pd.DataFrame(columns=["knot_id", "PD_Presentation"])

    assert pick_first_existing(df, ["pd_presentation"]) == "PD_Presentation"


def test_parse_pd_cell_handles_list_and_x_notation() -> None:
    expected = [[1, 5, 2, 4], [3, 1, 4, 6]]

    assert parse_pd_cell(str(expected)) == expected
    assert parse_pd_cell("X[1,5,2,4] X[3,1,4,6]") == expected


def test_parse_vector_cell_extracts_integer_values() -> None:
    assert parse_vector_cell("[1, 4, 1, 0, 1, -1]") == [1, 4, 1, 0, 1, -1]


def test_ensure_minmax_coeffs_validates_length() -> None:
    assert ensure_minmax_coeffs([1, 3, 7, 8, 9]) == (1, 3, [7, 8, 9])
    assert ensure_minmax_coeffs([1, 3, 7]) is None


def test_canonical_coefficient_keys_strip_external_zeros() -> None:
    assert canon_coeff_key([0, 1, 0, -1, 0]) == (1, 0, -1)
    assert canon_coeff_key_mirror([0, 1, 0, -1, 0]) == (-1, 0, 1)


def test_parse_unknotting_entry_distinguishes_exact_and_range() -> None:
    assert parse_unknotting_entry(2)["kind"] == "exact"
    assert parse_unknotting_entry("[2, 3]") == {
        "kind": "range",
        "lower": 2,
        "upper": 3,
        "raw": "[2, 3]",
    }


def test_format_unknotting_preserves_notebook_output_format() -> None:
    assert format_unknotting(2, 3) == "[2, 3]"
    assert format_unknotting(None, 3) is None


def test_normalize_invariant_key_cell_canonicalizes_json() -> None:
    assert normalize_invariant_key_cell('{"b": 2, "a": 1}') == '{"a":1,"b":2}'
