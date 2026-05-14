"""
document_tab.py – One self-contained editor pane per open INI file.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QFont, QPalette
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QFrame, QLabel, QPlainTextEdit,
    QSplitter, QTabWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
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
    """Holds one IniDocument with its own tree, preview, and header editor."""

    content_changed = pyqtSignal()

    def __init__(
        self,
        language: Language,
        sort_mode: SortMode,
        export_format: ExportFormat,
        parent: Optional[QWidget] = None,
    ) -> None:
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
        if self._doc is not None:
            self._refresh_preview()

    def set_labels(self, tree_label: str, preview_tab: str, header_tab: str, header_placeholder: str) -> None:
        self._tree_label.setText(tree_label)
        self._right_tabs.setTabText(0, preview_tab)
        self._right_tabs.setTabText(1, header_tab)
        self._header_edit.setPlaceholderText(header_placeholder)

    def push_undo_state(self) -> None:
        if self._doc is None:
            return
        self._undo_stack.append(self._doc.clone())
        del self._redo_stack[:]
        if len(self._undo_stack) > 100:
            self._undo_stack.pop(0)

    def undo(self) -> None:
        if not self._undo_stack or self._doc is None:
            return
        self._redo_stack.append(self._doc.clone())
        self._doc = self._undo_stack.pop()
        self._header_pristine = True
        self.load_into_ui()
        self._dirty = True
        self.content_changed.emit()

    def redo(self) -> None:
        if not self._redo_stack or self._doc is None:
            return
        self._undo_stack.append(self._doc.clone())
        self._doc = self._redo_stack.pop()
        self._header_pristine = True
        self.load_into_ui()
        self._dirty = True
        self.content_changed.emit()

    def load_document(self, doc: IniDocument) -> None:
        self._doc = doc
        self._dirty = False
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._header_pristine = True
        self.load_into_ui()

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

        palette = QApplication.palette()
        highlight = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight)
        col_count = self._tree.columnCount()

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

    def _refresh_preview(self) -> None:
        if self._doc is None:
            return
        doc = self._doc.sorted_copy(self._sort_mode)
        try:
            text = doc.export(self._export_format)
        except Exception as exc:
            text = f"[Render error: {exc}]"
        self._preview_edit.setPlainText(text)
        self._preview_edit.repaint()

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
        if self._syncing or self._export_format != ExportFormat.INI or self._doc is None:
            return
        line_no = self._preview_edit.firstVisibleBlock().blockNumber()
        lines = self._preview_edit.document().toPlainText().splitlines()
        current_section_name: Optional[str] = None
        for i in range(min(line_no, len(lines) - 1), -1, -1):
            stripped = lines[i].strip()
            if stripped.startswith("[") and "]" in stripped:
                current_section_name = stripped[1 : stripped.index("]")]
                break
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
        lines = self._preview_edit.document().toPlainText().splitlines()
        target_line: Optional[int] = None
        current_section: Optional[str] = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("[") and "]" in stripped:
                current_section = stripped[1 : stripped.index("]")]
                if current_section == section_name and key is None:
                    target_line = i
                    break
            elif (
                current_section == section_name
                and key is not None
                and "=" in stripped
                and not stripped.startswith(";")
                and not stripped.startswith("#")
            ):
                if stripped.split("=", 1)[0].strip() == key:
                    target_line = i
                    break
        if target_line is None:
            return
        self._syncing = True
        self._last_synced_section = section_name
        self._preview_edit.verticalScrollBar().setValue(target_line)
        self._syncing = False

    def _on_tree_scrolled(self) -> None:
        if self._syncing or self._export_format != ExportFormat.INI or self._doc is None:
            return
        item = self._tree.itemAt(0, 0)
        if item is None:
            return
        self._scroll_preview_to_item(item)

    def _on_tree_current_changed(
        self, item: Optional[QTreeWidgetItem], _: Optional[QTreeWidgetItem]
    ) -> None:
        if self._syncing or self._export_format != ExportFormat.INI or item is None or self._doc is None:
            return
        self._scroll_preview_to_item(item)
