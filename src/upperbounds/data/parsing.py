"""Shared parsing helpers used by the experiment notebooks."""

from __future__ import annotations

import ast
import json
import re
from typing import Any

import numpy as np
import pandas as pd


_INT_RE = re.compile(r"-?\d+")


def pick_first_existing(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Return the first candidate column present in a DataFrame.

    Args:
        df: DataFrame whose columns are searched case-insensitively.
        candidates: Candidate column names in priority order.

    Returns:
        The matched DataFrame column name, or `None` when no candidate exists.
    """
    lower_map = {str(column).lower(): column for column in df.columns}
    for candidate in candidates:
        if candidate.lower() in lower_map:
            return str(lower_map[candidate.lower()])
    return None


def parse_pd_cell(value: Any) -> list[list[int]] | None:
    """Parse a planar-diagram cell into integer crossing quadruples.

    Args:
        value: Workbook cell value containing a PD list or `X[...]` notation.

    Returns:
        A list of crossing quadruples, or `None` when parsing fails.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, list):
        return [[int(item) for item in quadruple] for quadruple in value]

    text = str(value).strip()
    if not text or text.lower() in {"nan", "none"}:
        return None

    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list) and all(
            isinstance(quadruple, (list, tuple)) and len(quadruple) == 4
            for quadruple in parsed
        ):
            return [[int(item) for item in quadruple] for quadruple in parsed]
    except Exception:
        pass

    items = re.findall(r"[Xx]\s*\[([^\]]+)\]", text)
    if not items:
        return None

    result = []
    for item in items:
        numbers = [int(part.strip()) for part in item.split(",")]
        if len(numbers) != 4:
            return None
        result.append(numbers)
    return result


def parse_vector_cell(value: Any) -> list[int] | None:
    """Parse a workbook vector cell into integers.

    Args:
        value: Workbook cell value containing a list-like vector.

    Returns:
        The parsed vector, or `None` when parsing fails.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (list, tuple)):
        try:
            return [int(item) for item in value]
        except Exception:
            return None

    text = str(value).strip()
    if not text or text.lower() in {"nan", "none"}:
        return None
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, (list, tuple)):
                return [int(item) for item in parsed]
        except Exception:
            pass

    numbers = _INT_RE.findall(text)
    if not numbers:
        return None
    return [int(number) for number in numbers]


def ensure_minmax_coeffs(
    vector: list[int] | tuple[int, ...] | None,
) -> tuple[int, int, list[int]] | None:
    """Validate and split a KnotInfo-style Jones vector.

    Args:
        vector: Vector whose first entries are min/max exponents.

    Returns:
        `(min_exponent, max_exponent, coefficients)`, or `None` if invalid.
    """
    if vector is None:
        return None
    normalized = [int(item) for item in vector]
    if len(normalized) < 3:
        return None

    min_exponent, max_exponent = normalized[0], normalized[1]
    coefficients = normalized[2:]
    if len(coefficients) != abs(max_exponent - min_exponent) + 1:
        return None
    return min_exponent, max_exponent, coefficients


def strip_leading_trailing_zeros(coefficients: list[int]) -> list[int]:
    """Remove leading and trailing zero coefficients.

    Args:
        coefficients: Polynomial coefficient sequence.

    Returns:
        The stripped sequence, preserving a single zero for all-zero input.
    """
    values = list(map(int, coefficients))
    start, end = 0, len(values)
    while start < end and values[start] == 0:
        start += 1
    while end > start and values[end - 1] == 0:
        end -= 1
    result = values[start:end]
    return result if result else [0]


def canon_coeff_key(coefficients: list[int]) -> tuple[int, ...]:
    """Return a canonical coefficient tuple ignoring exterior zeros."""
    return tuple(strip_leading_trailing_zeros(coefficients))


def canon_coeff_key_mirror(coefficients: list[int]) -> tuple[int, ...]:
    """Return the mirrored canonical coefficient tuple."""
    return tuple(reversed(strip_leading_trailing_zeros(coefficients)))


def span_abs(min_exponent: int, max_exponent: int) -> int:
    """Return the absolute span between min and max exponents."""
    return abs(int(max_exponent) - int(min_exponent))


def parse_unknotting_entry(value: Any) -> dict[str, Any]:
    """Parse exact or range-valued unknotting-number cells.

    Args:
        value: Workbook cell value.

    Returns:
        A dictionary with `kind`, `lower`, `upper`, and `raw` fields.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return {"kind": "missing", "lower": None, "upper": None, "raw": value}
    if isinstance(value, (int, np.integer)):
        number = int(value)
        return {"kind": "exact", "lower": number, "upper": number, "raw": value}
    if isinstance(value, float) and float(value).is_integer():
        number = int(value)
        return {"kind": "exact", "lower": number, "upper": number, "raw": value}

    text = str(value).strip()
    if not text or text.lower() in {"nan", "none"}:
        return {"kind": "missing", "lower": None, "upper": None, "raw": value}

    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, (list, tuple)) and len(parsed) == 2:
            lower, upper = int(parsed[0]), int(parsed[1])
            if lower == upper:
                return {
                    "kind": "exact",
                    "lower": lower,
                    "upper": upper,
                    "raw": value,
                }
            return {
                "kind": "range",
                "lower": min(lower, upper),
                "upper": max(lower, upper),
                "raw": value,
            }
    except Exception:
        pass

    numbers = [int(number) for number in _INT_RE.findall(text)]
    if len(numbers) == 1:
        return {
            "kind": "exact",
            "lower": numbers[0],
            "upper": numbers[0],
            "raw": value,
        }
    if len(numbers) >= 2:
        lower, upper = numbers[0], numbers[1]
        if lower == upper:
            return {
                "kind": "exact",
                "lower": lower,
                "upper": upper,
                "raw": value,
            }
        return {
            "kind": "range",
            "lower": min(lower, upper),
            "upper": max(lower, upper),
            "raw": value,
        }

    return {"kind": "other", "lower": None, "upper": None, "raw": value}


def format_unknotting(lower: int | None, upper: int | None) -> str | None:
    """Format an unknotting-number bound pair as workbook text.

    Args:
        lower: Lower bound.
        upper: Upper bound.

    Returns:
        A stringified two-entry list, or `None` for incomplete bounds.
    """
    if lower is None and upper is None:
        return None
    if lower is None or upper is None:
        return None
    return str([int(lower), int(upper)])


def normalize_invariant_key_cell(value: Any) -> str | None:
    """Normalize a JSON/dict invariant-key workbook cell.

    Args:
        value: Workbook cell value.

    Returns:
        A canonical JSON string, raw non-empty string, or `None`.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))

    text = str(value).strip()
    if not text or text.lower() in {"nan", "none"}:
        return None
    if text.startswith("{") and text.endswith("}"):
        try:
            parsed = json.loads(text)
            return json.dumps(parsed, sort_keys=True, separators=(",", ":"))
        except Exception:
            return text
    return text
