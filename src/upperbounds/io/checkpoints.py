"""Checkpoint writers for local and GCS-backed experiment outputs."""

from __future__ import annotations

import datetime as dt
import io
import json
import os
import uuid
from pathlib import Path
from typing import Any


DEFAULT_CHECKPOINT_ROOT = "gs://the-unknotters-checkpoints/upperbounds"


def utc_run_date(now: dt.datetime | None = None) -> str:
    """Return the UTC run date used for partitioned checkpoint paths.

    Args:
        now: Optional datetime to format. Naive values are treated as UTC.

    Returns:
        A date string in ISO format, such as `2026-07-27`.
    """
    value = now or dt.datetime.now(dt.UTC)
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt.UTC)
    return value.astimezone(dt.UTC).date().isoformat()


def default_run_id(now: dt.datetime | None = None) -> str:
    """Return a unique run identifier suitable for checkpoint directories.

    Args:
        now: Optional datetime to use as the timestamp prefix.

    Returns:
        A timestamp plus short random suffix.
    """
    value = now or dt.datetime.now(dt.UTC)
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt.UTC)
    stamp = value.astimezone(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


def join_uri(*parts: str) -> str:
    """Join URI or path fragments with exactly one slash between parts.

    Args:
        *parts: URI/path fragments to join.

    Returns:
        The joined URI/path string.
    """
    if not parts:
        return ""

    first = parts[0].rstrip("/")
    rest = [part.strip("/") for part in parts[1:] if part]
    if first.startswith("gs:"):
        first = "gs://" + first.removeprefix("gs:").strip("/")
    return "/".join([first, *rest])


class CheckpointWriter:
    """Write experiment checkpoints under a run-date partition."""

    def __init__(
        self,
        root_uri: str = DEFAULT_CHECKPOINT_ROOT,
        run_date: str | None = None,
        run_id: str | None = None,
    ) -> None:
        """Initialize the checkpoint writer.

        Args:
            root_uri: Local path or `gs://` URI used as the checkpoint root.
            run_date: Optional date partition. Defaults to today's UTC date.
            run_id: Optional run identifier. Defaults to a unique UTC id.
        """
        self.root_uri = root_uri.rstrip("/")
        self.run_date = run_date or utc_run_date()
        self.run_id = run_id or default_run_id()

    @classmethod
    def from_env(cls) -> "CheckpointWriter":
        """Build a writer from environment variables.

        Returns:
            A writer using `UPPERBOUNDS_CHECKPOINT_ROOT`,
            `UPPERBOUNDS_RUN_DATE`, and `UPPERBOUNDS_RUN_ID` when set.
        """
        return cls(
            root_uri=os.environ.get(
                "UPPERBOUNDS_CHECKPOINT_ROOT", DEFAULT_CHECKPOINT_ROOT
            ),
            run_date=os.environ.get("UPPERBOUNDS_RUN_DATE"),
            run_id=os.environ.get("UPPERBOUNDS_RUN_ID"),
        )

    @property
    def is_gcs(self) -> bool:
        """Return whether this writer targets Google Cloud Storage."""
        return self.root_uri.startswith("gs://")

    @property
    def run_uri(self) -> str:
        """Return the base URI for this run's checkpoints."""
        return join_uri(
            self.root_uri,
            f"run_date={self.run_date}",
            f"run_id={self.run_id}",
        )

    def path(self, *parts: str) -> str:
        """Return a checkpoint URI/path below this run directory.

        Args:
            *parts: Relative path fragments below the run directory.

        Returns:
            A local path or `gs://` URI.
        """
        return join_uri(self.run_uri, *parts)

    def write_text(self, relative_path: str, text: str) -> str:
        """Write text to a checkpoint object.

        Args:
            relative_path: Path below this run directory.
            text: Text content to write.

        Returns:
            The destination URI/path.
        """
        destination = self.path(relative_path)
        self._write_bytes(destination, text.encode("utf-8"))
        return destination

    def write_json(self, relative_path: str, payload: Any) -> str:
        """Write a JSON checkpoint object.

        Args:
            relative_path: Path below this run directory.
            payload: JSON-serializable payload.

        Returns:
            The destination URI/path.
        """
        text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        return self.write_text(relative_path, text)

    def append_jsonl(self, relative_path: str, payload: Any) -> str:
        """Append one JSONL record to a local or GCS checkpoint object.

        Args:
            relative_path: Path below this run directory.
            payload: JSON-serializable payload.

        Returns:
            The destination URI/path.
        """
        destination = self.path(relative_path)
        line = json.dumps(payload, ensure_ascii=False) + "\n"
        self._append_text(destination, line)
        return destination

    def write_excel(self, relative_path: str, dataframe: Any) -> str:
        """Write a pandas DataFrame as an Excel checkpoint.

        Args:
            relative_path: Path below this run directory.
            dataframe: Object exposing `to_excel`.

        Returns:
            The destination URI/path.
        """
        buffer = io.BytesIO()
        dataframe.to_excel(buffer, index=False)
        destination = self.path(relative_path)
        self._write_bytes(destination, buffer.getvalue())
        return destination

    def _write_bytes(self, destination: str, payload: bytes) -> None:
        if self.is_gcs:
            import gcsfs

            fs = gcsfs.GCSFileSystem()
            with fs.open(destination, "wb") as output_file:
                output_file.write(payload)
            return

        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    def _append_text(self, destination: str, text: str) -> None:
        if self.is_gcs:
            import gcsfs

            fs = gcsfs.GCSFileSystem()
            mode = "a" if fs.exists(destination) else "w"
            with fs.open(destination, mode, encoding="utf-8") as output_file:
                output_file.write(text)
            return

        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as output_file:
            output_file.write(text)
