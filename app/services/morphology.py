"""Simple heuristic-based morphology checker."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List
from PyQt6 import QtGui


@dataclass
class MorphologyError:
    """Represents a detected morphology issue in text."""

    start: int
    length: int
    message: str


class MorphologyService:
    """Service detecting common Russian morphology issues."""

    _pattern = re.compile(r"\b[А-Яа-яёЁ]+(?:тся|ться)\b")

    def analyze(self, text: str) -> List[MorphologyError]:
        """Return list of potential morphology errors in *text*."""
        errors: List[MorphologyError] = []
        for match in self._pattern.finditer(text):
            errors.append(
                MorphologyError(
                    start=match.start(),
                    length=len(match.group(0)),
                    message="Проверьте окончание 'тся/ться'",
                )
            )
        return errors


class MorphologyHighlighter(QtGui.QSyntaxHighlighter):
    """Underline morphology errors using :class:`MorphologyService`."""

    def __init__(self, document: QtGui.QTextDocument, service: MorphologyService) -> None:
        super().__init__(document)
        self._service = service
        self.errors: List[MorphologyError] = []
        self._fmt = QtGui.QTextCharFormat()
        self._fmt.setUnderlineStyle(QtGui.QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
        self._fmt.setUnderlineColor(QtGui.QColor("red"))

    def update_errors(self) -> None:
        """Reanalyse document text and rehighlight."""
        text = self.document().toPlainText()
        self.errors = self._service.analyze(text)
        self.rehighlight()

    # QSyntaxHighlighter API
    def highlightBlock(self, text: str) -> None:  # noqa: N802
        start = self.currentBlock().position()
        end = start + len(text)
        for err in self.errors:
            err_start = err.start
            err_end = err.start + err.length
            if err_start < end and err_end > start:
                left = max(err_start, start)
                right = min(err_end, end)
                self.setFormat(left - start, right - left, self._fmt)
