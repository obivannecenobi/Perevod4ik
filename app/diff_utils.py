"""Utilities for diff highlighting in text edits."""
from __future__ import annotations

import difflib
from PyQt6 import QtGui


class DiffHighlighter(QtGui.QSyntaxHighlighter):
    """Highlight differences from a baseline text."""

    def __init__(self, document: QtGui.QTextDocument, base: str = "") -> None:
        super().__init__(document)
        self._base = base
        self._diff_ranges: list[tuple[int, int]] = []
        self._fmt = QtGui.QTextCharFormat()
        # Using a subtle yellow background for changed text
        self._fmt.setBackground(QtGui.QColor(255, 255, 0, 128))

    def set_base(self, text: str) -> None:
        """Set baseline *text* for future comparisons."""
        self._base = text
        self.update_diff()

    def update_diff(self) -> None:
        """Recompute ranges of changed text and rehighlight."""
        if not self._base:
            self._diff_ranges = []
            self.rehighlight()
            return
        current = self.document().toPlainText()
        matcher = difflib.SequenceMatcher(a=self._base, b=current)
        self._diff_ranges = [
            (j1, j2) for tag, _i1, _i2, j1, j2 in matcher.get_opcodes() if tag != "equal"
        ]
        self.rehighlight()

    # QSyntaxHighlighter API
    def highlightBlock(self, text: str) -> None:  # noqa: N802 (Qt API)
        start = self.currentBlock().position()
        end = start + len(text)
        for s, e in self._diff_ranges:
            if s < end and e > start:
                left = max(s, start)
                right = min(e, end)
                self.setFormat(left - start, right - left, self._fmt)
