"""
main_window.py – PyQt6 main window for the INI Editor application.
"""
from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QAction, QColor, QFont, QIcon, QKeySequence, QPalette, QPixmap,
    QTextCharFormat, QSyntaxHighlighter,
)
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QFileDialog, QFormLayout, QFrame, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QSizePolicy, QLineEdit, QMainWindow, QMenu, QMenuBar, QMessageBox,
    QPlainTextEdit, QPushButton, QSplitter, QStatusBar, QTabWidget, QTextEdit,
    QToolBar, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

try:
    from src.ini_parser import (
        ExportFormat, IniDocument, IniEntry, IniParser, IniSection, SortMode,
    )
except ModuleNotFoundError:
    from ini_parser import (
        ExportFormat, IniDocument, IniEntry, IniParser, IniSection, SortMode,
    )


class Language(Enum):
    DE = "de"
    EN = "en"

TRANSLATIONS = {
    Language.DE: {
        "app_name": "ini-file-editor",
        "status_ready": "Bereit – Öffnen Sie eine INI-Datei oder erstellen Sie ein neues Dokument.",
        "status_new_document": "Neues Dokument erstellt.",
        "status_loaded": "Geladen: {path}",
        "status_merged": "{count} INI-Datei(en) zusammengeführt.",
        "status_saved": "Gespeichert: {path}",
        "status_exported": "Exportiert nach: {path}",
        "sort_group": "🔀 Sortierung",
        "sort_none": "Keine Sortierung",
        "sort_sections": "Abschnitte alphabetisch",
        "sort_keys": "Schlüssel alphabetisch",
        "sort_both": "Abschnitte & Schlüssel alphabetisch",
        "export_group": "📋Export-Format",
        "export_button": "⤵ Exportieren",
        "language_label": "🌍 Sprache",
        "preview_tab": "👁 Vorschau",
        "header_tab": "📝 Header-Kommentare",
        "header_placeholder": "Globale Kopf-Kommentare der INI-Datei …",
        "entry_edit_title": "Eintrag bearbeiten",
        "entry_key": "Schlüssel:",
        "entry_value": "Wert:",
        "entry_inline": "Inline-Kommentar:",
        "entry_preceding": "Vorherige Kommentare:",
        "section_edit_title": "Abschnitt bearbeiten",
        "section_name": "Abschnittsname:",
        "section_pre_comments": "Kommentare (vor Header):",
        "section_post_comments": "Kommentare (nach Einträgen):",
        "context_add_section": "➕ Abschnitt hinzufügen",
        "context_edit_section": "✏️ Abschnitt bearbeiten",
        "context_add_entry": "➕ Schlüssel hinzufügen",
        "context_delete_section": "🗑️ Abschnitt löschen",
        "context_edit_entry": "✏️ Eintrag bearbeiten",
        "context_delete_entry": "🗑️ Eintrag löschen",
        "menu_file": "&Datei",
        "menu_edit": "&Bearbeiten",
        "menu_view": "&Ansicht",
        "menu_help": "&Hilfe",
        "action_new": "&Neu",
        "action_open": "📁 &Öffnen…",
        "action_merge": "🔁 Mehrere Dateien zusammenführen…",
        "action_save": "💾 &Speichern",
        "action_save_as": "💾 Speichern &als…",
        "action_export": "⤵ &Exportieren…",
        "action_quit": "❌ &Beenden",
        "action_add_section": "➕ Abschnitt &hinzufügen",
        "action_expand": "Alle &aufklappen",
        "action_collapse": "Alle &einklappen",
        "action_about": "ℹ️ &Über …",
        "toolbar_name": "Hauptwerkzeuge",
        "open_file_title": "INI-Datei öffnen",
        "merge_files_title": "INI-Dateien zusammenführen",
        "save_file_title": "INI-Datei speichern",
        "no_document_title": "Kein Dokument",
        "no_document_text": "Bitte zuerst eine INI-Datei öffnen oder erstellen.",
        "error_open": "Datei konnte nicht geöffnet werden:\n{exc}",
        "error_save": "Datei konnte nicht gespeichert werden:\n{exc}",
        "error_export": "Export-Fehler",
        "delete_section_title": "Abschnitt löschen",
        "delete_section_text": "Abschnitt [{name}] und alle Einträge wirklich löschen?",
        "delete_entry_title": "Eintrag löschen",
        "delete_entry_text": "Eintrag [{key}] wirklich löschen?",
        "confirm_discard_title": "Ungespeicherte Änderungen",
        "confirm_discard_text": "Es gibt ungespeicherte Änderungen. Wirklich fortfahren?",
        "about_title": "Über {app}",
        "about_text": "<h3>{app}</h3><p>Ein kommentarerhaltender INI-Datei-Editor mit Export nach JSON, XML und YAML.</p><p>Entwickelt mit Python 3 und PyQt6.</p><p>Entwickelt von Thomas Reichenbach (Helferlein21963)</p>",
        "prompt_new_section": "Neuer Abschnitt",
        "prompt_new_entry": "Neuer Eintrag",
        "prompt_key_label": "Schlüssel:",
        "prompt_value_label": "Wert:",
        "tree_label": "📋 Struktur-Übersicht",
        "tree_header_section": "Schlüssel / Abschnitt",
        "tree_header_value": "Wert",
        "tree_header_comment": "Kommentar",
        "merge_error": "Fehler beim Import",
        "action_find": "🔍 &Suchen",
        "action_find_replace": "🔄 Suchen & &Ersetzen",
        "find_title": "Suchen",
        "find_label": "Suchtext:",
        "find_case_sensitive": "Groß-/Kleinschreibung beachten",
        "find_whole_words": "Ganze Wörter",
        "find_next": "Nächstes",
        "find_prev": "Vorheriges",
        "find_not_found": "Suchtext nicht gefunden",
        "find_count": "{count} Treffer gefunden",
        "find_replace_title": "Suchen & Ersetzen",
        "find_replace_label": "Ersetzen durch:",
        "find_replace_one": "Ersetzen",
        "find_replace_all": "Alle ersetzen",
        "find_replace_count": "{count} Einträge ersetzt",
    },
    Language.EN: {
        "app_name": "ini-file-editor",
        "status_ready": "Ready — open an INI file or create a new document.",
        "status_new_document": "New document created.",
        "status_loaded": "Loaded: {path}",
        "status_merged": "{count} INI file(s) merged.",
        "status_saved": "Saved: {path}",
        "status_exported": "Exported to: {path}",
        "sort_group": "🔀 Sorting",
        "sort_none": "No sorting",
        "sort_sections": "Sections alphabetically",
        "sort_keys": "Keys alphabetically",
        "sort_both": "Sections & keys alphabetically",
        "export_group": "📋 Export format",
        "export_button": "⤵ Export",
        "language_label": "🌍 Language",
        "preview_tab": "👁 Preview",
        "header_tab": "📝 Header comments",
        "header_placeholder": "Global header comments for the INI file…",
        "entry_edit_title": "Edit entry",
        "entry_key": "Key:",
        "entry_value": "Value:",
        "entry_inline": "Inline comment:",
        "entry_preceding": "Preceding comments:",
        "section_edit_title": "Edit section",
        "section_name": "Section name:",
        "section_pre_comments": "Comments (before header):",
        "section_post_comments": "Comments (after entries):",
        "context_add_section": "➕ Add section",
        "context_edit_section": "✏️ Edit section",
        "context_add_entry": "➕ Add key",
        "context_delete_section": "🗑️ Delete section",
        "context_edit_entry": "✏️ Edit entry",
        "context_delete_entry": "🗑️ Delete entry",
        "menu_file": "&File",
        "menu_edit": "&Edit",
        "menu_view": "&View",
        "menu_help": "&Help",
        "action_new": "&New",
        "action_open": "📁 &Open…",
        "action_merge": "🔁 Merge multiple files…",
        "action_save": "💾 &Save",
        "action_save_as": "💾 Save &as…",
        "action_export": "⤵ &Export…",
        "action_quit": "❌ &Quit",
        "action_add_section": "➕ Add section",
        "action_expand": "Expand all",
        "action_collapse": "Collapse all",
        "action_about": "ℹ️ &About …",
        "toolbar_name": "Main tools",
        "open_file_title": "Open INI file",
        "merge_files_title": "Merge INI files",
        "save_file_title": "Save INI file",
        "no_document_title": "No document",
        "no_document_text": "Please open or create an INI file first.",
        "error_open": "Could not open file:\n{exc}",
        "error_save": "Could not save file:\n{exc}",
        "error_export": "Export error",
        "delete_section_title": "Delete section",
        "delete_section_text": "Delete section [{name}] and all entries?",
        "delete_entry_title": "Delete entry",
        "delete_entry_text": "Delete entry [{key}]?",
        "confirm_discard_title": "Unsaved changes",
        "confirm_discard_text": "There are unsaved changes. Continue anyway?",
        "about_title": "About {app}",
        "about_text": "<h3>{app}</h3><p>A comment-preserving INI editor with export to JSON, XML, and YAML.</p><p>Built with Python 3 and PyQt6.</p><p>Developed by Thomas Reichenbach (Helferlein21963)</p>",
        "prompt_new_section": "New section",
        "prompt_new_entry": "New entry",
        "prompt_key_label": "Key:",
        "prompt_value_label": "Value:",
        "tree_label": "📋 Structure overview",
        "tree_header_section": "Key / Section",
        "tree_header_value": "Value",
        "tree_header_comment": "Comment",
        "merge_error": "Import error",
        "action_find": "🔍 &Find",
        "action_find_replace": "🔄 Find & &Replace",
        "find_title": "Find",
        "find_label": "Search text:",
        "find_case_sensitive": "Case sensitive",
        "find_whole_words": "Whole words",
        "find_next": "Next",
        "find_prev": "Previous",
        "find_not_found": "Search text not found",
        "find_count": "{count} matches found",
        "find_replace_title": "Find & Replace",
        "find_replace_label": "Replace with:",
        "find_replace_one": "Replace",
        "find_replace_all": "Replace all",
        "find_replace_count": "{count} entries replaced",
    },
}

def translate(lang: Language, key: str, **kwargs: object) -> str:
    text = TRANSLATIONS[lang].get(key, key)
    return text.format(**kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# Syntax highlighter for the raw text preview
# ─────────────────────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────────────────────
# Entry editor dialog
# ─────────────────────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────────────────────
# Section editor dialog
# ─────────────────────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────────────────────
# Central tree widget that displays sections and entries
# ─────────────────────────────────────────────────────────────────────────────
class IniTreeWidget(QTreeWidget):
    document_changed = pyqtSignal()

    def __init__(self, language: Language, parent: Optional[QWidget] = None) -> None:
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

    # ── public ────────────────────────────────────────────────────────────
    def load_document(self, doc: IniDocument) -> None:
        self._doc = doc
        self._refresh()

    def set_sort_mode(self, mode: SortMode) -> None:
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
        comment_text = " | ".join(
            c for c in sec.preceding_comments if c.strip()
        )
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
            return QColor("#FF4B4B")  # rot
        if normalized in {"true", "1"}:
            return QColor("#6CCC70")  # grün

        try:
            int(raw)
        except ValueError:
            pass
        else:
            return QColor("#4DD0E1")  # cyan

        try:
            float(raw)
        except ValueError:
            pass
        else:
            return QColor("#B468C7")  # violett

        return QColor("#D4840A")  # orange

    # ── interactions ──────────────────────────────────────────────────────
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
            dlg.apply_to_section()
            self._style_section_item(item, sec)
            self.document_changed.emit()

    def _edit_entry(self, item: QTreeWidgetItem, entry: IniEntry) -> None:
        dlg = EntryEditDialog(entry, self._language, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dlg.apply_to_entry()
            self._style_entry_item(item, entry)
            self.document_changed.emit()

    def _add_section(self) -> None:
        if self._doc is None:
            return
        name, ok = self._simple_input(self._t("prompt_new_section"), self._t("section_name"))
        if ok and name:
            sec = IniSection(name=name)
            self._doc.sections.append(sec)
            self._refresh()
            self.document_changed.emit()

    def _add_entry(self, sec_item: QTreeWidgetItem, sec: IniSection) -> None:
        key, ok = self._simple_input(self._t("prompt_new_entry"), self._t("entry_key"))
        if ok and key:
            val, ok2 = self._simple_input(self._t("prompt_new_entry"), self._t("entry_value"))
            if ok2:
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
        sec: IniSection = parent.data(0, Qt.ItemDataRole.UserRole)
        sec.remove_entry(entry.key)
        parent.removeChild(item)
        self.document_changed.emit()

    @staticmethod
    def _simple_input(title: str, label: str) -> tuple[str, bool]:
        from PyQt6.QtWidgets import QInputDialog
        return QInputDialog.getText(None, title, label)


# ─────────────────────────────────────────────────────────────────────────────
# Find dialog
# ─────────────────────────────────────────────────────────────────────────────
class FindDialog(QDialog):
    """A modeless Find dialog"""
    found = pyqtSignal(int)  # emits the number of matches found
    
    def __init__(self, language: Language, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._language = language
        self.setWindowTitle(translate(language, "find_title"))
        self.setMinimumWidth(400)
        self.setWindowModality(Qt.WindowModality.NonModal)
        
        layout = QVBoxLayout(self)
        
        # Search field
        search_layout = QHBoxLayout()
        self._search_label = QLabel(translate(language, "find_label"))
        self._search_edit = QLineEdit()
        self._search_edit.returnPressed.connect(self._find_next)
        search_layout.addWidget(self._search_label)
        search_layout.addWidget(self._search_edit)
        layout.addLayout(search_layout)
        
        # Options
        options_layout = QHBoxLayout()
        self._case_check = QCheckBox(translate(language, "find_case_sensitive"))
        self._whole_words_check = QCheckBox(translate(language, "find_whole_words"))
        options_layout.addWidget(self._case_check)
        options_layout.addWidget(self._whole_words_check)
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self._prev_btn = QPushButton(translate(language, "find_prev"))
        self._prev_btn.clicked.connect(self._find_prev)
        self._next_btn = QPushButton(translate(language, "find_next"))
        self._next_btn.clicked.connect(self._find_next)
        self._close_btn = QPushButton("Close")
        self._close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self._prev_btn)
        buttons_layout.addWidget(self._next_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self._close_btn)
        layout.addLayout(buttons_layout)
        
        # Status label
        self._status_label = QLabel("")
        layout.addWidget(self._status_label)
    
    def set_language(self, language: Language) -> None:
        """Update all text elements for the new language"""
        self._language = language
        self.setWindowTitle(translate(language, "find_title"))
        self._search_label.setText(translate(language, "find_label"))
        self._case_check.setText(translate(language, "find_case_sensitive"))
        self._whole_words_check.setText(translate(language, "find_whole_words"))
        self._prev_btn.setText(translate(language, "find_prev"))
        self._next_btn.setText(translate(language, "find_next"))
    
    def get_search_text(self) -> str:
        return self._search_edit.text()
    
    def is_case_sensitive(self) -> bool:
        return self._case_check.isChecked()
    
    def is_whole_words(self) -> bool:
        return self._whole_words_check.isChecked()
    
    def set_status(self, message: str) -> None:
        self._status_label.setText(message)
    
    def _find_next(self) -> None:
        pass  # Will be connected to MainWindow
    
    def _find_prev(self) -> None:
        pass  # Will be connected to MainWindow
    
    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._search_edit.clear()
        self._status_label.clear()
        super().closeEvent(event)


# ─────────────────────────────────────────────────────────────────────────────
# Find & Replace dialog
# ─────────────────────────────────────────────────────────────────────────────
class FindReplaceDialog(QDialog):
    """A modeless Find & Replace dialog"""
    
    def __init__(self, language: Language, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._language = language
        self.setWindowTitle(translate(language, "find_replace_title"))
        self.setMinimumWidth(450)
        self.setWindowModality(Qt.WindowModality.NonModal)
        
        layout = QVBoxLayout(self)
        
        # Search field
        search_layout = QHBoxLayout()
        self._search_label = QLabel(translate(language, "find_label"))
        self._search_edit = QLineEdit()
        self._search_edit.returnPressed.connect(self._find_next)
        search_layout.addWidget(self._search_label)
        search_layout.addWidget(self._search_edit)
        layout.addLayout(search_layout)
        
        # Replace field
        replace_layout = QHBoxLayout()
        self._replace_label = QLabel(translate(language, "find_replace_label"))
        self._replace_edit = QLineEdit()
        self._replace_edit.returnPressed.connect(self._replace_next)
        replace_layout.addWidget(self._replace_label)
        replace_layout.addWidget(self._replace_edit)
        layout.addLayout(replace_layout)
        
        # Options
        options_layout = QHBoxLayout()
        self._case_check = QCheckBox(translate(language, "find_case_sensitive"))
        self._whole_words_check = QCheckBox(translate(language, "find_whole_words"))
        options_layout.addWidget(self._case_check)
        options_layout.addWidget(self._whole_words_check)
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self._prev_btn = QPushButton(translate(language, "find_prev"))
        self._prev_btn.clicked.connect(self._find_prev)
        self._next_btn = QPushButton(translate(language, "find_next"))
        self._next_btn.clicked.connect(self._find_next)
        self._replace_btn = QPushButton(translate(language, "find_replace_one"))
        self._replace_btn.clicked.connect(self._replace_next)
        self._replace_all_btn = QPushButton(translate(language, "find_replace_all"))
        self._replace_all_btn.clicked.connect(self._replace_all)
        self._close_btn = QPushButton("Close")
        self._close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self._prev_btn)
        buttons_layout.addWidget(self._next_btn)
        buttons_layout.addWidget(self._replace_btn)
        buttons_layout.addWidget(self._replace_all_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self._close_btn)
        layout.addLayout(buttons_layout)
        
        # Status label
        self._status_label = QLabel("")
        layout.addWidget(self._status_label)
    
    def set_language(self, language: Language) -> None:
        """Update all text elements for the new language"""
        self._language = language
        self.setWindowTitle(translate(language, "find_replace_title"))
        self._search_label.setText(translate(language, "find_label"))
        self._replace_label.setText(translate(language, "find_replace_label"))
        self._case_check.setText(translate(language, "find_case_sensitive"))
        self._whole_words_check.setText(translate(language, "find_whole_words"))
        self._prev_btn.setText(translate(language, "find_prev"))
        self._next_btn.setText(translate(language, "find_next"))
        self._replace_btn.setText(translate(language, "find_replace_one"))
        self._replace_all_btn.setText(translate(language, "find_replace_all"))
    
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
    
    def _find_next(self) -> None:
        pass  # Will be connected to MainWindow
    
    def _find_prev(self) -> None:
        pass  # Will be connected to MainWindow
    
    def _replace_next(self) -> None:
        pass  # Will be connected to MainWindow
    
    def _replace_all(self) -> None:
        pass  # Will be connected to MainWindow
    
    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._search_edit.clear()
        self._replace_edit.clear()
        self._status_label.clear()
        super().closeEvent(event)


# ─────────────────────────────────────────────────────────────────────────────
# Main window
# ─────────────────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    APP_NAME = "ini-file-editor"

    def __init__(self) -> None:
        super().__init__()
        self._doc: Optional[IniDocument] = None
        self._dirty = False
        self._current_sort = SortMode.NONE
        self._current_format = ExportFormat.INI
        self._language = Language.EN
        self._find_dialog: Optional[FindDialog] = None
        self._find_replace_dialog: Optional[FindReplaceDialog] = None
        self._last_tree_match: Optional[QTreeWidgetItem] = None

        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._apply_dark_theme()

        # Set window icon
        if hasattr(sys, '_MEIPASS'):
            # Running in PyInstaller bundle
            icon_path = Path(sys._MEIPASS) / "src" / "icon.ico"
        else:
            icon_path = Path(__file__).resolve().parent / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._update_translations()
        self.resize(1200, 750)
        self.statusBar().showMessage(self._t("status_ready"))

    def _t(self, key: str, **kwargs: object) -> str:
        return translate(self._language, key, **kwargs)

    def _update_translations(self) -> None:
        self.setWindowTitle(self._t("app_name"))
        self._sort_group.setTitle(self._t("sort_group"))
        self._sort_combo.blockSignals(True)
        self._sort_combo.clear()
        self._sort_combo.addItems([
            self._t("sort_none"),
            self._t("sort_sections"),
            self._t("sort_keys"),
            self._t("sort_both"),
        ])
        self._sort_combo.setCurrentIndex(self._current_sort.value - 1 if self._current_sort != SortMode.NONE else 0)
        self._sort_combo.blockSignals(False)
        self._export_group.setTitle(self._t("export_group"))
        self._export_button.setText(self._t("export_button"))
        self._language_group.setTitle(self._t("language_label"))
        self._left_label.setText(self._t("tree_label"))
        self._tabs.setTabText(0, self._t("preview_tab"))
        self._tabs.setTabText(1, self._t("header_tab"))
        self._header_edit.setPlaceholderText(self._t("header_placeholder"))
        self._file_menu.setTitle(self._t("menu_file"))
        self._edit_menu.setTitle(self._t("menu_edit"))
        self._view_menu.setTitle(self._t("menu_view"))
        self._help_menu.setTitle(self._t("menu_help"))
        self._act_new.setText(self._t("action_new"))
        self._act_open.setText(self._t("action_open"))
        self._act_merge.setText(self._t("action_merge"))
        self._act_save.setText(self._t("action_save"))
        self._act_save_as.setText(self._t("action_save_as"))
        self._act_export.setText(self._t("action_export"))
        self._act_quit.setText(self._t("action_quit"))
        self._act_add_section.setText(self._t("action_add_section"))
        self._act_expand.setText(self._t("action_expand"))
        self._act_collapse.setText(self._t("action_collapse"))
        self._act_about.setText(self._t("action_about"))
        self._act_find.setText(self._t("action_find"))
        self._act_find_replace.setText(self._t("action_find_replace"))
        if hasattr(self, '_toolbar'):
            self._toolbar.setWindowTitle(self._t("toolbar_name"))
            self._tb_open.setText(self._t("action_open"))
            self._tb_save.setText(self._t("action_save"))
            self._tb_export.setText(self._t("action_export"))
            self._tb_add_section.setText(self._t("action_add_section"))
        self._language_combo.blockSignals(True)
        self._language_combo.setItemText(0, "Deutsch")
        self._language_combo.setItemText(1, "English")
        self._language_combo.setCurrentIndex(0 if self._language == Language.DE else 1)
        self._language_combo.blockSignals(False)
        if self._doc is None:
            self.statusBar().showMessage(self._t("status_ready"))
        else:
            self._update_title()

    def _on_language_changed(self, idx: int) -> None:
        self._language = Language.DE if idx == 0 else Language.EN
        self._tree.set_language(self._language)
        # Update dialog languages if they exist
        if self._find_dialog is not None:
            self._find_dialog.set_language(self._language)
        if self._find_replace_dialog is not None:
            self._find_replace_dialog.set_language(self._language)
        self._update_translations()
        self._load_into_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(6, 6, 6, 6)

        # Top control bar
        ctrl_bar = QHBoxLayout()

        # Sort group
        self._sort_group = QGroupBox()
        sort_layout = QHBoxLayout(self._sort_group)
        self._sort_combo = QComboBox()
        self._sort_combo.addItems([
            self._t("sort_none"),
            self._t("sort_sections"),
            self._t("sort_keys"),
            self._t("sort_both"),
        ])
        self._sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        sort_layout.addWidget(self._sort_combo)
        ctrl_bar.addWidget(self._sort_group)

        # Export group
        self._export_group = QGroupBox()
        export_layout = QHBoxLayout(self._export_group)
        self._format_combo = QComboBox()
        self._format_combo.addItems(["INI", "JSON", "XML", "YAML"])
        self._format_combo.currentIndexChanged.connect(self._on_format_changed)
        export_layout.addWidget(self._format_combo)
        self._export_button = QPushButton()
        self._export_button.clicked.connect(self._export_file)
        export_layout.addWidget(self._export_button)
        ctrl_bar.addWidget(self._export_group)

        # Language group
        self._language_group = QGroupBox()
        language_layout = QHBoxLayout(self._language_group)
        self._language_combo = QComboBox()
        self._language_combo.addItems(["Deutsch", "English"])
        self._language_combo.currentIndexChanged.connect(self._on_language_changed)
        language_layout.addWidget(self._language_combo)
        ctrl_bar.addWidget(self._language_group)

        ctrl_bar.addStretch()

        self._logo_label: Optional[QLabel] = None
        self._logo_pixmap: Optional[QPixmap] = None
        if hasattr(sys, '_MEIPASS'):
            # Running in PyInstaller bundle
            logo_path = Path(sys._MEIPASS) / "src" / "logo.png"
        else:
            logo_path = Path(__file__).resolve().parent / "logo.png"
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            if not pixmap.isNull():
                self._logo_pixmap = pixmap
                self._logo_label = QLabel()
                self._logo_label.setObjectName("logoLabel")
                self._logo_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self._logo_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
                self._logo_label.setMinimumHeight(48)
                self._logo_label.setMaximumHeight(64)
                self._logo_label.setMaximumWidth(240)
                self._logo_label.setScaledContents(False)
                self._update_logo_pixmap()
                ctrl_bar.addWidget(self._logo_label)

        root_layout.addLayout(ctrl_bar)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: tree
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_label = QLabel(self._t("tree_label"))
        left_label.setStyleSheet("font-weight: bold; padding: 4px;")
        self._left_label = left_label
        left_layout.addWidget(left_label)
        self._tree = IniTreeWidget(self._language)
        self._tree.document_changed.connect(self._on_document_changed)
        left_layout.addWidget(self._tree)
        splitter.addWidget(left_frame)

        # Right: tabs
        self._tabs = QTabWidget()

        self._preview_edit = QPlainTextEdit()
        self._preview_edit.setReadOnly(True)
        self._preview_edit.setFont(QFont("Courier New", 10))
        self._highlighter = IniHighlighter(self._preview_edit.document())
        self._tabs.addTab(self._preview_edit, self._t("preview_tab"))

        self._header_edit = QPlainTextEdit()
        self._header_edit.setFont(QFont("Courier New", 10))
        self._header_edit.setPlaceholderText(self._t("header_placeholder"))
        self._header_edit.textChanged.connect(self._on_header_changed)
        self._tabs.addTab(self._header_edit, self._t("header_tab"))

        splitter.addWidget(self._tabs)
        splitter.setSizes([420, 780])
        root_layout.addWidget(splitter, 1)

    def _update_logo_pixmap(self) -> None:
        if self._logo_pixmap is None or self._logo_label is None:
            return
        width = self._logo_label.width()
        if width <= 0:
            width = 160
        width = min(width, 240)
        self._logo_label.setPixmap(
            self._logo_pixmap.scaled(
                width, self._logo_label.maximumHeight(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._logo_label is not None:
            self._update_logo_pixmap()

    def _build_menu(self) -> None:
        bar = self.menuBar()

        # File
        self._file_menu = bar.addMenu(self._t("menu_file"))
        self._act_new = QAction(self._t("action_new"), self)
        self._act_new.setShortcut(QKeySequence.StandardKey.New)
        self._act_new.triggered.connect(self._new_document)
        self._file_menu.addAction(self._act_new)

        self._act_open = QAction(self._t("action_open"), self)
        self._act_open.setShortcut(QKeySequence.StandardKey.Open)
        self._act_open.triggered.connect(self._open_file)
        self._file_menu.addAction(self._act_open)

        self._act_merge = QAction(self._t("action_merge"), self)
        self._act_merge.triggered.connect(self._merge_files)
        self._file_menu.addAction(self._act_merge)

        self._file_menu.addSeparator()
        self._act_save = QAction(self._t("action_save"), self)
        self._act_save.setShortcut(QKeySequence.StandardKey.Save)
        self._act_save.triggered.connect(self._save_file)
        self._file_menu.addAction(self._act_save)

        self._act_save_as = QAction(self._t("action_save_as"), self)
        self._act_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        self._act_save_as.triggered.connect(self._save_file_as)
        self._file_menu.addAction(self._act_save_as)

        self._file_menu.addSeparator()
        self._act_export = QAction(self._t("action_export"), self)
        self._act_export.triggered.connect(self._export_file)
        self._file_menu.addAction(self._act_export)

        self._file_menu.addSeparator()
        self._act_quit = QAction(self._t("action_quit"), self)
        self._act_quit.setShortcut(QKeySequence.StandardKey.Quit)
        self._act_quit.triggered.connect(self.close)
        self._file_menu.addAction(self._act_quit)

        # Edit
        self._edit_menu = bar.addMenu(self._t("menu_edit"))
        self._act_add_section = QAction(self._t("action_add_section"), self)
        self._act_add_section.triggered.connect(self._tree._add_section)
        self._edit_menu.addAction(self._act_add_section)
        
        self._edit_menu.addSeparator()
        
        self._act_find = QAction(self._t("action_find"), self)
        self._act_find.setShortcut(QKeySequence.StandardKey.Find)
        self._act_find.triggered.connect(self._show_find_dialog)
        self._edit_menu.addAction(self._act_find)
        
        self._act_find_replace = QAction(self._t("action_find_replace"), self)
        self._act_find_replace.setShortcut(QKeySequence.StandardKey.Replace)
        self._act_find_replace.triggered.connect(self._show_find_replace_dialog)
        self._edit_menu.addAction(self._act_find_replace)

        # View
        self._view_menu = bar.addMenu(self._t("menu_view"))
        self._act_expand = QAction(self._t("action_expand"), self)
        self._act_expand.triggered.connect(self._tree.expandAll)
        self._view_menu.addAction(self._act_expand)
        self._act_collapse = QAction(self._t("action_collapse"), self)
        self._act_collapse.triggered.connect(self._tree.collapseAll)
        self._view_menu.addAction(self._act_collapse)

        # Help
        self._help_menu = bar.addMenu(self._t("menu_help"))
        self._act_about = QAction(self._t("action_about"), self)
        self._act_about.triggered.connect(self._show_about)
        self._help_menu.addAction(self._act_about)

    def _build_toolbar(self) -> None:
        self._toolbar = QToolBar(self._t("toolbar_name"))
        self._toolbar.setMovable(False)
        self.addToolBar(self._toolbar)
        self._tb_open = self._toolbar.addAction(self._t("action_open"), self._open_file)
        self._tb_save = self._toolbar.addAction(self._t("action_save"), self._save_file)
        self._toolbar.addSeparator()
        self._tb_export = self._toolbar.addAction(self._t("action_export"), self._export_file)
        self._toolbar.addSeparator()
        self._tb_add_section = self._toolbar.addAction(self._t("action_add_section"), self._tree._add_section)

    # ── Dark theme ────────────────────────────────────────────────────────
    def _apply_dark_theme(self) -> None:
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI', 'Ubuntu', sans-serif;
                font-size: 13px;
            }
            QMenuBar { background-color: #181825; }
            QMenuBar::item:selected { background-color: #313244; }
            QMenu { background-color: #181825; border: 1px solid #45475a; }
            QMenu::item:selected { background-color: #313244; }
            QToolBar { background-color: #181825; border-bottom: 1px solid #45475a; spacing: 4px; }
            QToolButton { padding: 4px 10px; border-radius: 4px; }
            QToolButton:hover { background-color: #313244; }
            QGroupBox { border: 1px solid #45475a; border-radius: 6px; margin-top: 8px; padding: 6px; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; }
            QComboBox {
                background-color: #313244; border: 1px solid #45475a;
                border-radius: 4px; padding: 4px 8px; min-width: 200px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background-color: #313244; selection-background-color: #45475a; }
            QPushButton {
                background-color: #89b4fa; color: #1e1e2e;
                border: none; border-radius: 4px; padding: 5px 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #b4c7fa; }
            QPushButton:pressed { background-color: #6b8fcc; }
            QTreeWidget {
                background-color: #181825; alternate-background-color: #1e1e2e;
                border: 1px solid #45475a; border-radius: 4px;
            }
            QTreeWidget::item:selected { background-color: #313244; }
            QHeaderView::section {
                background-color: #313244; border: none;
                padding: 5px; border-bottom: 1px solid #45475a;
            }
            QPlainTextEdit, QTextEdit {
                background-color: #181825; border: 1px solid #45475a;
                border-radius: 4px; padding: 4px;
            }
            QTabWidget::pane { border: 1px solid #45475a; border-radius: 4px; }
            QTabBar::tab {
                background-color: #313244; border: 1px solid #45475a;
                padding: 6px 14px; border-bottom: none;
            }
            QTabBar::tab:selected { background-color: #45475a; }
            QStatusBar { background-color: #181825; border-top: 1px solid #45475a; }
            QFrame { border: none; }
            QDialog { background-color: #1e1e2e; }
            QLineEdit {
                background-color: #313244; border: 1px solid #45475a;
                border-radius: 4px; padding: 4px 8px;
            }
            QSplitter::handle { background-color: #45475a; width: 2px; }
        """)

    # ── Document management ───────────────────────────────────────────────
    def _new_document(self) -> None:
        if not self._confirm_discard():
            return
        self._doc = IniDocument()
        self._load_into_ui()
        self._dirty = False
        self._update_title()
        self.statusBar().showMessage(self._t("status_new_document"))

    def _load_into_ui(self) -> None:
        if self._doc is None:
            return
        self._tree.load_document(self._doc)
        self._tree.set_sort_mode(self._current_sort)
        # header comments
        self._header_edit.blockSignals(True)
        self._header_edit.setPlainText("\n".join(self._doc.header_comments))
        self._header_edit.blockSignals(False)
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        if self._doc is None:
            return
        doc = self._doc.sorted_copy(self._current_sort)
        try:
            text = doc.export(self._current_format)
        except Exception as exc:
            text = f"[Fehler beim Rendern: {exc}]"
        self._preview_edit.setPlainText(text)
        self._preview_edit.repaint()

    # ── Slots ─────────────────────────────────────────────────────────────
    def _on_sort_changed(self, idx: int) -> None:
        modes = [
            SortMode.NONE,
            SortMode.SECTIONS_ALPHA,
            SortMode.KEYS_ALPHA,
            SortMode.SECTIONS_AND_KEYS_ALPHA,
        ]
        self._current_sort = modes[idx]
        self._tree.set_sort_mode(self._current_sort)
        self._refresh_preview()

    def _on_format_changed(self, idx: int) -> None:
        fmts = [ExportFormat.INI, ExportFormat.JSON, ExportFormat.XML, ExportFormat.YAML]
        self._current_format = fmts[idx]
        self._refresh_preview()

    def _on_document_changed(self) -> None:
        self._dirty = True
        self._update_title()
        self._refresh_preview()

    def _on_header_changed(self) -> None:
        if self._doc is None:
            return
        raw = self._header_edit.toPlainText()
        self._doc.header_comments = raw.splitlines() if raw.strip() else []
        self._dirty = True
        self._update_title()
        self._refresh_preview()

    # ── File I/O ──────────────────────────────────────────────────────────
    def _open_file(self) -> None:
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, self._t("open_file_title"), "",
            "INI-Dateien (*.ini *.cfg *.conf);;Alle Dateien (*)"
        )
        if not path:
            return
        try:
            self._doc = IniParser.parse_file(path)
            self._load_into_ui()
            self._dirty = False
            self._update_title(Path(path).name)
            self.statusBar().showMessage(self._t("status_loaded", path=path))
        except Exception as exc:
            QMessageBox.critical(self, self._t("error_export"), self._t("error_open", exc=str(exc)))

    def _merge_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, self._t("merge_files_title"), "",
            "INI-Dateien (*.ini *.cfg *.conf);;Alle Dateien (*)"
        )
        if not paths:
            return

        if self._doc is None:
            self._doc = IniDocument()

        merged = 0
        for path in paths:
            try:
                doc = IniParser.parse_file(path)
                self._doc.merge_from(doc)
                merged += 1
            except Exception as exc:
                QMessageBox.warning(self, self._t("merge_error"), f"{path}: {exc}")

        if merged == 0:
            return

        self._load_into_ui()
        self._dirty = True
        self._update_title()
        self.statusBar().showMessage(self._t("status_merged", count=merged))

    def _save_file(self) -> None:
        if self._doc is None:
            return
        if self._doc.source_path:
            self._write_ini(self._doc.source_path)
        else:
            self._save_file_as()

    def _save_file_as(self) -> None:
        if self._doc is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, self._t("save_file_title"), "",
            "INI-Dateien (*.ini);;Alle Dateien (*)"
        )
        if path:
            self._write_ini(Path(path))

    def _write_ini(self, path: Path) -> None:
        try:
            # Write based on current sort
            doc = self._doc.sorted_copy(self._current_sort) if self._current_sort != SortMode.NONE else self._doc
            path.write_text(doc.to_ini_string(), encoding="utf-8")
            self._doc.source_path = path
            self._dirty = False
            self._update_title(path.name)
            self.statusBar().showMessage(self._t("status_saved", path=path))
        except Exception as exc:
            QMessageBox.critical(self, self._t("error_export"), self._t("error_save", exc=str(exc)))

    def _export_file(self) -> None:
        if self._doc is None:
            QMessageBox.information(self, self._t("no_document_title"), self._t("no_document_text"))
            return
        ext_map = {
            ExportFormat.INI: ("INI-Dateien (*.ini)", ".ini"),
            ExportFormat.JSON: ("JSON-Dateien (*.json)", ".json"),
            ExportFormat.XML: ("XML-Dateien (*.xml)", ".xml"),
            ExportFormat.YAML: ("YAML-Dateien (*.yaml *.yml)", ".yaml"),
        }
        filt, ext = ext_map[self._current_format]
        path, _ = QFileDialog.getSaveFileName(self, self._t("action_export"), f"export{ext}", f"{filt};;Alle Dateien (*)")
        if not path:
            return
        try:
            doc = self._doc.sorted_copy(self._current_sort)
            content = doc.export(self._current_format)
            Path(path).write_text(content, encoding="utf-8")
            self.statusBar().showMessage(self._t("status_exported", path=path))
        except Exception as exc:
            QMessageBox.critical(self, self._t("error_export"), str(exc))

    # ── Helpers ───────────────────────────────────────────────────────────
    def _update_title(self, filename: str = "") -> None:
        dirty_mark = " *" if self._dirty else ""
        if filename:
            self.setWindowTitle(f"{filename}{dirty_mark} – {self._t('app_name')}")
        else:
            self.setWindowTitle(f"{self._t('app_name')}{dirty_mark}")

    def _confirm_discard(self) -> bool:
        if not self._dirty:
            return True
        reply = QMessageBox.question(
            self, self._t("confirm_discard_title"),
            self._t("confirm_discard_text"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def _show_about(self) -> None:
        QMessageBox.about(
            self, self._t("about_title", app=self.APP_NAME),
            self._t("about_text", app=self.APP_NAME)
        )
    
    # ── Find & Replace ────────────────────────────────────────────────────
    def _show_find_dialog(self) -> None:
        if self._find_dialog is None:
            self._find_dialog = FindDialog(self._language, self)
            self._find_dialog.found.connect(self._on_find_triggered)
            # Connect button clicks
            self._find_dialog._next_btn.clicked.disconnect()
            self._find_dialog._prev_btn.clicked.disconnect()
            self._find_dialog._next_btn.clicked.connect(self._find_next)
            self._find_dialog._prev_btn.clicked.connect(self._find_prev)
        
        self._find_dialog.show()
        self._find_dialog.raise_()
        self._find_dialog.activateWindow()
        self._find_dialog._search_edit.setFocus()
        self._find_dialog._search_edit.selectAll()
    
    def _show_find_replace_dialog(self) -> None:
        if self._find_replace_dialog is None:
            self._find_replace_dialog = FindReplaceDialog(self._language, self)
            # Connect button clicks
            self._find_replace_dialog._next_btn.clicked.disconnect()
            self._find_replace_dialog._prev_btn.clicked.disconnect()
            self._find_replace_dialog._replace_btn.clicked.disconnect()
            self._find_replace_dialog._replace_all_btn.clicked.disconnect()
            self._find_replace_dialog._next_btn.clicked.connect(self._find_next)
            self._find_replace_dialog._prev_btn.clicked.connect(self._find_prev)
            self._find_replace_dialog._replace_btn.clicked.connect(self._replace_next)
            self._find_replace_dialog._replace_all_btn.clicked.connect(self._replace_all)
        
        self._find_replace_dialog.show()
        self._find_replace_dialog.raise_()
        self._find_replace_dialog.activateWindow()
        self._find_replace_dialog._search_edit.setFocus()
        self._find_replace_dialog._search_edit.selectAll()
    
    def _find_next(self) -> None:
        """Search for the next occurrence"""
        dialog = self._find_dialog if self._find_dialog and self._find_dialog.isVisible() else self._find_replace_dialog
        if dialog is None or not dialog.isVisible():
            return
        
        search_text = dialog.get_search_text()
        if not search_text:
            dialog.set_status("")
            return
        
        case_sensitive = dialog.is_case_sensitive()
        whole_words = dialog.is_whole_words()

        count = self._search_in_text_edit(self._preview_edit, search_text, case_sensitive, whole_words, forward=True)

        if count == 0:
            dialog.set_status(self._t("find_not_found"))
        else:
            dialog.set_status(self._t("find_count", count=count))

    def _find_prev(self) -> None:
        """Search for the previous occurrence"""
        dialog = self._find_dialog if self._find_dialog and self._find_dialog.isVisible() else self._find_replace_dialog
        if dialog is None or not dialog.isVisible():
            return

        search_text = dialog.get_search_text()
        if not search_text:
            dialog.set_status("")
            return

        case_sensitive = dialog.is_case_sensitive()
        whole_words = dialog.is_whole_words()

        count = self._search_in_text_edit(self._preview_edit, search_text, case_sensitive, whole_words, forward=False)

        if count == 0:
            dialog.set_status(self._t("find_not_found"))
        else:
            dialog.set_status(self._t("find_count", count=count))
    
    def _sync_doc_from_preview(self) -> None:
        """Re-parse the preview text into self._doc and refresh the tree."""
        text = self._preview_edit.document().toPlainText()
        try:
            new_doc = IniParser.parse_string(text)
            new_doc.source_path = self._doc.source_path if self._doc else None
            self._doc = new_doc
            self._tree.load_document(self._doc)
            self._tree.set_sort_mode(self._current_sort)
        except Exception:
            pass
        self._dirty = True
        self._update_title()

    def _replace_next(self) -> None:
        """Replace the current selection and find next"""
        if self._find_replace_dialog is None or not self._find_replace_dialog.isVisible():
            return
        
        search_text = self._find_replace_dialog.get_search_text()
        replace_text = self._find_replace_dialog.get_replace_text()
        
        if not search_text:
            return
        
        # Try to replace selected text in preview
        cursor = self._preview_edit.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText()
            if selected == search_text or (not self._find_replace_dialog.is_case_sensitive() and selected.lower() == search_text.lower()):
                cursor.insertText(replace_text)
                self._sync_doc_from_preview()

        # Find next occurrence
        self._find_next()
    
    def _replace_all(self) -> None:
        """Replace all occurrences"""
        if self._find_replace_dialog is None or not self._find_replace_dialog.isVisible():
            return
        
        search_text = self._find_replace_dialog.get_search_text()
        replace_text = self._find_replace_dialog.get_replace_text()
        case_sensitive = self._find_replace_dialog.is_case_sensitive()
        
        if not search_text:
            return
        
        # Get all text from preview
        doc = self._preview_edit.document()
        text = doc.toPlainText()
        
        # Replace all
        if case_sensitive:
            new_text = text.replace(search_text, replace_text)
            count = text.count(search_text)
        else:
            # Case-insensitive replacement
            import re
            pattern = re.compile(re.escape(search_text), re.IGNORECASE)
            new_text = pattern.sub(replace_text, text)
            count = len(pattern.findall(text))
        
        if count > 0:
            self._preview_edit.setPlainText(new_text)
            self._sync_doc_from_preview()
            self._find_replace_dialog.set_status(self._t("find_replace_count", count=count))
        else:
            self._find_replace_dialog.set_status(self._t("find_not_found"))
    
    def _count_all_in_text_edit(self, text_edit: QPlainTextEdit, search_text: str, case_sensitive: bool, whole_words: bool) -> int:
        """Count all occurrences of search_text in a QPlainTextEdit."""
        from PyQt6.QtGui import QTextCursor, QTextDocument

        doc = text_edit.document()
        options = QTextDocument.FindFlag(0)
        if case_sensitive:
            options |= QTextDocument.FindFlag.FindCaseSensitively
        if whole_words:
            options |= QTextDocument.FindFlag.FindWholeWords

        count = 0
        cursor = QTextCursor(doc)
        while True:
            cursor = doc.find(search_text, cursor, options)
            if cursor.isNull():
                break
            count += 1
        return count

    def _search_in_text_edit(self, text_edit: QPlainTextEdit, search_text: str, case_sensitive: bool, whole_words: bool, forward: bool = True) -> int:
        """Navigate to next/prev match. Returns total number of matches."""
        from PyQt6.QtGui import QTextCursor, QTextDocument

        doc = text_edit.document()
        cursor = text_edit.textCursor()

        options = QTextDocument.FindFlag(0)
        if case_sensitive:
            options |= QTextDocument.FindFlag.FindCaseSensitively
        if whole_words:
            options |= QTextDocument.FindFlag.FindWholeWords
        if not forward:
            options |= QTextDocument.FindFlag.FindBackward

        found_cursor = doc.find(search_text, cursor, options)

        if found_cursor.isNull():
            # Try wrapping around
            if forward:
                cursor.movePosition(QTextCursor.MoveOperation.Start)
            else:
                cursor.movePosition(QTextCursor.MoveOperation.End)
            found_cursor = doc.find(search_text, cursor, options)

        if not found_cursor.isNull():
            text_edit.setTextCursor(found_cursor)
            if text_edit is self._preview_edit and self._current_format == ExportFormat.INI:
                self._sync_tree_to_preview_match(found_cursor)
            return self._count_all_in_text_edit(text_edit, search_text, case_sensitive, whole_words)

        return 0
    
    def _sync_tree_to_preview_match(self, cursor) -> None:
        """Select the tree item that corresponds to the cursor position in the preview."""
        line_no = cursor.blockNumber()
        lines = self._preview_edit.document().toPlainText().splitlines()

        current_section_name: Optional[str] = None
        matched_key: Optional[str] = None

        for i, line in enumerate(lines[: line_no + 1]):
            stripped = line.strip()
            if stripped.startswith("[") and "]" in stripped:
                current_section_name = stripped[1 : stripped.index("]")]
                if i == line_no:
                    matched_key = None
            elif (
                "=" in stripped
                and not stripped.startswith(";")
                and not stripped.startswith("#")
                and i == line_no
            ):
                matched_key = stripped.split("=", 1)[0].strip()

        if current_section_name is None:
            return

        from PyQt6.QtGui import QBrush, QPalette
        from PyQt6.QtWidgets import QApplication
        palette = QApplication.palette()
        highlight = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight)
        col_count = self._tree.columnCount()

        # Clear previous match background
        if self._last_tree_match is not None:
            for c in range(col_count):
                self._last_tree_match.setBackground(c, QBrush())
            self._last_tree_match = None

        match_item: Optional[QTreeWidgetItem] = None
        for idx in range(self._tree.topLevelItemCount()):
            sec_item = self._tree.topLevelItem(idx)
            sec_data = sec_item.data(0, Qt.ItemDataRole.UserRole)
            if not hasattr(sec_data, "name") or sec_data.name != current_section_name:
                continue
            if matched_key is None:
                match_item = sec_item
            else:
                for j in range(sec_item.childCount()):
                    entry_item = sec_item.child(j)
                    entry_data = entry_item.data(0, Qt.ItemDataRole.UserRole)
                    if hasattr(entry_data, "key") and entry_data.key == matched_key:
                        match_item = entry_item
                        break
            break

        if match_item is not None:
            for c in range(col_count):
                match_item.setBackground(c, QBrush(highlight))
            self._tree.scrollToItem(match_item)
            self._last_tree_match = match_item

    def _search_in_tree(self, search_text: str, case_sensitive: bool, whole_words: bool) -> int:
        """Search in tree and highlight matching items"""
        count = 0
        
        def search_recursive(item: QTreeWidgetItem) -> None:
            nonlocal count
            for col in range(self._tree.columnCount()):
                item_text = item.text(col)
                if self._match_text(item_text, search_text, case_sensitive, whole_words):
                    item.setSelected(True)
                    count += 1
                    break
            
            for i in range(item.childCount()):
                search_recursive(item.child(i))
        
        # Clear previous selection
        self._tree.clearSelection()
        
        # Search from root
        for i in range(self._tree.topLevelItemCount()):
            search_recursive(self._tree.topLevelItem(i))
        
        return count
    
    def _match_text(self, text: str, search_text: str, case_sensitive: bool, whole_words: bool) -> bool:
        """Check if text matches search criteria"""
        if whole_words:
            words = text.split()
            search_words = search_text.split()
            for word in search_words:
                if case_sensitive:
                    if word not in words:
                        return False
                else:
                    if word.lower() not in [w.lower() for w in words]:
                        return False
            return True
        else:
            if case_sensitive:
                return search_text in text
            else:
                return search_text.lower() in text.lower()
    
    def _on_find_triggered(self, count: int) -> None:
        """Slot for find dialog signals"""
        pass

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self._confirm_discard():
            event.accept()
        else:
            event.ignore()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("ini-file-editor")
    app.setOrganizationName("OpenSource")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
