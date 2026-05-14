"""PyQt6 main window for the INI Editor application.

Hosts the menu bar, toolbar, multi-tab file area, status bar, find bar, and
all top-level actions. Each open file is shown in its own
:class:`~document_tab.DocumentTab`; document comparison opens in a
:class:`~diff_tab.DiffTab`.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import (
    QAction, QDragEnterEvent, QDropEvent, QIcon, QKeySequence, QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QDialog, QFileDialog, QGroupBox, QHBoxLayout,
    QLabel, QSizePolicy, QMainWindow, QMessageBox, QPlainTextEdit,
    QPushButton, QTabWidget, QToolBar, QVBoxLayout, QWidget,
)

try:
    from src.ini_parser import (
        ExportFormat, IniDocument, IniParser, SortMode,
    )
except ModuleNotFoundError:
    from ini_parser import (
        ExportFormat, IniDocument, IniParser, SortMode,
    )

try:
    from src._version import __version__ as _APP_VERSION
except ModuleNotFoundError:
    try:
        from _version import __version__ as _APP_VERSION  # type: ignore[no-redef]
    except ModuleNotFoundError:
        _APP_VERSION = "dev"

try:
    from src.translations import Language, translate
except ModuleNotFoundError:
    from translations import Language, translate  # type: ignore[no-redef]

try:
    from src.find_bar import FindBar
except ModuleNotFoundError:
    from find_bar import FindBar  # type: ignore[no-redef]

try:
    from src.document_tab import DocumentTab
except ModuleNotFoundError:
    from document_tab import DocumentTab  # type: ignore[no-redef]

try:
    from src.diff_tab import DiffTab
except ModuleNotFoundError:
    from diff_tab import DiffTab  # type: ignore[no-redef]

try:
    from src.dialogs import DiffSelectDialog
except ModuleNotFoundError:
    from dialogs import DiffSelectDialog  # type: ignore[no-redef]


DARK_STYLESHEET = """
    QMainWindow, QDialog, QWidget {
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
    QLabel { background-color: transparent; color: #cdd6f4; }
    QComboBox {
        background-color: #313244; border: 1px solid #45475a;
        color: #cdd6f4;
        border-radius: 4px; padding: 4px 8px; min-width: 200px;
    }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background-color: #313244; color: #cdd6f4;
        selection-background-color: #45475a;
    }
    QPushButton {
        background-color: #89b4fa; color: #1e1e2e;
        border: none; border-radius: 4px; padding: 5px 14px; font-weight: bold;
        min-width: 72px;
    }
    QPushButton:hover { background-color: #b4c7fa; }
    QPushButton:pressed { background-color: #6b8fcc; }
    QPushButton:disabled { background-color: #45475a; color: #6c7086; }
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
        background-color: #181825; color: #cdd6f4;
        border: 1px solid #45475a;
        border-radius: 4px; padding: 4px;
        selection-background-color: #45475a;
    }
    QTabWidget::pane { border: 1px solid #45475a; border-radius: 4px; }
    QTabBar::tab {
        background-color: #313244; border: 1px solid #45475a;
        padding: 6px 14px; border-bottom: none;
    }
    QTabBar::tab:selected { background-color: #45475a; }
    QTabBar::close-button { subcontrol-position: right; }
    QTabBar::close-button:hover { background-color: #f38ba8; border-radius: 2px; }
    QStatusBar { background-color: #181825; border-top: 1px solid #45475a; }
    QFrame { border: none; }
    QLineEdit {
        background-color: #313244; color: #cdd6f4;
        border: 1px solid #45475a;
        border-radius: 4px; padding: 4px 8px;
        selection-background-color: #45475a;
    }
    QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus {
        border: 1px solid #89b4fa;
    }
    QSplitter::handle { background-color: #45475a; width: 2px; }
    QMessageBox { background-color: #1e1e2e; }
    QMessageBox QLabel { color: #cdd6f4; }
    QInputDialog { background-color: #1e1e2e; }
    QInputDialog QLabel { color: #cdd6f4; }
    QDialogButtonBox { button-layout: 0; }
    QScrollBar:vertical {
        background: #181825; width: 12px; margin: 0;
    }
    QScrollBar::handle:vertical {
        background: #45475a; border-radius: 4px; min-height: 24px;
    }
    QScrollBar::handle:vertical:hover { background: #585b70; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar:horizontal {
        background: #181825; height: 12px; margin: 0;
    }
    QScrollBar::handle:horizontal {
        background: #45475a; border-radius: 4px; min-width: 24px;
    }
    QScrollBar::handle:horizontal:hover { background: #585b70; }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
"""


class MainWindow(QMainWindow):
    """Top-level application window.

    Manages the bilingual UI, the tab area containing one
    :class:`~document_tab.DocumentTab` per open file, file I/O actions,
    export, find/replace, and the side-by-side diff view.

    Attributes:
        APP_NAME: Application name shown in the title bar and About dialog.
    """

    APP_NAME = "ini-file-editor"

    def __init__(self) -> None:
        """Construct the main window and open one empty document tab."""
        super().__init__()
        self._current_sort = SortMode.NONE
        self._current_format = ExportFormat.INI
        self._language = Language.EN
        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._apply_dark_theme()

        if hasattr(sys, '_MEIPASS'):
            icon_path = Path(sys._MEIPASS) / "assets" / "icon.ico"
        else:
            icon_path = Path(__file__).resolve().parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._update_translations()
        self.resize(1200, 750)
        self.statusBar().showMessage(self._t("status_ready"))
        self.setAcceptDrops(True)

    def _t(self, key: str, **kwargs: object) -> str:
        return translate(self._language, key, **kwargs)

    def _current_tab(self) -> Optional[DocumentTab]:
        w = self._file_tabs.currentWidget()
        return w if isinstance(w, DocumentTab) else None

    def _new_tab(self, doc: Optional[IniDocument] = None) -> DocumentTab:
        tab = DocumentTab(self._language, self._current_sort, self._current_format)
        tab.content_changed.connect(lambda: self._on_tab_content_changed(tab))
        tab.set_labels(
            self._t("tree_label"),
            self._t("preview_tab"),
            self._t("header_tab"),
            self._t("header_placeholder"),
        )
        title = self._t("tab_untitled")
        idx = self._file_tabs.addTab(tab, title)
        self._file_tabs.setCurrentIndex(idx)
        if doc is not None:
            tab.load_document(doc)
        return tab

    def _close_tab(self, idx: int) -> None:
        tab = self._file_tabs.widget(idx)
        if isinstance(tab, DocumentTab) and tab.dirty:
            reply = QMessageBox.question(
                self,
                self._t("confirm_discard_title"),
                self._t("confirm_discard_text"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self._file_tabs.removeTab(idx)
        if self._file_tabs.count() == 0:
            self._new_tab(IniDocument())

    def _close_current_tab(self) -> None:
        idx = self._file_tabs.currentIndex()
        if idx >= 0:
            self._close_tab(idx)

    def _set_tab_title(self, idx: int, tab: DocumentTab) -> None:
        doc = tab.doc
        if doc is None or doc.source_path is None:
            name = self._t("tab_untitled")
        else:
            name = doc.source_path.name
        dirty_mark = " *" if tab.dirty else ""
        self._file_tabs.setTabText(idx, f"{name}{dirty_mark}")
        tooltip = str(doc.source_path) if doc is not None and doc.source_path else ""
        self._file_tabs.setTabToolTip(idx, tooltip)

    def _update_window_title(self) -> None:
        tab = self._current_tab()
        if tab is None or tab.doc is None:
            self.setWindowTitle(self._t("app_name"))
            return
        doc = tab.doc
        dirty_mark = " *" if tab.dirty else ""
        if doc.source_path:
            self.setWindowTitle(f"{doc.source_path.name}{dirty_mark} – {self._t('app_name')}")
        else:
            self.setWindowTitle(f"{self._t('app_name')}{dirty_mark}")

    def _on_tab_content_changed(self, tab: DocumentTab) -> None:
        for i in range(self._file_tabs.count()):
            if self._file_tabs.widget(i) is tab:
                self._set_tab_title(i, tab)
                break
        if self._current_tab() is tab:
            self._update_window_title()

    def _on_file_tab_changed(self, _: int) -> None:
        tab = self._current_tab()
        if tab is not None:
            self._current_sort = tab.sort_mode
            self._current_format = tab.export_format
            sort_modes = [SortMode.NONE, SortMode.SECTIONS_ALPHA, SortMode.KEYS_ALPHA, SortMode.SECTIONS_AND_KEYS_ALPHA]
            self._sort_combo.blockSignals(True)
            self._sort_combo.setCurrentIndex(sort_modes.index(self._current_sort))
            self._sort_combo.blockSignals(False)
            fmts = [ExportFormat.INI, ExportFormat.JSON, ExportFormat.XML, ExportFormat.YAML]
            self._format_combo.blockSignals(True)
            self._format_combo.setCurrentIndex(fmts.index(self._current_format))
            self._format_combo.blockSignals(False)
        self._update_window_title()

    def _update_translations(self) -> None:
        self._update_window_title()
        self._sort_group.setTitle(self._t("sort_group"))
        sort_modes = [SortMode.NONE, SortMode.SECTIONS_ALPHA, SortMode.KEYS_ALPHA, SortMode.SECTIONS_AND_KEYS_ALPHA]
        self._sort_combo.blockSignals(True)
        self._sort_combo.clear()
        self._sort_combo.addItems([
            self._t("sort_none"),
            self._t("sort_sections"),
            self._t("sort_keys"),
            self._t("sort_both"),
        ])
        self._sort_combo.setCurrentIndex(sort_modes.index(self._current_sort))
        self._sort_combo.blockSignals(False)
        self._export_group.setTitle(self._t("export_group"))
        self._export_button.setText(self._t("export_button"))
        self._language_group.setTitle(self._t("language_label"))
        self._file_menu.setTitle(self._t("menu_file"))
        self._edit_menu.setTitle(self._t("menu_edit"))
        self._view_menu.setTitle(self._t("menu_view"))
        self._help_menu.setTitle(self._t("menu_help"))
        self._act_new.setText(self._t("action_new"))
        self._act_new_tab.setText(self._t("action_new_tab"))
        self._act_open.setText(self._t("action_open"))
        self._act_open_tab.setText(self._t("action_open_tab"))
        self._act_merge.setText(self._t("action_merge"))
        self._act_close_tab.setText(self._t("action_close_tab"))
        self._act_save.setText(self._t("action_save"))
        self._act_save_as.setText(self._t("action_save_as"))
        self._act_export.setText(self._t("action_export"))
        self._act_quit.setText(self._t("action_quit"))
        self._act_undo.setText(self._t("action_undo"))
        self._act_redo.setText(self._t("action_redo"))
        self._act_add_section.setText(self._t("action_add_section"))
        self._act_expand.setText(self._t("action_expand"))
        self._act_collapse.setText(self._t("action_collapse"))
        self._act_about.setText(self._t("action_about"))
        self._act_find.setText(self._t("action_find"))
        self._act_find_replace.setText(self._t("action_find_replace"))
        self._act_compare.setText(self._t("action_compare"))
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
        for i in range(self._file_tabs.count()):
            tab = self._file_tabs.widget(i)
            if isinstance(tab, DocumentTab):
                tab.set_labels(
                    self._t("tree_label"),
                    self._t("preview_tab"),
                    self._t("header_tab"),
                    self._t("header_placeholder"),
                )
                self._set_tab_title(i, tab)

    def _on_language_changed(self, idx: int) -> None:
        self._language = Language.DE if idx == 0 else Language.EN
        for i in range(self._file_tabs.count()):
            tab = self._file_tabs.widget(i)
            if isinstance(tab, DocumentTab):
                tab.set_language(self._language)
        self._find_bar.set_language(self._language)
        self._update_translations()
        for i in range(self._file_tabs.count()):
            w = self._file_tabs.widget(i)
            if isinstance(w, DiffTab):
                w.set_language(self._language)
        tab = self._current_tab()
        if tab is not None:
            tab.load_into_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(6, 6, 6, 6)

        ctrl_bar = QHBoxLayout()

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
            logo_path = Path(sys._MEIPASS) / "assets" / "logo.png"
        else:
            logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
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

        self._file_tabs = QTabWidget()
        self._file_tabs.setTabsClosable(True)
        self._file_tabs.tabCloseRequested.connect(self._close_tab)
        self._file_tabs.currentChanged.connect(self._on_file_tab_changed)
        root_layout.addWidget(self._file_tabs, 1)

        self._find_bar = FindBar(self._language)
        self._find_bar.find_next_requested.connect(self._find_next)
        self._find_bar.find_prev_requested.connect(self._find_prev)
        self._find_bar.replace_requested.connect(self._replace_next)
        self._find_bar.replace_all_requested.connect(self._replace_all)
        root_layout.addWidget(self._find_bar)

        self._new_tab(IniDocument())

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

        self._file_menu = bar.addMenu(self._t("menu_file"))

        self._act_new = QAction(self._t("action_new"), self)
        self._act_new.setShortcut(QKeySequence.StandardKey.New)
        self._act_new.triggered.connect(self._new_document)
        self._file_menu.addAction(self._act_new)

        self._act_new_tab = QAction(self._t("action_new_tab"), self)
        self._act_new_tab.setShortcut(QKeySequence("Ctrl+T"))
        self._act_new_tab.triggered.connect(lambda: self._new_tab(IniDocument()))
        self._file_menu.addAction(self._act_new_tab)

        self._file_menu.addSeparator()

        self._act_open = QAction(self._t("action_open"), self)
        self._act_open.setShortcut(QKeySequence.StandardKey.Open)
        self._act_open.triggered.connect(self._open_file)
        self._file_menu.addAction(self._act_open)

        self._act_open_tab = QAction(self._t("action_open_tab"), self)
        self._act_open_tab.setShortcut(QKeySequence("Ctrl+Shift+O"))
        self._act_open_tab.triggered.connect(self._open_file_in_new_tab)
        self._file_menu.addAction(self._act_open_tab)

        self._act_merge = QAction(self._t("action_merge"), self)
        self._act_merge.triggered.connect(self._merge_files)
        self._file_menu.addAction(self._act_merge)

        self._file_menu.addSeparator()

        self._act_close_tab = QAction(self._t("action_close_tab"), self)
        self._act_close_tab.setShortcut(QKeySequence("Ctrl+W"))
        self._act_close_tab.triggered.connect(self._close_current_tab)
        self._file_menu.addAction(self._act_close_tab)

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

        self._edit_menu = bar.addMenu(self._t("menu_edit"))

        self._act_undo = QAction(self._t("action_undo"), self)
        self._act_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self._act_undo.triggered.connect(self._undo)
        self._edit_menu.addAction(self._act_undo)

        self._act_redo = QAction(self._t("action_redo"), self)
        self._act_redo.setShortcut(QKeySequence.StandardKey.Redo)
        self._act_redo.triggered.connect(self._redo)
        self._edit_menu.addAction(self._act_redo)

        self._edit_menu.addSeparator()

        self._act_add_section = QAction(self._t("action_add_section"), self)
        self._act_add_section.triggered.connect(self._add_section_to_current_tab)
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

        self._edit_menu.addSeparator()

        self._act_compare = QAction(self._t("action_compare"), self)
        self._act_compare.triggered.connect(self._open_diff_tab)
        self._edit_menu.addAction(self._act_compare)

        self._view_menu = bar.addMenu(self._t("menu_view"))
        self._act_expand = QAction(self._t("action_expand"), self)
        self._act_expand.triggered.connect(self._expand_all)
        self._view_menu.addAction(self._act_expand)
        self._act_collapse = QAction(self._t("action_collapse"), self)
        self._act_collapse.triggered.connect(self._collapse_all)
        self._view_menu.addAction(self._act_collapse)

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
        self._tb_add_section = self._toolbar.addAction(
            self._t("action_add_section"), self._add_section_to_current_tab
        )

    def _apply_dark_theme(self) -> None:
        self.setStyleSheet(DARK_STYLESHEET)

    @staticmethod
    def _is_pristine_tab(tab: Optional[DocumentTab]) -> bool:
        if tab is None or tab.dirty:
            return False
        doc = tab.doc
        if doc is None:
            return True
        return (
            doc.source_path is None
            and not doc.sections
            and not doc.header_comments
            and not doc.trailing_comments
        )

    def _new_document(self) -> None:
        tab = self._current_tab()
        if self._is_pristine_tab(tab):
            tab.load_document(IniDocument())
            self._set_tab_title(self._file_tabs.currentIndex(), tab)
        else:
            self._new_tab(IniDocument())
        self._update_window_title()
        self.statusBar().showMessage(self._t("status_new_document"))

    def _load_file_into_tab(self, path: str, tab: DocumentTab) -> bool:
        try:
            doc = IniParser.parse_file(path)
            tab.load_document(doc)
            return True
        except Exception as exc:
            QMessageBox.critical(self, self._t("error_export"), self._t("error_open", exc=str(exc)))
            return False

    def _open_file_paths(self, paths: list[str | Path]) -> None:
        """Open each path in its own tab.

        The current tab is reused if it is pristine (no document, not dirty);
        every remaining path is opened in a new tab. Files that fail to parse
        are reported via a dialog but do not abort the batch.

        Args:
            paths: One or more file paths to open.
        """
        loaded = 0
        for i, path in enumerate(paths):
            path = str(path)
            tab = self._current_tab()
            if i == 0 and self._is_pristine_tab(tab):
                if self._load_file_into_tab(path, tab):
                    self._set_tab_title(self._file_tabs.currentIndex(), tab)
                    loaded += 1
            else:
                tab = self._new_tab()
                if self._load_file_into_tab(path, tab):
                    self._set_tab_title(self._file_tabs.currentIndex(), tab)
                    loaded += 1
        if loaded == 0:
            return
        self._update_window_title()
        if loaded > 1:
            self.statusBar().showMessage(self._t("status_opened_multiple", count=loaded))
        else:
            self.statusBar().showMessage(self._t("status_loaded", path=str(paths[0])))

    def _open_file(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, self._t("open_file_title"), "",
            "INI-Dateien (*.ini *.cfg *.conf);;Alle Dateien (*)"
        )
        if paths:
            self._open_file_paths(paths)

    def _open_file_in_new_tab(self, path: str = "") -> None:
        if not path:
            path, _ = QFileDialog.getOpenFileName(
                self, self._t("open_file_title"), "",
                "INI-Dateien (*.ini *.cfg *.conf);;Alle Dateien (*)"
            )
        if not path:
            return
        tab = self._new_tab()
        if self._load_file_into_tab(path, tab):
            idx = self._file_tabs.currentIndex()
            self._set_tab_title(idx, tab)
            self._update_window_title()
            self.statusBar().showMessage(self._t("status_loaded", path=path))

    def _merge_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, self._t("merge_files_title"), "",
            "INI-Dateien (*.ini *.cfg *.conf);;Alle Dateien (*)"
        )
        if not paths:
            return
        tab = self._current_tab()
        if tab is None:
            return
        if tab.doc is None:
            tab.load_document(IniDocument())

        merged = 0
        for path in paths:
            try:
                doc = IniParser.parse_file(path)
                tab.doc.merge_from(doc)
                merged += 1
            except Exception as exc:
                QMessageBox.warning(self, self._t("merge_error"), f"{path}: {exc}")

        if merged == 0:
            return

        tab.load_into_ui()
        tab.dirty = True
        idx = self._file_tabs.currentIndex()
        self._set_tab_title(idx, tab)
        self._update_window_title()
        self.statusBar().showMessage(self._t("status_merged", count=merged))

    def _save_file(self) -> None:
        tab = self._current_tab()
        if tab is None or tab.doc is None:
            return
        if tab.doc.source_path:
            self._write_ini(tab, tab.doc.source_path)
        else:
            self._save_file_as()

    def _save_file_as(self) -> None:
        tab = self._current_tab()
        if tab is None or tab.doc is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, self._t("save_file_title"), "",
            "INI-Dateien (*.ini);;Alle Dateien (*)"
        )
        if path:
            self._write_ini(tab, Path(path))

    def _write_ini(self, tab: DocumentTab, path: Path) -> None:
        try:
            doc = tab.doc.sorted_copy(tab.sort_mode) if tab.sort_mode != SortMode.NONE else tab.doc
            path.write_text(doc.to_ini_string(), encoding="utf-8")
            tab.doc.source_path = path
            tab.dirty = False
            idx = self._file_tabs.currentIndex()
            self._set_tab_title(idx, tab)
            self._update_window_title()
            self.statusBar().showMessage(self._t("status_saved", path=path))
        except Exception as exc:
            QMessageBox.critical(self, self._t("error_export"), self._t("error_save", exc=str(exc)))

    def _export_file(self) -> None:
        tab = self._current_tab()
        if tab is None or tab.doc is None:
            QMessageBox.information(self, self._t("no_document_title"), self._t("no_document_text"))
            return
        ext_map = {
            ExportFormat.INI: ("INI-Dateien (*.ini)", ".ini"),
            ExportFormat.JSON: ("JSON-Dateien (*.json)", ".json"),
            ExportFormat.XML: ("XML-Dateien (*.xml)", ".xml"),
            ExportFormat.YAML: ("YAML-Dateien (*.yaml *.yml)", ".yaml"),
        }
        filt, ext = ext_map[tab.export_format]
        path, _ = QFileDialog.getSaveFileName(
            self, self._t("action_export"), f"export{ext}", f"{filt};;Alle Dateien (*)"
        )
        if not path:
            return
        try:
            doc = tab.doc.sorted_copy(tab.sort_mode)
            content = doc.export(tab.export_format)
            Path(path).write_text(content, encoding="utf-8")
            self.statusBar().showMessage(self._t("status_exported", path=path))
        except Exception as exc:
            QMessageBox.critical(self, self._t("error_export"), str(exc))

    def _open_diff_tab(self) -> None:
        tabs_with_docs: list[tuple[str, DocumentTab]] = []
        for i in range(self._file_tabs.count()):
            w = self._file_tabs.widget(i)
            if isinstance(w, DocumentTab) and w.doc is not None:
                tabs_with_docs.append((self._file_tabs.tabText(i).rstrip(" *"), w))

        if len(tabs_with_docs) < 2:
            QMessageBox.information(
                self, self._t("diff_select_title"), self._t("diff_no_docs")
            )
            return

        dlg = DiffSelectDialog(tabs_with_docs, self._language, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        tab_a, tab_b = dlg.selected_tabs()
        if tab_a is tab_b:
            QMessageBox.warning(
                self, self._t("diff_select_title"), self._t("diff_same_doc")
            )
            return

        name_a = tab_a.doc.source_path.name if tab_a.doc and tab_a.doc.source_path else self._t("tab_untitled")
        name_b = tab_b.doc.source_path.name if tab_b.doc and tab_b.doc.source_path else self._t("tab_untitled")

        diff_widget = DiffTab(tab_a, tab_b, self._language)
        idx = self._file_tabs.addTab(diff_widget, f"⇔ {name_a} ↔ {name_b}")
        self._file_tabs.setCurrentIndex(idx)

    def _on_sort_changed(self, idx: int) -> None:
        modes = [SortMode.NONE, SortMode.SECTIONS_ALPHA, SortMode.KEYS_ALPHA, SortMode.SECTIONS_AND_KEYS_ALPHA]
        self._current_sort = modes[idx]
        tab = self._current_tab()
        if tab is not None:
            tab.set_sort_mode(self._current_sort)

    def _on_format_changed(self, idx: int) -> None:
        fmts = [ExportFormat.INI, ExportFormat.JSON, ExportFormat.XML, ExportFormat.YAML]
        self._current_format = fmts[idx]
        tab = self._current_tab()
        if tab is not None:
            tab.set_export_format(self._current_format)

    def _undo(self) -> None:
        tab = self._current_tab()
        if tab is not None:
            tab.undo()

    def _redo(self) -> None:
        tab = self._current_tab()
        if tab is not None:
            tab.redo()

    def _add_section_to_current_tab(self) -> None:
        tab = self._current_tab()
        if tab is not None:
            tab.tree._add_section()

    def _expand_all(self) -> None:
        tab = self._current_tab()
        if tab is not None:
            tab.tree.expandAll()

    def _collapse_all(self) -> None:
        tab = self._current_tab()
        if tab is not None:
            tab.tree.collapseAll()

    def _show_about(self) -> None:
        QMessageBox.about(
            self, self._t("about_title", app=self.APP_NAME),
            self._t("about_text", app=self.APP_NAME, version=_APP_VERSION)
        )

    def _show_find_dialog(self) -> None:
        w = self._file_tabs.currentWidget()
        if isinstance(w, DiffTab):
            w.show_find()
        else:
            self._find_bar.show_find()

    def _show_find_replace_dialog(self) -> None:
        w = self._file_tabs.currentWidget()
        if isinstance(w, DiffTab):
            w.show_find()
        else:
            self._find_bar.show_replace()

    def _find_next(self) -> None:
        if not self._find_bar.isVisible():
            return
        tab = self._current_tab()
        if tab is None:
            return
        search_text = self._find_bar.get_search_text()
        if not search_text:
            self._find_bar.set_status("")
            return
        count = self._search_in_text_edit(
            tab.preview_edit, search_text,
            self._find_bar.is_case_sensitive(), self._find_bar.is_whole_words(), forward=True
        )
        self._find_bar.set_status(self._t("find_count", count=count) if count else self._t("find_not_found"))

    def _find_prev(self) -> None:
        if not self._find_bar.isVisible():
            return
        tab = self._current_tab()
        if tab is None:
            return
        search_text = self._find_bar.get_search_text()
        if not search_text:
            self._find_bar.set_status("")
            return
        count = self._search_in_text_edit(
            tab.preview_edit, search_text,
            self._find_bar.is_case_sensitive(), self._find_bar.is_whole_words(), forward=False
        )
        self._find_bar.set_status(self._t("find_count", count=count) if count else self._t("find_not_found"))

    def _replace_next(self) -> None:
        if not self._find_bar.isVisible() or not self._find_bar.is_replace_mode():
            return
        tab = self._current_tab()
        if tab is None:
            return
        search_text = self._find_bar.get_search_text()
        replace_text = self._find_bar.get_replace_text()
        if not search_text:
            return
        cursor = tab.preview_edit.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText()
            matches = (
                selected == search_text
                if self._find_bar.is_case_sensitive()
                else selected.lower() == search_text.lower()
            )
            if matches:
                tab.push_undo_state()
                cursor.insertText(replace_text)
                tab.sync_doc_from_preview()
        self._find_next()

    def _replace_all(self) -> None:
        if not self._find_bar.isVisible() or not self._find_bar.is_replace_mode():
            return
        tab = self._current_tab()
        if tab is None:
            return
        search_text = self._find_bar.get_search_text()
        replace_text = self._find_bar.get_replace_text()
        case_sensitive = self._find_bar.is_case_sensitive()
        if not search_text:
            return
        text = tab.preview_edit.document().toPlainText()
        if case_sensitive:
            new_text = text.replace(search_text, replace_text)
            count = text.count(search_text)
        else:
            import re
            pattern = re.compile(re.escape(search_text), re.IGNORECASE)
            new_text = pattern.sub(replace_text, text)
            count = len(pattern.findall(text))
        if count > 0:
            tab.push_undo_state()
            tab.preview_edit.setPlainText(new_text)
            tab.sync_doc_from_preview()
            self._find_bar.set_status(self._t("find_replace_count", count=count))
        else:
            self._find_bar.set_status(self._t("find_not_found"))

    def _count_all_in_text_edit(
        self, text_edit: QPlainTextEdit, search_text: str, case_sensitive: bool, whole_words: bool
    ) -> int:
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

    def _search_in_text_edit(
        self, text_edit: QPlainTextEdit, search_text: str,
        case_sensitive: bool, whole_words: bool, forward: bool = True
    ) -> int:
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
            if forward:
                cursor.movePosition(QTextCursor.MoveOperation.Start)
            else:
                cursor.movePosition(QTextCursor.MoveOperation.End)
            found_cursor = doc.find(search_text, cursor, options)
        if not found_cursor.isNull():
            text_edit.setTextCursor(found_cursor)
            tab = self._current_tab()
            if tab is not None and text_edit is tab.preview_edit and tab.export_format == ExportFormat.INI:
                tab.sync_tree_to_preview_match(found_cursor)
            return self._count_all_in_text_edit(text_edit, search_text, case_sensitive, whole_words)
        return 0

    _INI_SUFFIXES = {".ini", ".cfg", ".conf"}

    def _is_valid_ini_url(self, url: QUrl) -> bool:
        return url.isLocalFile() and Path(url.toLocalFile()).suffix.lower() in self._INI_SUFFIXES

    def _is_file_already_open(self, path: Path) -> bool:
        for i in range(self._file_tabs.count()):
            tab = self._file_tabs.widget(i)
            if isinstance(tab, DocumentTab) and tab.doc is not None:
                if tab.doc.source_path == path:
                    return True
        return False

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls() and any(
            self._is_valid_ini_url(u) for u in event.mimeData().urls()
        ):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:  # type: ignore[override]
        event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # type: ignore[override]
        valid_paths = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if self._is_valid_ini_url(url) and not self._is_file_already_open(Path(url.toLocalFile()))
        ]
        if valid_paths:
            self._open_file_paths(valid_paths)
        event.acceptProposedAction()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        dirty_count = sum(
            1 for i in range(self._file_tabs.count())
            if isinstance(self._file_tabs.widget(i), DocumentTab)
            and self._file_tabs.widget(i).dirty  # type: ignore[union-attr]
        )
        if dirty_count == 0:
            event.accept()
            return
        msg = self._t("confirm_discard_all_text") if dirty_count > 1 else self._t("confirm_discard_text")
        reply = QMessageBox.question(
            self, self._t("confirm_discard_title"), msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


def main() -> None:
    """Application entry point.

    Boots :class:`QApplication`, shows the main window, and runs the Qt
    event loop until the user closes the application.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("ini-file-editor")
    app.setOrganizationName("OpenSource")
    app.setStyleSheet(DARK_STYLESHEET)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()