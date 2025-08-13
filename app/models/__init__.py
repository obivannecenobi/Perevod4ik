"""Helpers for obtaining translator classes and related utilities."""

from __future__ import annotations

from typing import Any, Dict, Type

from ..settings import AppSettings

from .deepl import DeepLTranslator
from .gemini import GeminiTranslator
from .grok import GrokTranslator
from .qwen import QwenTranslator


TranslatorType = Type[Any]


_MODELS: Dict[str, TranslatorType] = {
    "deepl": DeepLTranslator,
    "gemini": GeminiTranslator,
    "grok": GrokTranslator,
    "qwen": QwenTranslator,
}


def get_translator(name: str, settings: AppSettings | None = None):
    """Return a translator instance for *name* using the appropriate key.

    The lookup is case-insensitive. ``ValueError`` is raised for unknown
    names.
    """

    cls = _MODELS.get(name.lower())
    if not cls:
        raise ValueError(f"Unknown model: {name}")

    settings = settings or AppSettings.load()
    key = getattr(settings, f"{name.lower()}_key", "")
    return cls(api_key=key)


def fetch_synonyms_llm(word: str, model_name: str) -> list[str]:
    """Generate synonyms for *word* using the specified *model_name*.

    If the model cannot be initialised or the request fails, an empty
    list is returned.
    """

    if not model_name:
        return []
    try:
        translator = get_translator(model_name)
    except Exception:
        return []

    prompt = (
        "Provide a comma-separated list of synonyms for the following word."
    )
    try:
        response = translator.translate(word, prompt=prompt)
    except Exception:
        return []
    return [s.strip() for s in response.split(",") if s.strip()]

