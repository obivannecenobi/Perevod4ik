from __future__ import annotations

"""Simple project management utilities.

This module persists a list of projects and their paths in a JSON file. The
file contains two categories: ``active`` and ``archived``. Each project is a
mapping with ``name`` and ``path`` keys.
"""

from pathlib import Path
import json
from typing import Dict, List

PROJECTS_FILE = Path(__file__).resolve().parent / "projects.json"

def load_projects() -> Dict[str, List[Dict[str, str]]]:
    """Return project data from :data:`PROJECTS_FILE`.

    The resulting dictionary always contains ``active`` and ``archived`` keys.
    """
    if PROJECTS_FILE.exists():
        try:
            with PROJECTS_FILE.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                return {
                    "active": list(data.get("active", [])),
                    "archived": list(data.get("archived", [])),
                }
        except json.JSONDecodeError:
            pass
    return {"active": [], "archived": []}

def save_projects(projects: Dict[str, List[Dict[str, str]]]) -> None:
    """Persist project data to :data:`PROJECTS_FILE`."""
    PROJECTS_FILE.write_text(
        json.dumps(projects, ensure_ascii=False, indent=2), encoding="utf-8"
    )

def add_project(name: str, path: str, archived: bool = False) -> None:
    """Add a project and save it.

    Parameters
    ----------
    name:
        Display name of the project.
    path:
        Filesystem path to the project.
    archived:
        If ``True`` the project is added to the ``archived`` collection,
        otherwise to ``active``.
    """
    projects = load_projects()
    key = "archived" if archived else "active"
    if not any(p["name"] == name for p in projects[key]):
        projects[key].append({"name": name, "path": path})
        save_projects(projects)
