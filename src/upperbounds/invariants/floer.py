"""Knot Floer invariant key helpers."""

from __future__ import annotations

import json
from typing import Any


HFK_KEY_CACHE: dict[tuple[str, str], tuple[str | None, str | None]] = {}


def _as_int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def normalize_hfk_dict(hfk_obj: Any) -> dict[str, Any] | None:
    """Normalize SnapPy/Spherogram knot Floer homology output.

    Args:
        hfk_obj: Output from `Link.knot_floer_homology()`.

    Returns:
        A JSON-serializable normalized dictionary, or `None`.
    """
    if not isinstance(hfk_obj, dict):
        return None

    output = {
        "L_space_knot": (
            None
            if hfk_obj.get("L_space_knot") is None
            else bool(hfk_obj.get("L_space_knot"))
        ),
        "fibered": (
            None
            if hfk_obj.get("fibered") is None
            else bool(hfk_obj.get("fibered"))
        ),
        "modulus": _as_int_or_none(hfk_obj.get("modulus")),
        "seifert_genus": _as_int_or_none(hfk_obj.get("seifert_genus")),
        "tau": _as_int_or_none(hfk_obj.get("tau")),
        "nu": _as_int_or_none(hfk_obj.get("nu")),
        "epsilon": _as_int_or_none(hfk_obj.get("epsilon")),
        "total_rank": _as_int_or_none(hfk_obj.get("total_rank")),
    }

    ranks = hfk_obj.get("ranks", {})
    normalized_ranks = []
    if isinstance(ranks, dict):
        for key, value in ranks.items():
            try:
                alexander, maslov = key
                rank = int(value)
            except Exception:
                continue
            normalized_ranks.append([int(alexander), int(maslov), int(rank)])
    normalized_ranks.sort(key=lambda item: (item[0], item[1], item[2]))
    output["ranks"] = normalized_ranks

    if output["total_rank"] is None and normalized_ranks:
        output["total_rank"] = int(sum(item[2] for item in normalized_ranks))

    return output


def hfk_key_from_link(link: Any) -> str:
    """Return the canonical HFK key for a Spherogram link.

    Args:
        link: Spherogram `Link` object exposing `knot_floer_homology()`.

    Returns:
        Canonical JSON key.

    Raises:
        ValueError: If the HFK computation does not return a dictionary.
    """
    hfk = link.knot_floer_homology()
    normalized = normalize_hfk_dict(hfk)
    if normalized is None:
        raise ValueError("knot_floer_homology returned non-dict output")
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def hfk_keys_from_pd(
    pd_list: list[list[int]],
    include_mirror: bool = False,
) -> tuple[str | None, str | None, str | None]:
    """Compute direct and optional mirror HFK keys from a planar diagram.

    Args:
        pd_list: Planar diagram crossing quadruples.
        include_mirror: Whether to compute the mirror key.

    Returns:
        `(key, mirror_key, error)`, matching existing notebook behavior.
    """
    if not pd_list:
        return None, None, "Empty PD"

    pd_canon = json.dumps(pd_list, separators=(",", ":"))
    cache_key = ("mirror" if include_mirror else "direct", pd_canon)
    if cache_key in HFK_KEY_CACHE:
        key, mirror_key = HFK_KEY_CACHE[cache_key]
        return key, mirror_key, None

    try:
        from spherogram import Link

        link = Link(pd_list)
        key = hfk_key_from_link(link)
        mirror_key = None
        if include_mirror:
            mirror_key = hfk_key_from_link(link.mirror())

        HFK_KEY_CACHE[cache_key] = (key, mirror_key)
        if ("direct", pd_canon) not in HFK_KEY_CACHE:
            HFK_KEY_CACHE[("direct", pd_canon)] = (key, None)

        return key, mirror_key, None
    except Exception as exc:
        return None, None, repr(exc)
