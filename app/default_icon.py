from __future__ import annotations

import base64
from pathlib import Path

EMPTY_PROJECT_ICON_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAAC0lEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
)

def ensure_empty_project_icon() -> None:
    """Ensure the default project icon file exists.

    The application expects ``assets/empty_project.png`` to be present for
    projects without a custom icon. To avoid shipping a binary file in the
    repository, the icon is stored as base64 data and materialised on demand.
    """
    root = Path(__file__).resolve().parent.parent
    target = root / "assets" / "empty_project.png"
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    data = base64.b64decode(EMPTY_PROJECT_ICON_BASE64)
    target.write_bytes(data)
