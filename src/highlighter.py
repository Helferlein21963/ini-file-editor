"""Syntax highlighter for the INI preview pane.

Colours comments, section headers, keys, and values inline using a fixed
VS-Code-inspired palette. Designed to be cheap: classification is single-pass
per line with no regex.
"""
from __future__ import annotations

import re

from PyQt6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


_INLINE_COMMENT_RE = re.compile(r"\s{2,}[;#]")


class IniHighlighter(QSyntaxHighlighter):
    """Qt syntax highlighter for INI text.

    Attach to a :class:`QTextDocument` once; Qt invokes
    :meth:`highlightBlock` for each visible line.
    """

    def highlightBlock(self, text: str) -> None:  # type: ignore[override]
        """Classify and colour a single line of text."""
        stripped = text.strip()

        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#6A9955"))
        comment_fmt.setFontItalic(True)

        section_fmt = QTextCharFormat()
        section_fmt.setForeground(QColor("#569CD6"))
        section_fmt.setFontWeight(QFont.Weight.Bold)

        key_fmt = QTextCharFormat()
        key_fmt.setForeground(QColor("#9CDCFE"))

        value_fmt = QTextCharFormat()
        value_fmt.setForeground(QColor("#CE9178"))

        if stripped.startswith(";") or stripped.startswith("#"):
            self.setFormat(0, len(text), comment_fmt)
        elif stripped.startswith("[") and "]" in stripped:
            self.setFormat(0, len(text), section_fmt)
        elif "=" in text:
            eq = text.index("=")
            self.setFormat(0, eq, key_fmt)
            value_start = eq + 1
            inline_match = _INLINE_COMMENT_RE.search(text, value_start)
            if inline_match:
                self.setFormat(value_start, inline_match.start() - value_start, value_fmt)
                self.setFormat(inline_match.start(), len(text) - inline_match.start(), comment_fmt)
            else:
                self.setFormat(value_start, len(text) - value_start, value_fmt)
