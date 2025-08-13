"""Utilities for working with project files.

This module provides helpers for traversing directories and for loading
or saving text in the DOCX format without third‑party dependencies. The
DOCX support implemented here is intentionally minimal – it extracts and
writes plain paragraphs only. It is sufficient for simple translation
workflows used in tests and examples.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET
import zipfile

# ---------------------------------------------------------------------------
# Directory traversal

def iter_docx_files(folder: Path | str) -> Iterable[Path]:
    """Yield all ``.docx`` files under *folder* recursively."""

    root = Path(folder)
    yield from root.rglob("*.docx")


# ---------------------------------------------------------------------------
# DOCX handling

_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="R1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""


def load_docx(path: Path | str) -> str:
    """Return plain text extracted from a DOCX file."""

    file_path = Path(path)
    with zipfile.ZipFile(file_path) as zf:
        with zf.open("word/document.xml") as doc:
            tree = ET.parse(doc)

    root = tree.getroot()
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for para in root.findall(".//w:p", ns):
        parts = [node.text for node in para.findall(".//w:t", ns) if node.text]
        paragraphs.append("".join(parts))
    return "\n".join(paragraphs)


def save_docx(text: str, path: Path | str) -> None:
    """Save *text* to *path* as a minimal DOCX document."""

    file_path = Path(path)
    document_xml = _build_document_xml(text)
    with zipfile.ZipFile(file_path, "w") as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES)
        zf.writestr("_rels/.rels", _RELS)
        zf.writestr("word/document.xml", document_xml)


def _build_document_xml(text: str) -> str:
    ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    ET.register_namespace("w", ns)
    root = ET.Element(f"{{{ns}}}document")
    body = ET.SubElement(root, f"{{{ns}}}body")
    for paragraph in text.splitlines():
        p = ET.SubElement(body, f"{{{ns}}}p")
        r = ET.SubElement(p, f"{{{ns}}}r")
        t = ET.SubElement(r, f"{{{ns}}}t")
        t.text = paragraph
    ET.SubElement(body, f"{{{ns}}}sectPr")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")
