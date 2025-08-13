"""Client for the Qwen (Alibaba Cloud) API."""

from __future__ import annotations

from typing import Dict, Optional
import json
from urllib import error, request

from settings import AppSettings


class QwenTranslator:
    """Translate text using the Qwen model."""

    BASE_URL = "https://api.qwen.ai/v1/chat/completions"
    DEFAULT_MODEL = "qwen-turbo"

    def __init__(self, api_key: Optional[str] = None, model: str | None = None) -> None:
        settings = AppSettings.load()
        self.api_key = api_key or settings.api_key
        if not self.api_key:
            raise ValueError("Qwen API key not found in settings")
        self.model = model or self.DEFAULT_MODEL

    # ------------------------------------------------------------------
    def translate(
        self,
        text: str,
        prompt: str = "",
        glossary: Optional[Dict[str, str]] = None,
    ) -> str:
        """Translate *text* using Qwen.

        ``prompt`` and ``glossary`` are combined into the system message.
        Network or API related errors are raised as :class:`RuntimeError`.
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
            with request.urlopen(req) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:  # pragma: no cover - network/IO safety
            message = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Qwen API error: {message}") from exc
        except error.URLError as exc:  # pragma: no cover - network/IO safety
            raise RuntimeError(f"Qwen connection error: {exc.reason}") from exc

        try:
            return payload["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as exc:
            raise RuntimeError("Unexpected response format from Qwen") from exc

