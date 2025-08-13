"""Prompt generation helpers."""

from __future__ import annotations

from .glossary import Glossary


def build_prompt(text: str, glossary: Glossary | None = None, instruction: str | None = None) -> str:
    """Create a prompt string using *text* and optional *glossary*.

    Parameters
    ----------
    text:
        Main text to include in the prompt.
    glossary:
        Optional :class:`~app.services.glossary.Glossary` whose entries will
        be appended to the prompt.
    instruction:
        Additional instruction placed at the beginning of the prompt.
    """

    parts: list[str] = []
    if instruction:
        parts.append(instruction.strip())
    parts.append(text.strip())
    if glossary and glossary.entries:
        glossary_lines = "\n".join(f"{src} -> {dst}" for src, dst in glossary.entries.items())
        parts.append("Glossary:\n" + glossary_lines)
    return "\n\n".join(part for part in parts if part)
