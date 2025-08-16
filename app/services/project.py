"""Project management and metadata collection utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict

from docx import Document


@dataclass
class Chapter:
    """Metadata for a single chapter."""

    name: str
    names: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    plot: str = ""


@dataclass
class Project:
    """Representation of a translation project."""

    id: str
    title: str
    icon_path: str = "assets/empty_project.png"
    chapters: list[Chapter] = field(default_factory=list)


def _extract_metadata(text: str) -> Dict[str, List[str] | str]:
    """Very lightweight metadata extraction from *text*."""

    words = [w.strip(".,!?;:\"'()[]") for w in text.split()]
    names = sorted({w for w in words if w.istitle()})
    plot = text.splitlines()[0][:200] if text else ""
    return {
        "names": names,
        "locations": [],
        "plot": plot,
    }


class ProjectManager:
    """Load and save :class:`Project` instances."""

    def __init__(self, base_dir: Path | str = Path("data/projects")) -> None:
        self.base_dir = Path(base_dir)

    # ------------------------------------------------------------------
    def load(self, project_id: str, title: str | None = None) -> Project:
        """Load project metadata from disk or create a new project."""

        project_dir = self.base_dir / project_id
        path = project_dir / "project.json"
        if path.exists():
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            data.setdefault("icon_path", "assets/empty_project.png")
            data["chapters"] = [Chapter(**c) for c in data.get("chapters", [])]
            return Project(**data)
        return Project(id=project_id, title=title or project_id)

    # ------------------------------------------------------------------
    def save(self, project: Project) -> None:
        """Persist *project* metadata to JSON."""

        project_dir = self.base_dir / project.id
        project_dir.mkdir(parents=True, exist_ok=True)
        path = project_dir / "project.json"
        with path.open("w", encoding="utf-8") as fh:
            json.dump(asdict(project), fh, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    def add_chapter(self, project: Project, name: str, text: str) -> None:
        """Append a chapter entry and save associated files."""

        meta = _extract_metadata(text)
        project.chapters.append(Chapter(name=name, **meta))
        self._save_chapter_docx(project.id, name, text)
        self.save(project)

    # ------------------------------------------------------------------
    def _save_chapter_docx(self, project_id: str, name: str, text: str) -> None:
        """Persist chapter *text* to a DOCX file using ``python-docx``."""

        project_dir = self.base_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        file_path = project_dir / f"{name}.docx"
        doc = Document()
        for paragraph in text.splitlines():
            doc.add_paragraph(paragraph)
        doc.save(file_path)

    # ------------------------------------------------------------------
    def overview(self, project: Project, upto: int) -> str:
        """Return a short summary of chapters before index ``upto``."""

        parts: list[str] = []
        for chapter in project.chapters[:upto]:
            parts.append(f"{chapter.name}: {chapter.plot}")
        return "\n".join(parts)
