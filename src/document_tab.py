"""Self-contained editor pane shown for one open INI file.

Each :class:`DocumentTab` owns its own :class:`~ini_parser.IniDocument`,
tree widget, preview pane, header editor, and undo/redo stacks. The main
window holds one tab per open file.
"""
from __future__ import annotations

from typing import Optional

import re

from PyQt6 import sip
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QBrush, QColor, QFont, QPalette, QTextCharFormat, QTextCursor, QTextFormat,
)
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QFrame, QLabel, QPlainTextEdit,
    QSplitter, QTabWidget, QTextEdit, QTreeWidgetItem, QVBoxLayout, QWidget,
)

try:
    from src.ini_parser import ExportFormat, IniDocument, IniParser, SortMode
except ModuleNotFoundError:
    from ini_parser import ExportFormat, IniDocument, IniParser, SortMode  # type: ignore[no-redef]

try:
    from src.translations import Language
except ModuleNotFoundError:
    from translations import Language  # type: ignore[no-redef]

try:
    from src.highlighter import IniHighlighter
except ModuleNotFoundError:
    from highlighter import IniHighlighter  # type: ignore[no-redef]

try:
    from src.ini_tree_widget import IniTreeWidget
except ModuleNotFoundError:
    from ini_tree_widget import IniTreeWidget  # type: ignore[no-redef]


class DocumentTab(QSplitter):
    """One open INI file with its own UI state and undo history.

    The tab is a horizontal splitter: the tree widget on the left, the
    preview / header tabs on the right. Undo and redo work on document
    snapshots (``IniDocument.clone()``) rather than Qt's :class:`QUndoStack`.

    Signals:
        content_changed: Emitted whenever the underlying document is mutated
            (entry edited, section added, preview re-parsed, undo, etc.).
            The main window connects to this to update tab titles and the
            dirty marker.
    """

    content_changed = pyqtSignal()

    _DUPLICATE_BG = QColor("#5b3232")
    _DUPLICATE_WINNER_BG = QColor("#5b5232")
    _PREVIEW_SECTION_RE = re.compile(r"^\s*\[([^\]]+)\]\s*$")
    _PREVIEW_KV_RE = re.compile(r"^\s*([^=;#]+?)\s*=")
    _JSON_SECTION_RE = re.compile(r'^  "([^"]+)":\s*\{')
    _JSON_KEY_RE = re.compile(r'^    "([^"]+)":')
    _XML_SECTION_RE = re.compile(r'<section\s+name="([^"]+)"')
    _XML_KEY_RE = re.compile(r'<entry\s+key="([^"]+)"')
    _YAML_SECTION_RE = re.compile(r"^(?:'([^']+)'|\"([^\"]+)\"|(\S[^:]*)):")
    _YAML_KEY_RE = re.compile(r"^  (?:'([^']+)'|\"([^\"]+)\"|(\S[^:]*)):")

    def __init__(
        self,
        language: Language,
        sort_mode: SortMode,
        export_format: ExportFormat,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Build the tab UI.

        Args:
            language: Initial UI language for child widgets.
            sort_mode: Initial sort mode applied to the preview and tree.
            export_format: Initial export format used for the preview pane.
            parent: Optional Qt parent.
        """
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._language = language
        self._sort_mode = sort_mode
        self._export_format = export_format
        self._doc: Optional[IniDocument] = None
        self._dirty = False
        self._syncing = False
        self._last_synced_section: Optional[str] = None
        self._last_tree_match: Optional[QTreeWidgetItem] = None
        self._undo_stack: list[IniDocument] = []
        self._redo_stack: list[IniDocument] = []
        self._header_pristine = True
        self._build_widgets()

    def _build_widgets(self) -> None:
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self._tree_label = QLabel("")
        self._tree_label.setStyleSheet("font-weight: bold; padding: 4px;")
        left_layout.addWidget(self._tree_label)

        self._tree = IniTreeWidget(self._language)
        self._tree.document_changed.connect(self._on_document_changed)
        self._tree.about_to_change.connect(self.push_undo_state)
        left_layout.addWidget(self._tree)
        self.addWidget(left_frame)

        self._right_tabs = QTabWidget()

        self._preview_edit = QPlainTextEdit()
        self._preview_edit.setReadOnly(True)
        self._preview_edit.setFont(QFont("Courier New", 10))
        self._highlighter = IniHighlighter(self._preview_edit.document())
        self._right_tabs.addTab(self._preview_edit, "")

        self._header_edit = QPlainTextEdit()
        self._header_edit.setFont(QFont("Courier New", 10))
        self._header_edit.textChanged.connect(self._on_header_changed)
        self._right_tabs.addTab(self._header_edit, "")

        self.addWidget(self._right_tabs)
        self.setSizes([420, 780])

        self._preview_edit.verticalScrollBar().valueChanged.connect(self._on_preview_scrolled)
        self._tree.verticalScrollBar().valueChanged.connect(self._on_tree_scrolled)
        self._tree.currentItemChanged.connect(self._on_tree_current_changed)

    @property
    def doc(self) -> Optional[IniDocument]:
        return self._doc

    @property
    def dirty(self) -> bool:
        return self._dirty

    @dirty.setter
    def dirty(self, value: bool) -> None:
        # Saving the document clears the merge highlight: the green tint
        # is meant to flag "added but not yet persisted" rows.
        if self._dirty and not value:
            self._tree.clear_merge_highlights()
        self._dirty = value

    @property
    def tree(self) -> IniTreeWidget:
        return self._tree

    @property
    def preview_edit(self) -> QPlainTextEdit:
        return self._preview_edit

    @property
    def sort_mode(self) -> SortMode:
        return self._sort_mode

    @property
    def export_format(self) -> ExportFormat:
        return self._export_format

    def set_language(self, language: Language) -> None:
        self._language = language
        self._tree.set_language(language)

    def set_sort_mode(self, mode: SortMode) -> None:
        self._sort_mode = mode
        if self._doc is not None:
            self._tree.set_sort_mode(mode)
            self._refresh_preview()

    def set_export_format(self, fmt: ExportFormat) -> None:
        self._export_format = fmt
        self._last_synced_section = None
        if self._doc is not None:
            self._refresh_preview()

    def set_labels(self, tree_label: str, preview_tab: str, header_tab: str, header_placeholder: str) -> None:
        self._tree_label.setText(tree_label)
        self._right_tabs.setTabText(0, preview_tab)
        self._right_tabs.setTabText(1, header_tab)
        self._header_edit.setPlaceholderText(header_placeholder)

    def push_undo_state(self) -> None:
        """Snapshot the current document onto the undo stack.

        Clears the redo stack and caps the undo stack at 100 entries.
        Called by widgets before they mutate the document.
        """
        if self._doc is None:
            return
        self._undo_stack.append(self._doc.clone())
        del self._redo_stack[:]
        if len(self._undo_stack) > 100:
            self._undo_stack.pop(0)

    def undo(self) -> None:
        """Restore the previous document snapshot, if any."""
        if not self._undo_stack or self._doc is None:
            return
        self._redo_stack.append(self._doc.clone())
        self._doc = self._undo_stack.pop()
        self._header_pristine = True
        # Undo swaps in a cloned document; the old id()s in the merge
        # highlight set would never match again, so drop them.
        self._tree.clear_merge_highlights()
        self.load_into_ui()
        self._dirty = True
        self.content_changed.emit()

    def redo(self) -> None:
        """Replay the most recently undone document snapshot, if any."""
        if not self._redo_stack or self._doc is None:
            return
        self._undo_stack.append(self._doc.clone())
        self._doc = self._redo_stack.pop()
        self._header_pristine = True
        self._tree.clear_merge_highlights()
        self.load_into_ui()
        self._dirty = True
        self.content_changed.emit()

    def load_document(self, doc: IniDocument) -> None:
        """Replace the current document and reset undo/redo state.

        Args:
            doc: New document to display. The tab takes ownership; no clone
                is made.
        """
        self._doc = doc
        self._dirty = False
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._header_pristine = True
        # Highlights from a previous document don't apply to the new one.
        self._tree.clear_merge_highlights()
        self.load_into_ui()
        # Auto-size the section/key and value columns so the user doesn't
        # have to drag splitters on every file open. Only fires here (initial
        # load); later refreshes from sort/format/undo keep the user's width.
        # Deferred so the tree's viewport has been laid out — auto_size_columns
        # uses viewport().width() to reserve room for the comment column.
        QTimer.singleShot(0, self._tree.auto_size_columns)

    def load_into_ui(self) -> None:
        if self._doc is None:
            return
        self._header_pristine = True
        self._tree.load_document(self._doc)
        self._tree.set_sort_mode(self._sort_mode)
        self._header_edit.blockSignals(True)
        self._header_edit.setPlainText("\n".join(self._doc.header_comments))
        self._header_edit.blockSignals(False)
        self._refresh_preview()

    def sync_doc_from_preview(self) -> None:
        """Re-parse the preview text and adopt it as the new document.

        Used after the user edits the preview pane (currently triggered by
        find/replace). Parse failures are swallowed silently so a transient
        invalid state during typing does not destroy data.
        """
        text = self._preview_edit.document().toPlainText()
        try:
            new_doc = IniParser.parse_string(text)
            new_doc.source_path = self._doc.source_path if self._doc else None
            self._doc = new_doc
            self._tree.load_document(self._doc)
            self._tree.set_sort_mode(self._sort_mode)
        except Exception:
            pass
        self._dirty = True
        self.content_changed.emit()

    def sync_tree_to_preview_match(self, cursor) -> None:
        line_no = cursor.blockNumber()
        lines = self._preview_edit.document().toPlainText().splitlines()

        located = self._locate_in_preview(lines, line_no)
        if located is None:
            return
        current_section_name, matched_key = located

        palette = QApplication.palette()
        highlight = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight)
        col_count = self._tree.columnCount()

        if self._last_tree_match is not None:
            if not sip.isdeleted(self._last_tree_match):
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

    _JSON_SECTION_RE = re.compile(r'^\s+"([^"]+)"\s*:\s*\{')
    _JSON_ENTRY_RE = re.compile(r'^\s+"([^"]+)"\s*:\s*(?!\{)')
    _JSON_SECTION_CLOSE_RE = re.compile(r'^\s+\}')
    _XML_SECTION_RE = re.compile(r'<section\s+[^>]*name="([^"]+)"')
    _XML_ENTRY_RE = re.compile(r'<entry\s+[^>]*key="([^"]+)"')
    _XML_SECTION_CLOSE_RE = re.compile(r'</section\s*>')
    _YAML_SECTION_RE = re.compile(r'^(["\']?)([^\s"\'][^:]*?)\1\s*:')
    _YAML_ENTRY_RE = re.compile(r'^\s+(["\']?)([^\s"\'][^:]*?)\1\s*:')

    def _locate_in_preview(
        self, lines: list[str], line_no: int,
    ) -> Optional[tuple[str, Optional[str]]]:
        fmt = self._export_format
        if fmt == ExportFormat.INI:
            return self._locate_in_ini(lines, line_no)
        if fmt == ExportFormat.JSON:
            return self._locate_in_json(lines, line_no)
        if fmt == ExportFormat.XML:
            return self._locate_in_xml(lines, line_no)
        if fmt == ExportFormat.YAML:
            return self._locate_in_yaml(lines, line_no)
        return None

    def _locate_in_ini(
        self, lines: list[str], line_no: int,
    ) -> Optional[tuple[str, Optional[str]]]:
        section: Optional[str] = None
        matched_key: Optional[str] = None
        for i, line in enumerate(lines[: line_no + 1]):
            stripped = line.strip()
            if stripped.startswith("[") and "]" in stripped:
                section = stripped[1 : stripped.index("]")]
                if i == line_no:
                    matched_key = None
            elif (
                "=" in stripped
                and not stripped.startswith(";")
                and not stripped.startswith("#")
                and i == line_no
            ):
                matched_key = stripped.split("=", 1)[0].strip()
        return (section, matched_key) if section is not None else None

    def _locate_in_json(
        self, lines: list[str], line_no: int,
    ) -> Optional[tuple[str, Optional[str]]]:
        section: Optional[str] = None
        matched_key: Optional[str] = None
        for i, line in enumerate(lines[: line_no + 1]):
            m = self._JSON_SECTION_RE.match(line)
            if m:
                section = m.group(1)
                if i == line_no:
                    matched_key = None
                continue
            if i == line_no:
                m = self._JSON_ENTRY_RE.match(line)
                if m:
                    matched_key = m.group(1)
                continue
            if self._JSON_SECTION_CLOSE_RE.match(line):
                section = None
        return (section, matched_key) if section is not None else None

    def _locate_in_xml(
        self, lines: list[str], line_no: int,
    ) -> Optional[tuple[str, Optional[str]]]:
        section: Optional[str] = None
        matched_key: Optional[str] = None
        for i, line in enumerate(lines[: line_no + 1]):
            m = self._XML_SECTION_RE.search(line)
            if m:
                section = m.group(1)
                if i == line_no:
                    matched_key = None
                continue
            if i == line_no:
                m = self._XML_ENTRY_RE.search(line)
                if m:
                    matched_key = m.group(1)
                continue
            if self._XML_SECTION_CLOSE_RE.search(line):
                section = None
        return (section, matched_key) if section is not None else None

    def _locate_in_yaml(
        self, lines: list[str], line_no: int,
    ) -> Optional[tuple[str, Optional[str]]]:
        section: Optional[str] = None
        matched_key: Optional[str] = None
        for i, line in enumerate(lines[: line_no + 1]):
            if not line.strip():
                continue
            if line[0] not in (" ", "\t"):
                m = self._YAML_SECTION_RE.match(line)
                if m:
                    section = m.group(2).strip()
                    if i == line_no:
                        matched_key = None
            else:
                if i == line_no:
                    m = self._YAML_ENTRY_RE.match(line)
                    if m:
                        matched_key = m.group(2).strip()
        return (section, matched_key) if section is not None else None

    def _refresh_preview(self) -> None:
        if self._doc is None:
            return
        doc = self._doc.sorted_copy(self._sort_mode)
        try:
            text = doc.export(self._export_format)
        except Exception as exc:
            text = f"[Render error: {exc}]"
        # setPlainText resets the scrollbar to 0 and can transiently report
        # value == maximum (both 0 before layout), which would trigger the
        # scroll-sync to send the tree to its bottom. Suppress sync, replace
        # the text, then restore the user's vertical position.
        preview_sb = self._preview_edit.verticalScrollBar()
        saved_scroll = preview_sb.value()
        was_syncing = self._syncing
        self._syncing = True
        try:
            self._preview_edit.setPlainText(text)
            self._apply_duplicate_highlights()
            preview_sb.setValue(min(saved_scroll, preview_sb.maximum()))
        finally:
            self._syncing = was_syncing
        self._preview_edit.repaint()

    def _apply_duplicate_highlights(self) -> None:
        """Underlay duplicate section/key lines in the preview with a tint.

        Highlighting is recomputed from the rendered text, not the parser's
        ``doc.duplicates`` list, so it stays correct after in-memory edits.
        Only the INI export format produces source-level lines worth marking;
        JSON/XML/YAML use dicts and have no duplicates by definition.
        """
        if self._export_format != ExportFormat.INI:
            self._preview_edit.setExtraSelections([])
            return
        text = self._preview_edit.document().toPlainText()

        # Pass 1: collect line numbers grouped by section name and (section, key).
        section_lines_by_name: dict[str, list[int]] = {}
        entry_lines_by_section_key: dict[tuple[str, str], list[int]] = {}
        current_section: Optional[str] = None
        for line_no, line in enumerate(text.splitlines()):
            m = self._PREVIEW_SECTION_RE.match(line)
            if m:
                sec_name = m.group(1).strip()
                current_section = sec_name
                section_lines_by_name.setdefault(sec_name, []).append(line_no)
                continue
            stripped = line.lstrip()
            if not stripped or stripped[0] in ";#" or current_section is None:
                continue
            kv = self._PREVIEW_KV_RE.match(line)
            if kv is None:
                continue
            key = kv.group(1).strip()
            entry_lines_by_section_key.setdefault(
                (current_section, key), []
            ).append(line_no)

        # Pass 2: for each name with 2+ occurrences, paint the first line
        # yellow (the entry Win32 actually returns) and every subsequent line
        # red (shadowed). Names that appear once get no highlight.
        selections: list[QTextEdit.ExtraSelection] = []
        for line_groups in (
            section_lines_by_name.values(),
            entry_lines_by_section_key.values(),
        ):
            for lines in line_groups:
                if len(lines) < 2:
                    continue
                self._add_line_selection(selections, lines[0], self._DUPLICATE_WINNER_BG)
                for line_no in lines[1:]:
                    self._add_line_selection(selections, line_no, self._DUPLICATE_BG)
        self._preview_edit.setExtraSelections(selections)

    def _add_line_selection(
        self,
        selections: list[QTextEdit.ExtraSelection],
        line_no: int,
        color: QColor,
    ) -> None:
        block = self._preview_edit.document().findBlockByLineNumber(line_no)
        if not block.isValid():
            return
        cursor = QTextCursor(block)
        sel = QTextEdit.ExtraSelection()
        sel.cursor = cursor
        fmt = QTextCharFormat()
        fmt.setBackground(color)
        fmt.setProperty(QTextFormat.Property.FullWidthSelection, True)
        sel.format = fmt
        selections.append(sel)

    def _on_document_changed(self) -> None:
        self._dirty = True
        self._refresh_preview()
        self.content_changed.emit()

    def _on_header_changed(self) -> None:
        if self._doc is None:
            return
        if self._header_pristine:
            self.push_undo_state()
            self._header_pristine = False
        raw = self._header_edit.toPlainText()
        self._doc.header_comments = raw.splitlines() if raw.strip() else []
        self._dirty = True
        self._refresh_preview()
        self.content_changed.emit()

    def _on_preview_scrolled(self) -> None:
        if self._syncing or self._doc is None:
            return
        preview_sb = self._preview_edit.verticalScrollBar()
        if preview_sb.value() == preview_sb.maximum():
            self._syncing = True
            tree_sb = self._tree.verticalScrollBar()
            tree_sb.setValue(tree_sb.maximum())
            self._syncing = False
            return
        current_section_name = self._section_at_preview_top()
        if current_section_name is None or current_section_name == self._last_synced_section:
            return
        self._last_synced_section = current_section_name
        for idx in range(self._tree.topLevelItemCount()):
            sec_item = self._tree.topLevelItem(idx)
            sec_data = sec_item.data(0, Qt.ItemDataRole.UserRole)
            if hasattr(sec_data, "name") and sec_data.name == current_section_name:
                self._syncing = True
                self._tree.scrollToItem(sec_item, QAbstractItemView.ScrollHint.PositionAtTop)
                self._syncing = False
                break

    def _section_at_preview_top(self) -> Optional[str]:
        """Return the name of the section currently visible at the top of the preview."""
        line_no = self._preview_edit.firstVisibleBlock().blockNumber()
        lines = self._preview_edit.document().toPlainText().splitlines()
        fmt = self._export_format
        for i in range(min(line_no, len(lines) - 1), -1, -1):
            line = lines[i]
            if fmt == ExportFormat.INI:
                stripped = line.strip()
                if stripped.startswith("[") and "]" in stripped:
                    return stripped[1 : stripped.index("]")]
            elif fmt == ExportFormat.JSON:
                m = self._JSON_SECTION_RE.match(line)
                if m:
                    return m.group(1)
            elif fmt == ExportFormat.XML:
                m = self._XML_SECTION_RE.search(line)
                if m:
                    return m.group(1)
            elif fmt == ExportFormat.YAML:
                m = self._YAML_SECTION_RE.match(line)
                if m:
                    return next(g for g in m.groups() if g is not None)
        return None

    def _find_in_preview(self, section_name: str, key: Optional[str]) -> Optional[int]:
        """Find the line number of ``section_name`` (or ``key`` inside it) in the preview."""
        lines = self._preview_edit.document().toPlainText().splitlines()
        fmt = self._export_format
        in_section = False
        for i, line in enumerate(lines):
            if fmt == ExportFormat.INI:
                stripped = line.strip()
                if stripped.startswith("[") and "]" in stripped:
                    name = stripped[1 : stripped.index("]")]
                    if name == section_name:
                        if key is None:
                            return i
                        in_section = True
                    else:
                        in_section = False
                elif (
                    in_section
                    and key is not None
                    and "=" in stripped
                    and not stripped.startswith(";")
                    and not stripped.startswith("#")
                    and stripped.split("=", 1)[0].strip() == key
                ):
                    return i
            elif fmt == ExportFormat.JSON:
                m = self._JSON_SECTION_RE.match(line)
                if m:
                    if m.group(1) == section_name:
                        if key is None:
                            return i
                        in_section = True
                    else:
                        in_section = False
                elif in_section and key is not None:
                    m2 = self._JSON_KEY_RE.match(line)
                    if m2 and m2.group(1) == key:
                        return i
            elif fmt == ExportFormat.XML:
                m = self._XML_SECTION_RE.search(line)
                if m:
                    if m.group(1) == section_name:
                        if key is None:
                            return i
                        in_section = True
                    else:
                        in_section = False
                elif in_section and key is not None:
                    m2 = self._XML_KEY_RE.search(line)
                    if m2 and m2.group(1) == key:
                        return i
            elif fmt == ExportFormat.YAML:
                m = self._YAML_SECTION_RE.match(line)
                if m:
                    name = next(g for g in m.groups() if g is not None)
                    if name == section_name:
                        if key is None:
                            return i
                        in_section = True
                    else:
                        in_section = False
                elif in_section and key is not None:
                    m2 = self._YAML_KEY_RE.match(line)
                    if m2:
                        kname = next(g for g in m2.groups() if g is not None)
                        if kname == key:
                            return i
        return None

    def _scroll_preview_to_item(self, item: QTreeWidgetItem) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data is None:
            return
        if hasattr(data, "name"):
            section_name: str = data.name
            key: Optional[str] = None
        elif hasattr(data, "key"):
            parent = item.parent()
            if parent is None:
                return
            sec_data = parent.data(0, Qt.ItemDataRole.UserRole)
            if not hasattr(sec_data, "name"):
                return
            section_name = sec_data.name
            key = data.key
        else:
            return
        target_line = self._find_in_preview(section_name, key)
        if target_line is None:
            return
        self._syncing = True
        self._last_synced_section = section_name
        self._preview_edit.verticalScrollBar().setValue(target_line)
        self._syncing = False

    def _on_tree_scrolled(self) -> None:
        if self._syncing or self._doc is None:
            return
        tree_sb = self._tree.verticalScrollBar()
        if tree_sb.value() == tree_sb.maximum():
            self._syncing = True
            preview_sb = self._preview_edit.verticalScrollBar()
            preview_sb.setValue(preview_sb.maximum())
            self._syncing = False
            return
        item = self._tree.itemAt(0, 0)
        if item is None:
            return
        self._scroll_preview_to_item(item)

    def _on_tree_current_changed(
        self, item: Optional[QTreeWidgetItem], _: Optional[QTreeWidgetItem]
    ) -> None:
        if self._syncing or item is None or self._doc is None:
            return
        self._scroll_preview_to_item(item)
