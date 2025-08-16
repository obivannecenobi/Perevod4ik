"""Application package metadata."""

from __future__ import annotations

import subprocess


def get_version() -> str:
    """Return application version ``0.1.<commit_count>``."""
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        commit_count = result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        commit_count = "0"
    return f"0.1.{commit_count}"


__version__ = get_version()

