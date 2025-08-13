"""Utilities for managing translation versions and update checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import subprocess
from pathlib import Path
from typing import List, Dict, Any

from .files import load_versions, save_versions


@dataclass
class VersionManager:
    """Keep track of translation revisions and persist them to disk."""

    path: Path
    versions: List[Dict[str, Any]] = field(default_factory=list)
    index: int = -1

    def __post_init__(self) -> None:
        self.versions = load_versions(self.path)
        if self.versions:
            self.index = len(self.versions) - 1

    def add_version(self, text: str) -> None:
        """Append *text* as a new revision if it differs from current."""

        if self.index >= 0 and self.versions[self.index]["text"] == text:
            return
        del self.versions[self.index + 1 :]
        self.versions.append({"timestamp": datetime.utcnow().isoformat(), "text": text})
        self.index = len(self.versions) - 1
        save_versions(self.versions, self.path)

    def undo(self) -> str | None:
        """Step back in history and return the previous text."""

        if self.index > 0:
            self.index -= 1
            save_versions(self.versions, self.path)
            return self.versions[self.index]["text"]
        return None

    def redo(self) -> str | None:
        """Step forward in history and return the next text."""

        if self.index < len(self.versions) - 1:
            self.index += 1
            save_versions(self.versions, self.path)
            return self.versions[self.index]["text"]
        return None


def check_for_updates(repo_path: Path) -> bool:
    """Return ``True`` if *repo_path* has updates available."""

    try:
        subprocess.run(["git", "fetch"], cwd=repo_path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        status = subprocess.run(
            ["git", "status", "-uno"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        return "behind" in status.stdout.lower()
    except Exception:
        return False
