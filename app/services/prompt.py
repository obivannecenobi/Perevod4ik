"""Prompt generation helpers."""

from __future__ import annotations

from .glossary import Glossary


def build_prompt(
    text: str,
    glossaries: list[Glossary] | None = None,
    instruction: str | None = None,
) -> str:
    """Create a prompt string using *text* and optional *glossaries*.

    Parameters
    ----------
    text:
        Main text to include in the prompt.
    glossaries:
        Optional list of :class:`~app.services.glossary.Glossary` instances.
        Only glossaries with ``auto_to_prompt=True`` and at least one entry
        are appended to the prompt.
    instruction:
        Additional instruction placed at the beginning of the prompt.
    """

    parts: list[str] = []
    if instruction:
        parts.append(instruction.strip())
    parts.append(text.strip())
    if glossaries:
        glossary_lines = [
            f"{src} -> {dst}"
            for g in glossaries
            if g.auto_to_prompt
            for src, dst in g.entries.items()
        ]
        if glossary_lines:
            parts.append("Glossary:\n" + "\n".join(glossary_lines))
    return "\n\n".join(part for part in parts if part)
