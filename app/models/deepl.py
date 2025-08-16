"""Client for interacting with the DeepL translation API."""

from __future__ import annotations

from typing import Dict, Optional
import json
from urllib import error, parse, request

from ..services.http import create_opener
from ..settings import AppSettings


class DeepLTranslator:
    """Simple wrapper around the DeepL HTTP API.

    Parameters
    ----------
    api_key:
        API key for the DeepL service.
    """

    #: Endpoint for the free DeepL API tier. The user may need to change this
    #: to ``api.deepl.com`` for a paid subscription.
    BASE_URL = "https://api-free.deepl.com/v2/translate"

    def __init__(self, api_key: str, *, settings: AppSettings | None = None) -> None:
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("DeepL API key not provided")
        self._opener = create_opener(settings)

    # ------------------------------------------------------------------
    def translate(
        self,
        text: str,
        prompt: str = "",
        glossary: Optional[Dict[str, str]] = None,
        target_lang: str = "EN",
        source_lang: Optional[str] = None,
    ) -> str:
        """Translate *text* using DeepL.

        Parameters
        ----------
        text:
            Source text to translate.
        prompt:
            Ignored by DeepL but kept for API consistency.
        glossary:
            Glossary terms. DeepL's API requires a separate glossary feature,
            which is not implemented here; entries are therefore ignored and
            kept solely for interface compatibility.
        target_lang:
            Target language code (default ``"EN"``).
        source_lang:
            Optional source language code.
        """

        params: Dict[str, str] = {"text": text, "target_lang": target_lang}
        if source_lang:
            params["source_lang"] = source_lang

        data = parse.urlencode(params).encode("utf-8")
        headers = {"Authorization": f"DeepL-Auth-Key {self.api_key}"}
        req = request.Request(self.BASE_URL, data=data, headers=headers)

        try:
            with self._opener.open(req) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:  # pragma: no cover - network/IO safety
            message = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"DeepL API error: {message}") from exc
        except error.URLError as exc:  # pragma: no cover - network/IO safety
            raise RuntimeError(f"DeepL connection error: {exc.reason}") from exc

        try:
            return payload["translations"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError("Unexpected response format from DeepL") from exc

