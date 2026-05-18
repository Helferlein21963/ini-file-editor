"""Modal dialogs used by the INI Editor.

Provides :class:`EntryEditDialog` and :class:`SectionEditDialog` for editing
key-value pairs and section metadata, and :class:`DiffSelectDialog` for
picking two open documents to compare.
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
    """Modal dialog for editing one :class:`~ini_parser.IniEntry`.

    Call :meth:`apply_to_entry` after :meth:`exec` returns ``Accepted`` to
    write the user input back into the entry. The entry is not mutated
    automatically.
    """

    def __init__(self, entry: IniEntry, language: Language, parent: Optional[QWidget] = None) -> None:
        """Pre-fill the form with the values from ``entry``."""
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
        self._comments_edit.setMinimumHeight(100)

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
        """Write the form values back into the wrapped entry."""
        self._entry.key = self._key_edit.text().strip()
        self._entry.value = self._value_edit.text()
        self._entry.inline_comment = self._inline_edit.text().strip()
        raw = self._comments_edit.toPlainText()
        self._entry.preceding_comments = raw.splitlines() if raw.strip() else []


class SectionEditDialog(QDialog):
    """Modal dialog for editing one :class:`~ini_parser.IniSection`.

    Call :meth:`apply_to_section` after :meth:`exec` returns ``Accepted`` to
    write the form values back into the section.
    """

    def __init__(self, section: IniSection, language: Language, parent: Optional[QWidget] = None) -> None:
        """Pre-fill the form with the values from ``section``."""
        super().__init__(parent)
        self._language = language
        self.setWindowTitle(translate(language, "section_edit_title"))
        self.setMinimumWidth(480)
        self._section = section

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._name_edit = QLineEdit(section.name)
        self._pre_edit = QPlainTextEdit("\n".join(section.preceding_comments))
        self._pre_edit.setMinimumHeight(90)
        self._trail_edit = QPlainTextEdit("\n".join(section.trailing_comments))
        self._trail_edit.setMinimumHeight(90)

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
        """Write the form values back into the wrapped section."""
        self._section.name = self._name_edit.text().strip()
        raw_pre = self._pre_edit.toPlainText()
        self._section.preceding_comments = raw_pre.splitlines() if raw_pre.strip() else []
        raw_trail = self._trail_edit.toPlainText()
        self._section.trailing_comments = raw_trail.splitlines() if raw_trail.strip() else []


class DiffSelectDialog(QDialog):
    """Lets the user pick two open documents for side-by-side comparison."""

    def __init__(
        self,
        tabs: list[tuple[str, "DocumentTab"]],
        language: Language,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Populate two combo boxes with the given tabs.

        Args:
            tabs: Pairs of ``(display_label, DocumentTab)``. At least two
                entries are expected; the second is pre-selected as B.
            language: Initial UI language.
            parent: Optional Qt parent.
        """
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
        """Return the currently selected ``(tab_a, tab_b)`` pair."""
        return self._combo_a.currentData(), self._combo_b.currentData()
