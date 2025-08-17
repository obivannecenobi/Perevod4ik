"""Application package metadata."""

from __future__ import annotations

import subprocess


def get_version() -> str:
    """Return application version ``1.1 + merges*0.1``.

    The version is calculated from the number of commits in the repository.
    Each commit increases the version by ``0.1`` starting from ``1.1``.
    ``git`` is queried via ``git rev-list --count HEAD``; if that command
    fails, ``1.1`` is returned.
    """

    try:
        merges = int(
            subprocess.check_output(
                ["git", "rev-list", "--count", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except (subprocess.SubprocessError, FileNotFoundError, ValueError):
        merges = 0

    version = 1.1 + merges * 0.1
    return f"{version:.1f}"


__version__ = get_version()

