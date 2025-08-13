"""Synonyms lookup service using selected LLM model."""

from __future__ import annotations

from typing import Dict, Tuple

from ..models import get_translator
from ..settings import AppSettings

SYN_PROMPT = (
    "Дай 5-10 вариантов синонимов одного русского слова в данном контексте.\n"
    "Формат: слово;слово;слово... Без лишнего текста."
)

_cache: Dict[Tuple[str, str, str], list[str]] = {}


def fetch_synonyms(word: str, left_ctx: str = "", right_ctx: str = "") -> list[str]:
    """Return synonyms for *word* using LLM with given context.

    Results are cached by the combination of word and surrounding context
    to reduce repeated model calls.
    """

    key = (word, left_ctx, right_ctx)
    if key in _cache:
        return _cache[key]

    settings = AppSettings.load()
    model_name = settings.model or "gemini"
    translator = get_translator(model_name)

    prompt = f"{SYN_PROMPT}\nКонтекст: ...{left_ctx} [ {word} ] {right_ctx}..."
    try:
        response = translator.translate("", prompt)
    except Exception:
        return []

    parts = [p.strip() for p in response.replace("\n", ";").split(";") if p.strip()]
    synonyms = parts[:10]
    _cache[key] = synonyms
    return synonyms
