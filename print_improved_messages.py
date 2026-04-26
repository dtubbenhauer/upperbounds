#!/usr/bin/env python3
"""Print only log messages that contain the word "Improved"."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


START_RE = re.compile(r"^\[\d+/\d+\]\s+Processing:")
NUMBER_RE = re.compile(r"^\d+(?:\.\d+)?$")
SEPARATOR_RE = re.compile(r"^=+$")


def trimmed_message(lines: list[str]) -> list[str]:
    """Drop trailing timing numbers/blank lines from one processing block."""
    result = [line.rstrip("\n") for line in lines]
    while result and (not result[-1].strip() or NUMBER_RE.fullmatch(result[-1].strip())):
        result.pop()
    return result


def improved_messages(path: Path) -> list[list[str]]:
    messages: list[list[str]] = []
    current: list[str] = []

    def keep_current_if_improved() -> None:
        if current and any("Improved" in item for item in current):
            messages.append(trimmed_message(current))

    with path.open("r", encoding="utf-8") as log_file:
        for line in log_file:
            if START_RE.match(line):
                keep_current_if_improved()
                current = [line]
            elif current and SEPARATOR_RE.fullmatch(line.strip()):
                keep_current_if_improved()
                current = []
            elif current:
                current.append(line)

    keep_current_if_improved()

    return messages


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Print full processing messages containing "Improved".'
    )
    parser.add_argument(
        "log_file",
        nargs="?",
        default="output.txt",
        type=Path,
        help="Path to the log file, default: output.txt",
    )
    args = parser.parse_args()

    for index, message in enumerate(improved_messages(args.log_file)):
        if index:
            print()
        print("\n".join(message))


if __name__ == "__main__":
    main()
