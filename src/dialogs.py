"""
dialogs.py – Modal dialogs used by the INI Editor (entry/section edit, diff selection).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
    QPlainTextEdit, QVBoxLayout, QWidget,
)

try:
    from src.ini_parser import IniEntry, IniSection
except ModuleNotFoundError:
    from ini_parser import IniEntry, IniSection  # type: ignore[no-redef]

try:
    from src.translations import Language, translate
except ModuleNotFoundError:
    from translations import Language, translate  # type: ignore[no-redef]

if TYPE_CHECKING:
    from .document_tab import DocumentTab


class EntryEditDialog(QDialog):
    def __init__(self, entry: IniEntry, language: Language, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._language = language
        self.setWindowTitle(translate(language, "entry_edit_title"))
        self.setMinimumWidth(480)
        self._entry = entry

        layout = QVBoxLayout(self)

        form = QFormLayout()
        self._key_edit = QLineEdit(entry.key)
        self._value_edit = QLineEdit(entry.value)
        self._inline_edit = QLineEdit(entry.inline_comment)
        self._comments_edit = QPlainTextEdit("\n".join(entry.preceding_comments))
        self._comments_edit.setMaximumHeight(100)

        form.addRow(translate(language, "entry_key"), self._key_edit)
        form.addRow(translate(language, "entry_value"), self._value_edit)
        form.addRow(translate(language, "entry_inline"), self._inline_edit)
        form.addRow(translate(language, "entry_preceding"), self._comments_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def apply_to_entry(self) -> None:
        self._entry.key = self._key_edit.text().strip()
        self._entry.value = self._value_edit.text()
        self._entry.inline_comment = self._inline_edit.text().strip()
        raw = self._comments_edit.toPlainText()
        self._entry.preceding_comments = raw.splitlines() if raw.strip() else []


class SectionEditDialog(QDialog):
    def __init__(self, section: IniSection, language: Language, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._language = language
        self.setWindowTitle(translate(language, "section_edit_title"))
        self.setMinimumWidth(480)
        self._section = section

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._name_edit = QLineEdit(section.name)
        self._pre_edit = QPlainTextEdit("\n".join(section.preceding_comments))
        self._pre_edit.setMaximumHeight(90)
        self._trail_edit = QPlainTextEdit("\n".join(section.trailing_comments))
        self._trail_edit.setMaximumHeight(90)

        form.addRow(translate(language, "section_name"), self._name_edit)
        form.addRow(translate(language, "section_pre_comments"), self._pre_edit)
        form.addRow(translate(language, "section_post_comments"), self._trail_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def apply_to_section(self) -> None:
        self._section.name = self._name_edit.text().strip()
        raw_pre = self._pre_edit.toPlainText()
        self._section.preceding_comments = raw_pre.splitlines() if raw_pre.strip() else []
        raw_trail = self._trail_edit.toPlainText()
        self._section.trailing_comments = raw_trail.splitlines() if raw_trail.strip() else []


class DiffSelectDialog(QDialog):
    def __init__(
        self,
        tabs: list[tuple[str, "DocumentTab"]],
        language: Language,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(translate(language, "diff_select_title"))
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._combo_a = QComboBox()
        self._combo_b = QComboBox()
        for label, tab in tabs:
            self._combo_a.addItem(label, tab)
            self._combo_b.addItem(label, tab)
        if len(tabs) >= 2:
            self._combo_b.setCurrentIndex(1)

        form.addRow(translate(language, "diff_select_a"), self._combo_a)
        form.addRow(translate(language, "diff_select_b"), self._combo_b)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_tabs(self) -> tuple["DocumentTab", "DocumentTab"]:
        return self._combo_a.currentData(), self._combo_b.currentData()
