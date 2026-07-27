"""Tests for checkpoint path generation and local writes."""

from __future__ import annotations

import datetime as dt
import json

from upperbounds.io.checkpoints import (
    CheckpointWriter,
    default_run_id,
    join_uri,
    utc_run_date,
)


def test_utc_run_date_uses_utc_date() -> None:
    moment = dt.datetime(2026, 7, 26, 23, 30, tzinfo=dt.timezone.utc)

    assert utc_run_date(moment) == "2026-07-26"


def test_default_run_id_has_timestamp_prefix() -> None:
    moment = dt.datetime(2026, 7, 27, 1, 2, 3, tzinfo=dt.timezone.utc)

    assert default_run_id(moment).startswith("20260727T010203Z-")


def test_join_uri_preserves_gcs_scheme() -> None:
    result = join_uri(
        "gs://the-unknotters-checkpoints/upperbounds/",
        "/run_date=2026-07-27/",
        "results.jsonl",
    )

    assert result == (
        "gs://the-unknotters-checkpoints/upperbounds/"
        "run_date=2026-07-27/results.jsonl"
    )


def test_checkpoint_writer_writes_local_jsonl(tmp_path) -> None:
    writer = CheckpointWriter(
        root_uri=str(tmp_path),
        run_date="2026-07-27",
        run_id="example-run",
    )

    destination = writer.append_jsonl("results/output.jsonl", {"knot": "3_1"})
    writer.append_jsonl("results/output.jsonl", {"knot": "4_1"})

    output_path = tmp_path / "run_date=2026-07-27" / "run_id=example-run"
    output_path = output_path / "results" / "output.jsonl"
    lines = output_path.read_text().splitlines()
    records = [json.loads(line) for line in lines]

    assert destination == str(output_path)
    assert records == [{"knot": "3_1"}, {"knot": "4_1"}]
