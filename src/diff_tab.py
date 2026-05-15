"""Side-by-side comparison view for two open INI documents.

Wraps :class:`~ini_diff.IniDiff` results in a sortable, filterable tree with
status badges (added / removed / modified / unchanged) and a Find bar. The
view auto-refreshes when either source document is mutated.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)

try:
    from src.ini_parser import SortMode
except ModuleNotFoundError:
    from ini_parser import SortMode  # type: ignore[no-redef]

try:
    from src.ini_diff import DiffStatus, DuplicateRole, IniDiff
except ModuleNotFoundError:
    from ini_diff import DiffStatus, DuplicateRole, IniDiff  # type: ignore[no-redef]

try:
    from src.translations import Language, translate
except ModuleNotFoundError:
    from translations import Language, translate  # type: ignore[no-redef]

if TYPE_CHECKING:
    from .document_tab import DocumentTab


class DiffTab(QWidget):
    """Compares two :class:`~document_tab.DocumentTab` documents in a tree view.

    Connects to ``content_changed`` of both source tabs so the diff stays
    live as the user edits either side. Provides per-status colouring,
    a "differences only" filter, a sort selector, and an embedded find bar.
    """

    _BG_ADDED    = QColor("#1a3520")
    _BG_REMOVED  = QColor("#3a1a22")
    _BG_MODIFIED = QColor("#2e2a10")
    _FG_ADDED    = QColor("#a6e3a1")
    _FG_REMOVED  = QColor("#f38ba8")
    _FG_MODIFIED = QColor("#f9e2af")


    def __init__(
        self,
        tab_a: "DocumentTab",
        tab_b: "DocumentTab",
        language: Language,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Wire up the view and trigger an initial diff.

        Args:
            tab_a: Left-hand document tab.
            tab_b: Right-hand document tab.
            language: Initial UI language.
            parent: Optional Qt parent.
        """
        super().__init__(parent)
        self._tab_a = tab_a
        self._tab_b = tab_b
        self._language = language
        self._only_diffs = False
        self._sort_mode = SortMode.NONE
        self._find_matches: list[QTreeWidgetItem] = []
        self._find_idx = -1
        self._build_widgets()
        self._tab_a.content_changed.connect(self.refresh)
        self._tab_b.content_changed.connect(self.refresh)
        self.refresh()

    def _build_widgets(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        header = QHBoxLayout()
        self._label_a = QLabel()
        self._label_a.setStyleSheet("font-weight: bold; color: #89b4fa; padding: 2px 0;")
        self._label_b = QLabel()
        self._label_b.setStyleSheet("font-weight: bold; color: #a6e3a1; padding: 2px 0;")
        header.addWidget(self._label_a)
        header.addStretch()
        header.addWidget(self._label_b)
        layout.addLayout(header)

        opts = QHBoxLayout()
        self._only_diffs_check = QCheckBox()
        self._only_diffs_check.setChecked(False)
        self._only_diffs_check.stateChanged.connect(self._on_toggle_filter)
        opts.addWidget(self._only_diffs_check)
        opts.addSpacing(16)
        self._sort_label = QLabel()
        self._sort_label.setStyleSheet("color: #a6adc8;")
        opts.addWidget(self._sort_label)
        self._sort_combo = QComboBox()
        self._sort_combo.setFixedWidth(220)
        self._sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        opts.addWidget(self._sort_combo)
        opts.addStretch()
        self._summary_label = QLabel()
        self._summary_label.setStyleSheet("color: #a6adc8; font-size: 12px;")
        opts.addWidget(self._summary_label)
        layout.addLayout(opts)

        self._tree = QTreeWidget()
        self._tree.setColumnCount(5)
        self._tree.setAlternatingRowColors(False)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        hdr = self._tree.header()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self._tree)

        self._find_bar_widget = QWidget()
        self._find_bar_widget.setVisible(False)
        find_layout = QHBoxLayout(self._find_bar_widget)
        find_layout.setContentsMargins(4, 2, 4, 2)
        find_layout.setSpacing(4)

        self._find_label = QLabel()
        self._find_edit = QLineEdit()
        self._find_edit.setMinimumWidth(180)
        self._find_edit.returnPressed.connect(lambda: self._do_find(forward=True))
        self._find_edit.textChanged.connect(self._reset_find)

        _btn_font = QFont()
        _btn_font.setPointSize(15)
        self._find_prev_btn = QPushButton("◀")
        self._find_prev_btn.setFont(_btn_font)
        self._find_prev_btn.setFixedSize(38, 28)
        self._find_prev_btn.clicked.connect(lambda: self._do_find(forward=False))
        self._find_next_btn = QPushButton("▶")
        self._find_next_btn.setFont(_btn_font)
        self._find_next_btn.setFixedSize(38, 28)
        self._find_next_btn.clicked.connect(lambda: self._do_find(forward=True))
        self._find_case_check = QCheckBox()
        self._find_case_check.stateChanged.connect(self._reset_find)
        self._find_status = QLabel()
        self._find_status.setMinimumWidth(150)
        self._find_status.setStyleSheet("color: #a6adc8;")
        self._find_close_btn = QPushButton("✖")
        self._find_close_btn.setFont(_btn_font)
        self._find_close_btn.setFixedSize(38, 28)
        self._find_close_btn.clicked.connect(self._find_bar_widget.hide)

        find_layout.addWidget(self._find_label)
        find_layout.addWidget(self._find_edit)
        find_layout.addWidget(self._find_prev_btn)
        find_layout.addWidget(self._find_next_btn)
        find_layout.addSpacing(8)
        find_layout.addWidget(self._find_case_check)
        find_layout.addSpacing(8)
        find_layout.addWidget(self._find_status, 1)
        find_layout.addWidget(self._find_close_btn)
        layout.addWidget(self._find_bar_widget)

        self._refresh_static_labels()

    def _refresh_static_labels(self) -> None:
        self._label_a.setText(f"A: {self._doc_name(self._tab_a)}")
        self._label_b.setText(f"B: {self._doc_name(self._tab_b)}")
        self._only_diffs_check.setText(translate(self._language, "diff_only_diffs"))
        self._sort_label.setText(translate(self._language, "sort_group"))
        sort_modes = [SortMode.NONE, SortMode.SECTIONS_ALPHA, SortMode.KEYS_ALPHA, SortMode.SECTIONS_AND_KEYS_ALPHA]
        self._sort_combo.blockSignals(True)
        self._sort_combo.clear()
        self._sort_combo.addItems([
            translate(self._language, "sort_none"),
            translate(self._language, "sort_sections"),
            translate(self._language, "sort_keys"),
            translate(self._language, "sort_both"),
        ])
        self._sort_combo.setCurrentIndex(sort_modes.index(self._sort_mode))
        self._sort_combo.blockSignals(False)
        self._tree.setHeaderLabels([
            translate(self._language, "diff_col_key"),
            self._doc_name(self._tab_a),
            self._doc_name(self._tab_b),
            "",
            translate(self._language, "diff_col_role"),
        ])
        # Center-align the Win32 column header to match the centered symbols
        self._tree.headerItem().setTextAlignment(4, Qt.AlignmentFlag.AlignCenter)
        self._find_label.setText(translate(self._language, "find_label"))
        self._find_case_check.setText(translate(self._language, "find_case_sensitive"))
        self._find_prev_btn.setToolTip(translate(self._language, "find_prev"))
        self._find_next_btn.setToolTip(translate(self._language, "find_next"))

    def _doc_name(self, tab: "DocumentTab") -> str:
        try:
            doc = tab.doc
            if doc and doc.source_path:
                return doc.source_path.name
        except RuntimeError:
            pass
        return translate(self._language, "tab_untitled")

    def set_language(self, language: Language) -> None:
        self._language = language
        self._refresh_static_labels()
        self.refresh()

    def show_find(self) -> None:
        """Reveal the embedded find bar and focus the search field."""
        self._find_bar_widget.setVisible(True)
        self._find_edit.setFocus()
        self._find_edit.selectAll()

    def refresh(self) -> None:
        """Recompute the diff from the two source tabs and rebuild the tree."""
        try:
            doc_a = self._tab_a.doc
            doc_b = self._tab_b.doc
        except RuntimeError:
            return
        if doc_a is None or doc_b is None:
            self._tree.clear()
            return

        if self._sort_mode != SortMode.NONE:
            doc_a = doc_a.sorted_copy(self._sort_mode)
            doc_b = doc_b.sorted_copy(self._sort_mode)

        diff = IniDiff.compare(doc_a, doc_b)

        # Post-sort the merged diff so that A-only and B-only / B-excess
        # rows interleave alphabetically instead of being concatenated.
        # Python's sort is stable, so within a duplicated name the
        # WINNER row stays before its SHADOWED siblings.
        if self._sort_mode in (SortMode.SECTIONS_ALPHA, SortMode.SECTIONS_AND_KEYS_ALPHA):
            diff.sections.sort(key=lambda s: s.name.lower())
        if self._sort_mode in (SortMode.KEYS_ALPHA, SortMode.SECTIONS_AND_KEYS_ALPHA):
            for sec in diff.sections:
                sec.entries.sort(key=lambda e: e.key.lower())
        self._refresh_static_labels()
        self._tree.clear()
        self._find_matches = []
        self._find_idx = -1

        for sec_diff in diff.sections:
            if self._only_diffs and sec_diff.status == DiffStatus.UNCHANGED:
                continue

            sec_item = QTreeWidgetItem(self._tree)
            sec_item.setText(0, f"[{sec_diff.name}]")
            sec_item.setText(3, self._status_symbol(sec_diff.status))
            self._colorize(sec_item, sec_diff.status, cols=range(5))
            self._apply_role(sec_item, sec_diff.duplicate_role, is_section=True)

            for ed in sec_diff.entries:
                if self._only_diffs and ed.status == DiffStatus.UNCHANGED:
                    continue
                row = QTreeWidgetItem(sec_item)
                row.setText(0, ed.key)
                row.setText(1, ed.value_a or "")
                row.setText(2, ed.value_b or "")
                row.setText(3, self._status_symbol(ed.status))
                self._colorize(row, ed.status, cols=range(5))
                self._apply_role(row, ed.duplicate_role, is_section=False)

            sec_item.setExpanded(True)

        self._summary_label.setText(
            translate(
                self._language,
                "diff_summary",
                modified=diff.count_modified(),
                added=diff.count_added(),
                removed=diff.count_removed(),
                unchanged=diff.count_unchanged(),
            )
        )

    def _on_toggle_filter(self) -> None:
        self._only_diffs = self._only_diffs_check.isChecked()
        self.refresh()

    def _on_sort_changed(self, idx: int) -> None:
        modes = [SortMode.NONE, SortMode.SECTIONS_ALPHA, SortMode.KEYS_ALPHA, SortMode.SECTIONS_AND_KEYS_ALPHA]
        self._sort_mode = modes[idx]
        self.refresh()

    def _reset_find(self) -> None:
        self._find_matches = []
        self._find_idx = -1
        self._find_status.setText("")

    def _collect_all_items(self) -> list[QTreeWidgetItem]:
        items: list[QTreeWidgetItem] = []
        for i in range(self._tree.topLevelItemCount()):
            sec = self._tree.topLevelItem(i)
            items.append(sec)
            for j in range(sec.childCount()):
                items.append(sec.child(j))
        return items

    def _do_find(self, forward: bool) -> None:
        query = self._find_edit.text()
        if not query:
            self._find_status.setText("")
            return
        case = self._find_case_check.isChecked()
        q = query if case else query.lower()

        if not self._find_matches:
            self._find_matches = []
            for item in self._collect_all_items():
                texts = [item.text(c) for c in range(self._tree.columnCount())]
                haystack = " ".join(texts) if case else " ".join(t.lower() for t in texts)
                if q in haystack:
                    self._find_matches.append(item)
            self._find_idx = -1

        if not self._find_matches:
            self._find_status.setText(translate(self._language, "find_not_found"))
            return

        self._find_idx = (self._find_idx + (1 if forward else -1)) % len(self._find_matches)
        item = self._find_matches[self._find_idx]
        self._tree.setCurrentItem(item)
        self._tree.scrollToItem(item, QAbstractItemView.ScrollHint.PositionAtTop)
        total = len(self._find_matches)
        self._find_status.setText(
            f"{translate(self._language, 'find_count', count=total)}"
            f" ({self._find_idx + 1}/{total})"
        )

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() == Qt.Key.Key_Escape and self._find_bar_widget.isVisible():
            self._find_bar_widget.hide()
        else:
            super().keyPressEvent(event)

    @staticmethod
    def _status_symbol(status: DiffStatus) -> str:
        return {
            DiffStatus.ADDED:     "＋",
            DiffStatus.REMOVED:   "－",
            DiffStatus.MODIFIED:  "≠",
            DiffStatus.UNCHANGED: "＝",
        }[status]

    def _colorize(self, item: QTreeWidgetItem, status: DiffStatus, cols) -> None:
        if status == DiffStatus.UNCHANGED:
            return
        bg, fg = {
            DiffStatus.ADDED:    (self._BG_ADDED,    self._FG_ADDED),
            DiffStatus.REMOVED:  (self._BG_REMOVED,  self._FG_REMOVED),
            DiffStatus.MODIFIED: (self._BG_MODIFIED, self._FG_MODIFIED),
        }[status]
        bg_brush = QBrush(bg)
        fg_brush = QBrush(fg)
        for c in cols:
            item.setBackground(c, bg_brush)
            item.setForeground(c, fg_brush)

    # Symbols shown in the role column. Kept short so the column stays
    # narrow; the tooltip explains the meaning.
    _ROLE_SYMBOL_WINNER   = "★"
    _ROLE_SYMBOL_SHADOWED = "↓"

    def _apply_role(
        self, item: QTreeWidgetItem, role: DuplicateRole, *, is_section: bool,
    ) -> None:
        """Render a row's Win32 duplicate role via font and a dedicated column.

        Avoids background tinting so it doesn't collide with the status
        colours (REMOVED is red, MODIFIED is yellow — same hues we'd
        otherwise want for shadowed / winner). Instead:

        - section rows are always bold; if SHADOWED we add italics
        - entry rows: WINNER → bold, SHADOWED → italic, NONE → unchanged
        - column 4 carries a ★ (winner) or ↓ (shadowed) symbol
        - the appropriate tooltip is set on every column of the row
        """
        # Sections are intrinsically bold (section header convention);
        # entries inherit bold/italic only when the role demands it.
        bold = is_section or role == DuplicateRole.WINNER
        italic = role == DuplicateRole.SHADOWED
        font = QFont()
        font.setBold(bold)
        font.setItalic(italic)
        col_count = self._tree.columnCount()
        for c in range(col_count):
            item.setFont(c, font)

        if role == DuplicateRole.NONE:
            return

        symbol = (
            self._ROLE_SYMBOL_WINNER
            if role == DuplicateRole.WINNER
            else self._ROLE_SYMBOL_SHADOWED
        )
        tooltip = translate(
            self._language,
            "duplicate_winner_tooltip" if role == DuplicateRole.WINNER
            else "duplicate_tooltip",
        )
        item.setText(4, symbol)
        item.setTextAlignment(4, Qt.AlignmentFlag.AlignCenter)
        for c in range(col_count):
            item.setToolTip(c, tooltip)
