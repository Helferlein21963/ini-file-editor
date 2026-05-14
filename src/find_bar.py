"""Embedded find/replace bar shown at the bottom of the main window.

The bar emits signals for each user action; the host (typically
:class:`~main_window.MainWindow`) performs the actual search/replace on the
target widget so the same bar can drive different panes.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QWidget,
)

try:
    from src.translations import Language, translate
except ModuleNotFoundError:
    from translations import Language, translate  # type: ignore[no-redef]


class FindBar(QWidget):
    """Inline find/replace bar.

    Hidden by default. Call :meth:`show_find` or :meth:`show_replace` to
    reveal it. The host wires up the four signals to its own search logic.

    Signals:
        find_next_requested: User pressed Enter, the Next button, or
            otherwise asked for the next forward match.
        find_prev_requested: User asked for the previous match.
        replace_requested: User pressed the Replace button to replace the
            current selection if it matches.
        replace_all_requested: User pressed the Replace-All button.
    """

    find_next_requested = pyqtSignal()
    find_prev_requested = pyqtSignal()
    replace_requested = pyqtSignal()
    replace_all_requested = pyqtSignal()

    def __init__(self, language: Language, parent: Optional[QWidget] = None) -> None:
        """Build the bar in hidden state."""
        super().__init__(parent)
        self.setVisible(False)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 3, 6, 3)
        outer.setSpacing(2)

        find_row = QHBoxLayout()
        find_row.setSpacing(4)

        self._search_label = QLabel(translate(language, "find_label"))
        self._search_edit = QLineEdit()
        self._search_edit.setMinimumWidth(200)
        self._search_edit.returnPressed.connect(self.find_next_requested)

        _emoji_font = QFont()
        _emoji_font.setPointSize(15)

        self._prev_btn = QPushButton("◀")
        self._prev_btn.setFont(_emoji_font)
        self._prev_btn.setFixedSize(38, 28)
        self._prev_btn.clicked.connect(self.find_prev_requested)

        self._next_btn = QPushButton("▶")
        self._next_btn.setFont(_emoji_font)
        self._next_btn.setFixedSize(38, 28)
        self._next_btn.clicked.connect(self.find_next_requested)

        self._case_check = QCheckBox(translate(language, "find_case_sensitive"))
        self._whole_words_check = QCheckBox(translate(language, "find_whole_words"))

        self._status_label = QLabel("")
        self._status_label.setMinimumWidth(160)

        self._close_btn = QPushButton("✖")
        self._close_btn.setFont(_emoji_font)
        self._close_btn.setFixedSize(38, 28)
        self._close_btn.clicked.connect(self.hide)

        find_row.addWidget(self._search_label)
        find_row.addWidget(self._search_edit)
        find_row.addWidget(self._prev_btn)
        find_row.addWidget(self._next_btn)
        find_row.addSpacing(8)
        find_row.addWidget(self._case_check)
        find_row.addWidget(self._whole_words_check)
        find_row.addSpacing(8)
        find_row.addWidget(self._status_label, 1)
        find_row.addWidget(self._close_btn)
        outer.addLayout(find_row)

        self._replace_widget = QWidget()
        replace_row = QHBoxLayout(self._replace_widget)
        replace_row.setContentsMargins(0, 0, 0, 0)
        replace_row.setSpacing(4)

        self._replace_label = QLabel(translate(language, "find_replace_label"))
        self._replace_edit = QLineEdit()
        self._replace_edit.setMinimumWidth(200)
        self._replace_edit.returnPressed.connect(self.replace_requested)

        self._replace_btn = QPushButton(translate(language, "find_replace_one"))
        self._replace_btn.clicked.connect(self.replace_requested)
        self._replace_all_btn = QPushButton(translate(language, "find_replace_all"))
        self._replace_all_btn.clicked.connect(self.replace_all_requested)

        replace_row.addWidget(self._replace_label)
        replace_row.addWidget(self._replace_edit)
        replace_row.addWidget(self._replace_btn)
        replace_row.addWidget(self._replace_all_btn)
        replace_row.addStretch()
        outer.addWidget(self._replace_widget)

        self._replace_widget.setVisible(False)

    def show_find(self) -> None:
        """Reveal the bar in find-only mode and focus the search field."""
        self._replace_widget.setVisible(False)
        self.setVisible(True)
        self._search_edit.setFocus()
        self._search_edit.selectAll()

    def show_replace(self) -> None:
        """Reveal the bar in find-and-replace mode and focus the search field."""
        self._replace_widget.setVisible(True)
        self.setVisible(True)
        self._search_edit.setFocus()
        self._search_edit.selectAll()

    def is_replace_mode(self) -> bool:
        return self._replace_widget.isVisible()

    def get_search_text(self) -> str:
        return self._search_edit.text()

    def get_replace_text(self) -> str:
        return self._replace_edit.text()

    def is_case_sensitive(self) -> bool:
        return self._case_check.isChecked()

    def is_whole_words(self) -> bool:
        return self._whole_words_check.isChecked()

    def set_status(self, message: str) -> None:
        self._status_label.setText(message)

    def set_language(self, language: Language) -> None:
        self._search_label.setText(translate(language, "find_label"))
        self._prev_btn.setToolTip(translate(language, "find_prev"))
        self._next_btn.setToolTip(translate(language, "find_next"))
        self._case_check.setText(translate(language, "find_case_sensitive"))
        self._whole_words_check.setText(translate(language, "find_whole_words"))
        self._replace_label.setText(translate(language, "find_replace_label"))
        self._replace_btn.setText(translate(language, "find_replace_one"))
        self._replace_all_btn.setText(translate(language, "find_replace_all"))

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        super().keyPressEvent(event)
