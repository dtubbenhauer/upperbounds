"""Tests for shared knot invariant helpers."""

from __future__ import annotations

from upperbounds.invariants.floer import hfk_keys_from_pd, normalize_hfk_dict
from upperbounds.invariants.jones import (
    jones_vector_from_pd,
    parse_jones_string_to_dict,
    poly_dict_to_knotinfo_vector,
)


TREFOIL_PD = [[1, 5, 2, 4], [3, 1, 4, 6], [5, 3, 6, 2]]


def test_jones_vector_from_pd_preserves_notebook_trefoil_vector() -> None:
    vector, error = jones_vector_from_pd(TREFOIL_PD)

    assert error is None
    assert vector == [-2, 1, 1, 0, 1, -1]


def test_parse_jones_string_to_dict_handles_signs() -> None:
    assert parse_jones_string_to_dict("t^4 + t^2 - t") == {
        4: 1,
        2: 1,
        1: -1,
    }


def test_poly_dict_to_knotinfo_vector_handles_zero_polynomial() -> None:
    assert poly_dict_to_knotinfo_vector({}) == [0, 0, 0]
    assert poly_dict_to_knotinfo_vector({-1: 2, 1: -3}) == [-1, 1, 2, 0, -3]


def test_normalize_hfk_dict_canonicalizes_rank_entries() -> None:
    result = normalize_hfk_dict(
        {
            "fibered": 1,
            "tau": "2",
            "total_rank": None,
            "ranks": {(1, 2): "3", (0, 1): 2},
        }
    )

    assert result is not None
    assert result["fibered"] is True
    assert result["tau"] == 2
    assert result["total_rank"] == 5
    assert result["ranks"] == [[0, 1, 2], [1, 2, 3]]


def test_hfk_keys_from_pd_rejects_empty_pd() -> None:
    assert hfk_keys_from_pd([]) == (None, None, "Empty PD")
