"""
highlighter.py – Qt syntax highlighter for the raw INI text preview.
"""
from __future__ import annotations

from PyQt6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


class IniHighlighter(QSyntaxHighlighter):
    def highlightBlock(self, text: str) -> None:  # type: ignore[override]
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
            self.setFormat(eq + 1, len(text) - eq - 1, value_fmt)
