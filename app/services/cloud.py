"""Utilities for interacting with Google Docs.

This module provides a thin wrapper around the Google Docs and Drive
APIs.  The functions handle authorisation, listing documents inside a
folder and reading or writing their textual content.

The implementation intentionally keeps dependencies optional.  If the
`google-api-python-client` package is not installed, the functions will
raise a :class:`RuntimeError` when used.  This allows the rest of the
application to operate in environments without the Google libraries
while still offering cloud functionality when available.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple
import json

try:  # pragma: no cover - optional dependency
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except Exception:  # pragma: no cover - library not installed
    Credentials = None  # type: ignore
    build = None  # type: ignore

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
]


def _ensure_client() -> None:
    if Credentials is None or build is None:
        raise RuntimeError("Google API client libraries are required for cloud operations")


def _load_credentials(token: str) -> "Credentials":
    """Create :class:`Credentials` from a path or JSON string."""

    _ensure_client()
    token_path = Path(token)
    if token_path.exists():
        return Credentials.from_authorized_user_file(str(token_path), SCOPES)  # type: ignore[arg-type]
    info = json.loads(token)
    return Credentials.from_authorized_user_info(info, SCOPES)  # type: ignore[arg-type]


def _build_services(token: str):
    creds = _load_credentials(token)
    docs = build("docs", "v1", credentials=creds)
    drive = build("drive", "v3", credentials=creds)
    return docs, drive


def list_documents(token: str, folder_id: str) -> List[Tuple[str, str]]:
    """Return a list of ``(id, name)`` for Google Docs in *folder_id*."""

    docs_service, drive_service = _build_services(token)
    query = (
        f"'{folder_id}' in parents and "
        "mimeType='application/vnd.google-apps.document' and trashed=false"
    )
    response = (
        drive_service.files()
        .list(q=query, fields="files(id, name)")
        .execute()
    )
    files = response.get("files", [])
    return [(item["id"], item["name"]) for item in files]


def load_document(token: str, doc_id: str) -> str:
    """Return the plain text content of the Google Doc with *doc_id*."""

    docs_service, _ = _build_services(token)
    document = docs_service.documents().get(documentId=doc_id).execute()
    body = document.get("body", {})
    content: List[str] = []
    for value in body.get("content", []):
        para = value.get("paragraph")
        if not para:
            continue
        elements = para.get("elements", [])
        parts = [elem.get("textRun", {}).get("content", "") for elem in elements]
        content.append("".join(parts))
    return "".join(content)


def save_document(token: str, doc_id: str, text: str) -> None:
    """Replace the entire content of the Google Doc with *text*."""

    docs_service, _ = _build_services(token)
    document = docs_service.documents().get(documentId=doc_id).execute()
    end = 1
    content = document.get("body", {}).get("content", [])
    if content:
        end = content[-1].get("endIndex", 1)
    requests = [
        {"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end}}},
        {"insertText": {"location": {"index": 1}, "text": text}},
    ]
    docs_service.documents().batchUpdate(
        documentId=doc_id, body={"requests": requests}
    ).execute()
