"""Application package metadata."""

from __future__ import annotations

import subprocess


def get_version() -> str:
    """Return application version based on merge commit count."""
    base = 1.1
    merges = int(
        subprocess.check_output(["git", "rev-list", "--count", "--merges", "HEAD"])
    )
    return f"{base + merges * 0.1:.1f}"


__version__ = get_version()

