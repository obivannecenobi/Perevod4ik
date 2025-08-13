"""Helpers for obtaining translator classes."""

from __future__ import annotations

from typing import Any, Dict, Type

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


def get_translator(name: str):
    """Return a translator instance for *name*.

    The lookup is case-insensitive. ``ValueError`` is raised for unknown
    names.
    """

    cls = _MODELS.get(name.lower())
    if not cls:
        raise ValueError(f"Unknown model: {name}")
    return cls()

