"""Client for the Google Gemini API."""

from __future__ import annotations

from typing import Dict, Optional
import json
from urllib import error, request

from settings import AppSettings


class GeminiTranslator:
    """Translate text using Google's Gemini models."""

    BASE_URL = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-pro:generateContent"
    )

    def __init__(self, api_key: Optional[str] = None) -> None:
        settings = AppSettings.load()
        self.api_key = api_key or settings.api_key
        if not self.api_key:
            raise ValueError("Gemini API key not found in settings")

    # ------------------------------------------------------------------
    def translate(
        self,
        text: str,
        prompt: str = "",
        glossary: Optional[Dict[str, str]] = None,
    ) -> str:
        """Translate *text* using Gemini.

        The method sends a single prompt containing the optional *prompt*,
        formatted *glossary* terms and the *text* itself. Errors from the
        underlying HTTP API are re-raised as :class:`RuntimeError`.
        """

        parts = []
        if prompt:
            parts.append(prompt)
        if glossary:
            glossary_text = "\n".join(f"{k}: {v}" for k, v in glossary.items())
            parts.append("Glossary:\n" + glossary_text)
        parts.append(text)
        full_prompt = "\n\n".join(parts)

        body = {"contents": [{"parts": [{"text": full_prompt}]}]}
        url = f"{self.BASE_URL}?key={self.api_key}"
        req = request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        try:
            with request.urlopen(req) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:  # pragma: no cover - network/IO safety
            message = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Gemini API error: {message}") from exc
        except error.URLError as exc:  # pragma: no cover - network/IO safety
            raise RuntimeError(f"Gemini connection error: {exc.reason}") from exc

        try:
            return payload["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError("Unexpected response format from Gemini") from exc

