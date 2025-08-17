"""Application package metadata."""

from __future__ import annotations

import subprocess


def get_version() -> str:
    """Return application version ``0.1.<commit_count>``."""
    try:
        commit_count = (
            subprocess.check_output(
                ["git", "rev-list", "--count", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        commit_count = "0"
    return f"0.1.{commit_count}"


__version__ = get_version()

