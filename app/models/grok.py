"""Client for the xAI Grok API."""

from __future__ import annotations

from typing import Dict, Optional
import json
from urllib import error, request

from ..services.http import create_opener
from ..settings import AppSettings


class GrokTranslator:
    """Translate text using xAI's Grok model."""

    BASE_URL = "https://api.x.ai/v1/chat/completions"
    DEFAULT_MODEL = "grok-beta"

    def __init__(
        self, api_key: str, model: str | None = None, *, settings: AppSettings | None = None
    ) -> None:
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("Grok API key not provided")
        self.model = model or self.DEFAULT_MODEL
        self._opener = create_opener(settings)

    # ------------------------------------------------------------------
    def translate(
        self,
        text: str,
        prompt: str = "",
        glossary: Optional[Dict[str, str]] = None,
    ) -> str:
        """Translate *text* using Grok.

        The *prompt* and *glossary* are merged into a system instruction sent
        alongside the user's text. Any network or API related errors are
        propagated as :class:`RuntimeError`.
        """

        system_parts = [prompt] if prompt else []
        if glossary:
            glossary_text = "\n".join(f"{k}: {v}" for k, v in glossary.items())
            system_parts.append("Glossary:\n" + glossary_text)
        system_message = "\n\n".join(system_parts) if system_parts else ""

        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": text},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        req = request.Request(
            self.BASE_URL, data=json.dumps(body).encode("utf-8"), headers=headers
        )

        try:
            with self._opener.open(req) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:  # pragma: no cover - network/IO safety
            message = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Grok API error: {message}") from exc
        except error.URLError as exc:  # pragma: no cover - network/IO safety
            raise RuntimeError(f"Grok connection error: {exc.reason}") from exc

        try:
            return payload["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as exc:
            raise RuntimeError("Unexpected response format from Grok") from exc

