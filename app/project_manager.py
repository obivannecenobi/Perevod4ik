from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .default_icon import ensure_empty_project_icon


@dataclass
class Project:
    """Simple project representation."""

    id: str
    name: str
    archived: bool = False
    icon_path: str = "assets/empty_project.png"


class ProjectManager:
    """Manage :class:`Project` instances persisted to JSON."""

    def __init__(self, root: str | Path = Path("data")) -> None:
        ensure_empty_project_icon()
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "projects.json"
        self.projects: list[Project] = []
        self.load()

    # ------------------------------------------------------------------
    def load(self) -> None:
        """Load project data from :attr:`path`."""

        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            self.projects = [Project(**item) for item in data]
        else:
            self.projects = []

    # ------------------------------------------------------------------
    def save(self) -> None:
        """Persist current project list to :attr:`path`."""

        with self.path.open("w", encoding="utf-8") as fh:
            json.dump([asdict(p) for p in self.projects], fh, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    def get(self, project_id: str) -> Project | None:
        """Return project by ``project_id`` or ``None``."""

        for proj in self.projects:
            if proj.id == project_id:
                return proj
        return None

    # ------------------------------------------------------------------
    def create(self, name: str) -> Project:
        """Create a new project with ``name``."""

        base_id = "".join(c if c.isalnum() else "_" for c in name).lower() or "project"
        existing = {p.id for p in self.projects}
        candidate = base_id
        counter = 1
        while candidate in existing:
            counter += 1
            candidate = f"{base_id}_{counter}"
        project = Project(id=candidate, name=name)
        self.projects.append(project)
        self.save()
        return project

    # ------------------------------------------------------------------
    def rename(self, project_id: str, new_name: str) -> None:
        """Rename project identified by ``project_id``."""

        proj = self.get(project_id)
        if proj:
            proj.name = new_name
            self.save()

    # ------------------------------------------------------------------
    def archive(self, project_id: str, archived: bool = True) -> None:
        """Mark project as archived or active."""

        proj = self.get(project_id)
        if proj:
            proj.archived = archived
            self.save()

    # ------------------------------------------------------------------
    def delete(self, project_id: str) -> None:
        """Delete project by ``project_id``."""

        self.projects = [p for p in self.projects if p.id != project_id]
        self.save()
