"""Simple report generation utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
import csv
from html import escape


def save_csv(stats: Iterable[dict], path: Path | str) -> None:
    """Save *stats* to *path* in CSV format."""

    file_path = Path(path)
    with file_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["chapter", "characters", "time"])
        writer.writeheader()
        writer.writerows(stats)


def save_html(stats: Iterable[dict], path: Path | str) -> None:
    """Save *stats* to *path* as a minimal HTML table."""

    rows = "".join(
        f"<tr><td>{escape(str(s.get('chapter', '')))}</td><td>{s.get('characters', '')}</td><td>{s.get('time', '')}</td></tr>"
        for s in stats
    )
    table = (
        "<table>"
        "<tr><th>chapter</th><th>characters</th><th>time</th></tr>"
        f"{rows}"
        "</table>"
    )
    file_path = Path(path)
    with file_path.open("w", encoding="utf-8") as fh:
        fh.write("<html><body>" + table + "</body></html>")
