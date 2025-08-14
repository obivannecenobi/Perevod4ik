"""Client for the Google Gemini API."""

from __future__ import annotations

from typing import Dict, Optional
import json
import re
from pathlib import Path
from urllib import error, request


MODELS_URL = "https://generativelanguage.googleapis.com/v1/models"
_CACHE_FILE = Path(__file__).with_name("_gemini_models_cache.json")
_MODEL_CACHE: Dict[str, str] = {}


def fetch_latest_model(api_key: str, kind: str = "flash") -> str:
    """Return the newest Gemini model name for *kind*.

    Results are cached on disk to avoid repeated network requests.
    """

    if kind in _MODEL_CACHE:
        return _MODEL_CACHE[kind]

    if _CACHE_FILE.exists():
        try:
            _MODEL_CACHE.update(json.loads(_CACHE_FILE.read_text()))
            if kind in _MODEL_CACHE:
                return _MODEL_CACHE[kind]
        except Exception:
            _MODEL_CACHE.clear()

    url = f"{MODELS_URL}?key={api_key}"
    req = request.Request(url)

    try:
        with request.urlopen(req) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:  # pragma: no cover - network/IO safety
        message = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Gemini API error: {message}") from exc
    except error.URLError as exc:  # pragma: no cover - network/IO safety
        raise RuntimeError(f"Gemini connection error: {exc.reason}") from exc

    names = []
    for info in payload.get("models", []):
        name = info.get("name", "")
        if f"gemini-{kind}-" in name:
            names.append(name.split("/")[-1])

    if not names:
        raise RuntimeError(f"No Gemini models found for kind '{kind}'")

    def version_key(model_name: str) -> float:
        if model_name.endswith("-latest"):
            return float("inf")
        match = re.search(r"-v(\d+)$", model_name)
        return float(match.group(1)) if match else 0.0

    latest = max(names, key=version_key)
    _MODEL_CACHE[kind] = latest

    try:
        _CACHE_FILE.write_text(json.dumps(_MODEL_CACHE))
    except OSError:  # pragma: no cover - file system safety
        pass

    return latest

class GeminiTranslator:
    """Translate text using Google's Gemini models."""

    def __init__(
        self, api_key: str, model: str | None = None, *, kind: str = "flash"
    ) -> None:
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("Gemini API key not provided")
        self.model = model or fetch_latest_model(api_key, kind=kind)

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
        url = (
            f"{MODELS_URL}/{self.model}:generateContent?key={self.api_key}"
        )
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

