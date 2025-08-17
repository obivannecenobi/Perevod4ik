"""Client for the Google Gemini API."""

from __future__ import annotations

from typing import Dict, Optional, TYPE_CHECKING
import json
import re
from pathlib import Path
import requests
from ..services.http import create_session

if TYPE_CHECKING:
    from ..settings import AppSettings


MODELS_URL = "https://generativelanguage.googleapis.com/v1/models"
_CACHE_FILE = Path(__file__).with_name("_gemini_models_cache.json")
_MODEL_CACHE: Dict[str, str] = {}


def fetch_latest_model(api_key: str, kind: str = "flash", session: requests.Session | None = None) -> str:
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
    session = session or create_session()
    try:
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
    except requests.HTTPError as exc:  # pragma: no cover - network/IO safety
        message = exc.response.text if exc.response else str(exc)
        raise RuntimeError(f"Gemini API error: {message}") from exc
    except requests.RequestException as exc:  # pragma: no cover - network/IO safety
        raise RuntimeError(f"Gemini connection error: {exc}") from exc

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


def _verify_model(
    api_key: str, model: str, session: requests.Session | None = None
) -> bool:
    """Return ``True`` if *model* exists for the provided *api_key*.

    The check is performed by listing available models via the public
    ``ListModels`` endpoint. Any network or API error results in ``False``
    being returned so callers can handle verification failure uniformly.
    """

    url = f"{MODELS_URL}?key={api_key}"
    session = session or create_session()
    try:
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException:  # pragma: no cover - network/IO safety
        return False

    for info in payload.get("models", []):
        name = info.get("name", "").split("/")[-1]
        if name == model:
            return True
    return False

class GeminiTranslator:
    """Translate text using Google's Gemini models."""

    def __init__(
        self, api_key: str, model: str | None = None, *, kind: str = "flash",
        settings: AppSettings | None = None, session: requests.Session | None = None,
    ) -> None:
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("Gemini API key not provided")
        self.session = session or create_session(settings)
        self.model = model or fetch_latest_model(api_key, kind=kind, session=self.session)

        if not _verify_model(api_key, self.model, session=self.session):
            _MODEL_CACHE.clear()
            try:
                _CACHE_FILE.unlink()
            except OSError:  # pragma: no cover - file system safety
                pass
            if model is None:
                self.model = fetch_latest_model(api_key, kind=kind, session=self.session)
                if _verify_model(api_key, self.model, session=self.session):
                    return
            raise RuntimeError(
                "Selected Gemini model is unavailable. Please update your API key or region settings."
            )

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
        url = f"{MODELS_URL}/{self.model}:generateContent?key={self.api_key}"
        try:
            resp = self.session.post(url, json=body, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
        except requests.HTTPError as exc:  # pragma: no cover - network/IO safety
            message = exc.response.text if exc.response else str(exc)
            raise RuntimeError(f"Gemini API error: {message}") from exc
        except requests.RequestException as exc:  # pragma: no cover - network/IO safety
            raise RuntimeError(f"Gemini connection error: {exc}") from exc

        error_info = payload.get("error")
        if error_info:
            status = error_info.get("status")
            message = error_info.get("message", "")
            if status == "FAILED_PRECONDITION" and "User location is not supported" in message:
                raise RuntimeError("Gemini service not available in your region. Enable a proxy or use a supported region.")
            raise RuntimeError(f"Gemini API error: {message}")

        try:
            return payload["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError("Unexpected response format from Gemini") from exc

