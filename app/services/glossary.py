"""Glossary management utilities.

A glossary is stored as a JSON file containing a mapping of source words to
their translations. This module provides a small helper class with common
CRUD operations used by the application.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict
import json


@dataclass
class Glossary:
    """Simple in-memory representation of a glossary."""

    name: str
    entries: Dict[str, str] = field(default_factory=dict)
    file: Path | None = None

    # ------------------------------------------------------------------
    # Word pair operations
    def add(self, source: str, target: str) -> None:
        """Add or update a word pair."""

        self.entries[source] = target

    def remove(self, source: str) -> None:
        """Remove *source* if present."""

        self.entries.pop(source, None)

    def get(self, source: str) -> str | None:
        """Return translation for *source* or ``None``."""

        return self.entries.get(source)

    # ------------------------------------------------------------------
    # Persistence helpers
    def save(self, path: Path | str | None = None) -> None:
        """Write glossary to *path* or previously associated file."""

        file_path = Path(path) if path else self.file
        if file_path is None:
            raise ValueError("Path must be provided for unsaved glossaries")
        data = {"name": self.name, "entries": self.entries}
        file_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self.file = file_path

    @classmethod
    def load(cls, path: Path | str) -> "Glossary":
        """Load glossary from *path*."""

        file_path = Path(path)
        data = json.loads(file_path.read_text(encoding="utf-8"))
        obj = cls(name=data.get("name", file_path.stem), entries=data.get("entries", {}))
        obj.file = file_path
        return obj


def list_glossaries(folder: Path | str) -> list[Path]:
    """Return all glossary JSON files in *folder*."""

    root = Path(folder)
    return sorted(root.glob("*.json"))
