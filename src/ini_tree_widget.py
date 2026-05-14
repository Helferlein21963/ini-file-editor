"""Hierarchical tree widget showing sections and their entries.

Top-level items are sections; child items are the section's entries.
Double-clicking an item opens the corresponding edit dialog; the context
menu adds, edits, and deletes sections and entries. All mutations emit
:attr:`IniTreeWidget.about_to_change` (so the host can snapshot for undo)
followed by :attr:`IniTreeWidget.document_changed`.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView, QDialog, QHeaderView, QMenu, QMessageBox,
    QTreeWidget, QTreeWidgetItem, QWidget,
)

try:
    from src.ini_parser import IniDocument, IniEntry, IniSection, SortMode
except ModuleNotFoundError:
    from ini_parser import IniDocument, IniEntry, IniSection, SortMode  # type: ignore[no-redef]

try:
    from src.translations import Language, translate
except ModuleNotFoundError:
    from translations import Language, translate  # type: ignore[no-redef]

try:
    from src.dialogs import EntryEditDialog, SectionEditDialog
except ModuleNotFoundError:
    from dialogs import EntryEditDialog, SectionEditDialog  # type: ignore[no-redef]


class IniTreeWidget(QTreeWidget):
    """Tree view of the loaded :class:`~ini_parser.IniDocument`.

    Signals:
        document_changed: Emitted after the document was mutated by any tree
            action (edit, add, delete).
        about_to_change: Emitted *before* a mutation is applied. The hosting
            :class:`~document_tab.DocumentTab` connects this to
            :meth:`~document_tab.DocumentTab.push_undo_state`.
    """

    document_changed = pyqtSignal()
    about_to_change = pyqtSignal()

    def __init__(self, language: Language, parent: Optional[QWidget] = None) -> None:
        """Build the widget. Pass ``language`` for initial header labels."""
        super().__init__(parent)
        self._language = language
        self.setColumnCount(3)
        self._refresh_header_labels()
        self.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.itemDoubleClicked.connect(self._on_double_click)
        self._doc: Optional[IniDocument] = None
        self._sort_mode = SortMode.NONE

    def set_language(self, language: Language) -> None:
        self._language = language
        self._refresh_header_labels()

    def _t(self, key: str, **kwargs: object) -> str:
        return translate(self._language, key, **kwargs)

    def _refresh_header_labels(self) -> None:
        self.setHeaderLabels([
            self._t("tree_header_section"),
            self._t("tree_header_value"),
            self._t("tree_header_comment"),
        ])

    def load_document(self, doc: IniDocument) -> None:
        """Replace the visualised document and rebuild the tree.

        Args:
            doc: Document to display. The tree keeps a reference, so later
                mutations through tree actions modify ``doc`` in place.
        """
        self._doc = doc
        self._refresh()

    def set_sort_mode(self, mode: SortMode) -> None:
        """Apply a display-only sort mode and rebuild the tree.

        The underlying document is **not** mutated; sorting is purely visual.
        """
        self._sort_mode = mode
        self._refresh()

    def _refresh(self) -> None:
        self.clear()
        if self._doc is None:
            return
        sections = list(self._doc.sections)
        if self._sort_mode in (SortMode.SECTIONS_ALPHA, SortMode.SECTIONS_AND_KEYS_ALPHA):
            sections = sorted(sections, key=lambda s: s.name.lower())
        for sec in sections:
            sec_item = QTreeWidgetItem(self)
            self._style_section_item(sec_item, sec)
            entries = list(sec.entries)
            if self._sort_mode in (SortMode.KEYS_ALPHA, SortMode.SECTIONS_AND_KEYS_ALPHA):
                entries = sorted(entries, key=lambda e: e.key.lower())
            for entry in entries:
                entry_item = QTreeWidgetItem(sec_item)
                self._style_entry_item(entry_item, entry)
            sec_item.setExpanded(True)

    def _style_section_item(self, item: QTreeWidgetItem, sec: IniSection) -> None:
        item.setText(0, f"[{sec.name}]")
        item.setText(1, "")
        comment_text = " | ".join(c for c in sec.preceding_comments if c.strip())
        item.setText(2, comment_text)
        font = QFont()
        font.setBold(True)
        item.setFont(0, font)
        item.setForeground(0, QColor("#569CD6"))
        item.setData(0, Qt.ItemDataRole.UserRole, sec)

    def _style_entry_item(self, item: QTreeWidgetItem, entry: IniEntry) -> None:
        item.setText(0, entry.key)
        item.setText(1, entry.value)
        item.setText(2, entry.inline_comment)
        item.setForeground(1, self._value_color(entry.value))
        item.setData(0, Qt.ItemDataRole.UserRole, entry)

    def _value_color(self, value: str) -> QColor:
        raw = value.strip()
        normalized = raw.lower()
        if normalized in {"false", "0"}:
            return QColor("#FF4B4B")
        if normalized in {"true", "1"}:
            return QColor("#6CCC70")
        try:
            int(raw)
        except ValueError:
            pass
        else:
            return QColor("#4DD0E1")
        try:
            float(raw)
        except ValueError:
            pass
        else:
            return QColor("#B468C7")
        return QColor("#D4840A")

    def _on_double_click(self, item: QTreeWidgetItem, _col: int) -> None:
        obj = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(obj, IniSection):
            self._edit_section(item, obj)
        elif isinstance(obj, IniEntry):
            self._edit_entry(item, obj)

    def _context_menu(self, pos) -> None:
        item = self.itemAt(pos)
        menu = QMenu(self)
        if item is None:
            act_add_sec = menu.addAction(self._t("context_add_section"))
            act_add_sec.triggered.connect(self._add_section)
        else:
            obj = item.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(obj, IniSection):
                act_edit = menu.addAction(self._t("context_edit_section"))
                act_edit.triggered.connect(lambda: self._edit_section(item, obj))
                act_add_key = menu.addAction(self._t("context_add_entry"))
                act_add_key.triggered.connect(lambda: self._add_entry(item, obj))
                menu.addSeparator()
                act_del = menu.addAction(self._t("context_delete_section"))
                act_del.triggered.connect(lambda: self._delete_section(item, obj))
            elif isinstance(obj, IniEntry):
                act_edit = menu.addAction(self._t("context_edit_entry"))
                act_edit.triggered.connect(lambda: self._edit_entry(item, obj))
                menu.addSeparator()
                act_del = menu.addAction(self._t("context_delete_entry"))
                act_del.triggered.connect(lambda: self._delete_entry(item, obj))
        menu.exec(self.viewport().mapToGlobal(pos))

    def _edit_section(self, item: QTreeWidgetItem, sec: IniSection) -> None:
        dlg = SectionEditDialog(sec, self._language, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.about_to_change.emit()
            dlg.apply_to_section()
            self._style_section_item(item, sec)
            self.document_changed.emit()

    def _edit_entry(self, item: QTreeWidgetItem, entry: IniEntry) -> None:
        dlg = EntryEditDialog(entry, self._language, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.about_to_change.emit()
            dlg.apply_to_entry()
            self._style_entry_item(item, entry)
            self.document_changed.emit()

    def _add_section(self) -> None:
        if self._doc is None:
            return
        name, ok = self._simple_input(self, self._t("prompt_new_section"), self._t("section_name"))
        if ok and name:
            self.about_to_change.emit()
            self._doc.get_or_create_section(name)
            self._refresh()
            self.document_changed.emit()

    def _add_entry(self, sec_item: QTreeWidgetItem, sec: IniSection) -> None:
        key, ok = self._simple_input(self, self._t("prompt_new_entry"), self._t("entry_key"))
        if ok and key:
            val, ok2 = self._simple_input(self, self._t("prompt_new_entry"), self._t("entry_value"))
            if ok2:
                self.about_to_change.emit()
                entry = IniEntry(key=key, value=val)
                sec.entries.append(entry)
                child = QTreeWidgetItem(sec_item)
                self._style_entry_item(child, entry)
                self.document_changed.emit()

    def _delete_section(self, item: QTreeWidgetItem, sec: IniSection) -> None:
        if self._doc is None:
            return
        reply = QMessageBox.question(
            self,
            self._t("delete_section_title"),
            self._t("delete_section_text", name=sec.name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.about_to_change.emit()
            self._doc.remove_section(sec.name)
            root = self.invisibleRootItem()
            root.removeChild(item)
            self.document_changed.emit()

    def _delete_entry(self, item: QTreeWidgetItem, entry: IniEntry) -> None:
        parent = item.parent()
        if parent is None:
            return
        reply = QMessageBox.question(
            self,
            self._t("delete_entry_title"),
            self._t("delete_entry_text", key=entry.key),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.about_to_change.emit()
        sec: IniSection = parent.data(0, Qt.ItemDataRole.UserRole)
        sec.remove_entry(entry.key)
        parent.removeChild(item)
        self.document_changed.emit()

    @staticmethod
    def _simple_input(parent: QWidget, title: str, label: str) -> tuple[str, bool]:
        from PyQt6.QtWidgets import QInputDialog
        return QInputDialog.getText(parent, title, label)
