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

# Format / lint / type-check
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/

# Build standalone EXE
python -m pyinstaller ini-file-editor.spec
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
- Duplicate section headers are merged into the existing section

**Export** is dispatched via `IniDocument.export(ExportFormat)` to:
- `to_ini_string()` — full round-trip reconstruction with all comment metadata
- `to_json_string()` — nested `{section: {key: value}}`
- `to_xml_string()` — `<configuration><section><entry>` with lxml pretty-print
- `to_yaml_string()` — requires PyYAML (optional; GUI degrades gracefully if missing)

Round-trip guarantee: parse → serialize → re-parse produces an identical document.

### 3. GUI Layer (`src/main_window.py`)

- **`MainWindow`** — menu bar, toolbar, status bar, multi-tab file management with unsaved-changes guard
- **`IniTreeWidget`** — hierarchical tree: sections → entries, with Catppuccin-inspired dark theme
- **Edit dialogs** (`EntryEditDialog`, `SectionEditDialog`) — modal dialogs for key/value/comment editing
- **Format preview panel** — live right-side panel updating on every document change
- **Bilingual UI** — German/English switching via `TRANSLATIONS` dict and `Language` enum; all UI strings must have entries for both languages
- Features: Find/Replace, Undo/Redo (`QUndoStack`), Drag & Drop, Section merge, Sort dropdown

Data flow: User edit → dialog → `IniDocument` mutated → `refresh_tree()` → preview refreshed → save/export.

## Key Patterns

- **`sorted_copy()` / `clone()`** — sorting and transformations always return new instances; never mutate in place
- **Pending comments** — comments accumulate in a list and are assigned to the next section or entry encountered; this is the core of comment preservation
- **`SortMode` / `ExportFormat` enums** — used throughout; avoid raw string comparisons
- **`main.py` sys.path manipulation** — supports running from repo root, src dir, and PyInstaller bundles; do not remove

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
