# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ini-file-editor** is a comment-preserving INI file editor with a PyQt6 GUI and multi-format export capabilities. The application maintains all comments (preceding, inline, and header) during parsing and serialization.

**Stack:** Python 3.11+, PyQt6 6.6.0+, PyYAML, lxml  
**Type:** Cross-platform desktop GUI application

## Commands

```bash
# Install runtime dependencies
pip install -r requirements.txt

# Install dev dependencies (testing, linting, building)
pip install -r requirements-dev.txt

# Run the GUI
python main.py

# Run all tests
pytest

# Run a single test class
pytest tests/test_ini_parser.py::TestSorting -v

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Format / lint / type-check  (black uses line-length 100)
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/

# Build standalone EXE
python -m pyinstaller ini-file-editor.spec

# Build API documentation (Sphinx + Furo theme, Google-style docstrings)
sphinx-build -b html docs docs/_build/html        # one-shot HTML build
sphinx-build -b markdown docs docs/_build/markdown # Markdown for Azure DevOps Wiki
sphinx-autobuild docs docs/_build/html             # live-reload server on :8000
```

## Architecture

Three-layer design:

### 1. Data Model (`src/ini_parser.py`)

- **`IniEntry`** — a `key=value` pair with optional preceding and inline comments
- **`IniSection`** — a `[section]` with header comments and a list of `IniEntry` objects
- **`IniDocument`** — root container: header comments, list of sections, trailing comments, optional source path

All classes have `clone()` methods to enable non-destructive transformations. `IniDocument.sorted_copy(SortMode)` returns a new document; the original is never mutated by sorting.

### 2. Parser & Export Engine (`src/ini_parser.py`)

**`IniParser`** uses regex-based line classification (stateless, single-pass):
- Comments: `^[;#]` — accumulated into `pending_comments` until the next section/entry claims them
- Section headers: `^\[([^\]]+)\]`
- Key-value pairs: `^([^=]+)=(.*)$`
- Inline comments: `\s{2,}[;#]` — requires 2+ spaces to distinguish from value text
- **Duplicates** — duplicate section headers and duplicate keys within a section are preserved verbatim (separate `IniSection` / `IniEntry` instances) so the file round-trips byte-for-byte. Each duplicate is appended to `IniDocument.duplicates` as a `DuplicateRecord(kind, section, key, line)`. Lookup helpers (`IniDocument.get_section`, `IniSection.get_entry`, `set_entry`, `remove_entry`) return / mutate the **first** match — matching Win32 `GetPrivateProfileString` semantics, since these files are typically consumed by Win32 applications. The GUI surfaces a warning dialog on file load whenever `doc.duplicates` is non-empty.

**Export** is dispatched via `IniDocument.export(ExportFormat)` to:
- `to_ini_string()` — full round-trip reconstruction with all comment metadata
- `to_json_string()` — nested `{section: {key: value}}`
- `to_xml_string()` — `<configuration><section><entry>` with lxml pretty-print
- `to_yaml_string()` — requires PyYAML (optional; GUI degrades gracefully if missing)

Round-trip guarantee: parse → serialize → re-parse produces an identical document.

### 3. GUI Layer (`src/main_window.py`)

- **`MainWindow`** — menu bar, toolbar, status bar, multi-tab file management with unsaved-changes guard
- **`DocumentTab`** (`QSplitter`) — one instance per open file; owns the `IniTreeWidget`, preview `QPlainTextEdit`, header editor, and its own undo/redo stacks (`list[IniDocument]`). Undo is snapshot-based via `clone()`, not `QUndoStack`.
- **`IniTreeWidget`** — hierarchical tree: sections → entries, with Catppuccin-inspired dark theme
- **`IniHighlighter`** (`QSyntaxHighlighter`) — colors comments, section headers, keys, and values in the preview panel
- **`FindBar`** — embedded bottom panel for Find and Find/Replace; operates on the **preview text**, then calls `DocumentTab.sync_doc_from_preview()` to re-parse and update the model
- **Edit dialogs** (`EntryEditDialog`, `SectionEditDialog`) — modal dialogs for key/value/comment editing
- **Bilingual UI** — German/English switching via `TRANSLATIONS` dict and `Language` enum; all UI strings must have entries for both languages
- **Scroll sync** — when export format is INI, scrolling the tree scrolls the preview and vice-versa; disabled for non-INI formats

Data flow: User edit → dialog → `IniDocument` mutated → `refresh_tree()` → preview refreshed → save/export.

### 4. Documentation (`docs/`)

Sphinx-based API documentation generated from Google-style docstrings.

- **`docs/conf.py`** — Furo theme, `napoleon` (Google-style), `autodoc`, `autosummary`, `sphinx-autodoc-typehints`. `autodoc_mock_imports` covers `PyQt6`, `yaml`, `lxml`, `PIL` so the build runs on machines without those installed. `napoleon_use_ivar = True` and `napoleon_custom_sections = [("Signals", "params_style")]` are set to keep the build warning-clean.
- **`docs/index.rst`** — entry page with toctree to `api/*.rst` and `architecture.rst`
- **`docs/api/`** — one `.rst` per module: `ini_parser`, `ini_diff`, `translations`, `gui` (aggregates all PyQt6 modules)
- **`docs/Makefile` / `docs/make.bat`** — targets `html`, `markdown`, `clean`

Build is wired into [azure-pipelines.yml](azure-pipelines.yml) as a `Docs` stage that runs in parallel with `Build`: publishes HTML as the `docs-html` pipeline artifact and pushes Markdown to the project's Azure DevOps Wiki (`wikiMaster` branch, `API/` folder). Wiki push is `continueOnError: true` so missing wiki setup never breaks CI.

## Key Patterns

- **`sorted_copy()` / `clone()`** — sorting and transformations always return new instances; never mutate in place
- **Pending comments** — comments accumulate in a list and are assigned to the next section or entry encountered; this is the core of comment preservation
- **`SortMode` / `ExportFormat` enums** — used throughout; avoid raw string comparisons
- **`main.py` sys.path manipulation** — supports running from repo root, src dir, and PyInstaller bundles; do not remove
- **Google-style docstrings** — all new public classes / methods get them so Sphinx `autodoc` + `napoleon` picks them up. Use `Signals:` (custom section, configured in `conf.py`) to document PyQt signals on widgets.

## Adding a New Export Format

1. Add entry to `ExportFormat` enum in [src/ini_parser.py](src/ini_parser.py)
2. Implement `to_<format>_string()` on `IniDocument`
3. Add case to `export()` dispatch
4. Add test in [tests/test_ini_parser.py](tests/test_ini_parser.py)
5. Add format to the export dropdown in [src/main_window.py](src/main_window.py) with translations for both `Language.DE` and `Language.EN`

## Testing Notes

- GUI code (`src/main_window.py`) is excluded from coverage in `pyproject.toml`; parser has >95% coverage
- `test_roundtrip()` is critical — catches regressions in comment preservation
- CI runs GUI tests under `xvfb-run` on Linux; native display on Windows/macOS
