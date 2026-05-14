# Ini-File-Editor

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://pypi.org/project/PyQt6/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Ein kommentarerhaltender INI-Datei-Editor mit **PyQt6-GUI**, flexibler Sortierung und Export nach **INI / JSON / XML / YAML**.

---

## Inhaltsverzeichnis

- [Features](#features)
- [Screenshots](#screenshots)
- [Voraussetzungen](#voraussetzungen)
- [Installation](#installation)
- [Verwendung](#verwendung)
- [Projektstruktur](#projektstruktur)
- [Architektur](#architektur)
- [Tests ausführen](#tests-ausführen)
- [Dokumentation bauen](#dokumentation-bauen)
- [DevOps / CI-CD Pipeline](#devops--cicd-pipeline)
  - [Versionierung](#versionierung)
- [Docker](#docker)
- [Beitragen](#beitragen)
- [Lizenz](#lizenz)

---

## Features

### Kern-Engine (`ini_parser.py`)

| Feature | Beschreibung |
|---|---|
| **Kommentarerhalt** | `;`- und `#`-Kommentare (vorangestellt und inline) bleiben vollständig erhalten |
| **Abschnitts-Kommentare** | Kommentare vor/nach `[section]`-Headern werden getrennt gespeichert |
| **Globale Kopfkommentare** | Datei-Header-Kommentare vor dem ersten Abschnitt werden dediziert behandelt |
| **Sortierung** | Keine / Abschnitte alphabetisch / Schlüssel alphabetisch / beides |
| **Export: INI** | Formatierte, einheitliche INI-Ausgabe inkl. aller Kommentare |
| **Export: JSON** | Kompaktes JSON als `{ "section": { "key": "value" } }` |
| **Export: XML** | Valides XML mit `<configuration><section><entry>` Struktur |
| **Export: YAML** | Lesbares YAML (benötigt PyYAML) |
| **Round-Trip** | Parse → Serialize → Re-Parse ergibt identische Datenstruktur |
| **Meta-INI / Merge** | Mehrere INI-Dateien zu einem Dokument zusammenführen und exportieren |

### GUI-Schicht (`main_window.py` + Submodule)

| Feature | Beschreibung |
|---|---|
| **Strukturübersicht** | Hierarchischer Tree-View: Abschnitt → Schlüssel/Wert/Kommentar |
| **Inline-Editing** | Doppelklick oder Kontextmenü öffnet Bearbeitungs-Dialoge |
| **Kommentar-Editing** | Vorangestellte und Inline-Kommentare editierbar |
| **Sortierung live** | Dropdown ändert die Darstellung sofort, Export folgt der Sortierung |
| **Format-Vorschau** | Rechtes Panel zeigt Live-Preview im gewählten Export-Format |
| **Syntax-Highlighting** | Schlüssel, Werte, Kommentare und Abschnittsnamen farblich hervorgehoben |
| **Dark Theme** | Modernes dunkles Erscheinungsbild (Catppuccin-inspiriert) |
| **Unsaved-Changes-Guard** | Warnung beim Schließen mit ungespeicherten Änderungen |
| **Plattformübergreifend** | Windows, macOS, Linux |

---

## Voraussetzungen

- **Python 3.11** oder neuer
- **PyQt6** ≥ 6.6.0
- **PyYAML** ≥ 6.0 (für YAML-Export)
- Linux: `libgl1`, `libglib2.0-0` (für Qt)

---

## Installation

### Option A – direkt aus dem Repository

```bash
git clone https://github.com/Helferlein21963/ini-file-editor.git
cd ini-file-editor

# Virtuelle Umgebung empfohlen
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Option C – vorkompiliertes Binary (Releases-Seite)

Laden Sie das passende Binary von der [Releases](https://github.com/Helferlein21963/ini-file-editor/releases) Seite herunter – kein Python-Setup erforderlich.

---

## Setup & Entwicklung

### Virtual Environment einrichten

**Windows:**
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux/macOS:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Entwicklungsumgebung aufsetzen

Mit allen Dev-Dependencies (Tests, Linting, Formatting, PyInstaller):

```bash
pip install -r requirements-dev.txt
```

---

## Build & Distribution

### Icon konvertieren

Liegt eine `assets/icon.png` vor, generiert die PyInstaller-Spec beim Build automatisch eine
passende `assets/icon.ico` (Multi-Resolution: 16/32/48/64/128/256), sofern die `.ico` fehlt
oder älter als das PNG ist. Du musst also nichts vorab tun.

Optional kann die Konvertierung auch manuell angestoßen werden:

```bash
python src/convert_icon.py
```

Das Skript liest `assets/icon.png` und schreibt `assets/icon.ico`. Benötigt `Pillow`
(in `requirements-dev.txt` enthalten).

### Executable mit PyInstaller bauen

**Voraussetzungen:**
- Virtual Environment aktiviert
- `pyinstaller` installiert: `pip install pyinstaller` (oder `pip install -r requirements-dev.txt`)

**Executable erstellen (empfohlen):**

```bash
python -m pyinstaller --onefile --windowed --add-data "assets/logo.png;assets" --icon="assets/icon.ico" --name ini-file-editor main.py
```

Das Executable wird erstellt in: `dist/ini-file-editor.exe`

**Optionen erklärt:**
- `--onefile` – Alles in eine einzelne `.exe` packen
- `--windowed` – Keine Konsole anzeigen (nur GUI)
- `--add-data "assets/logo.png;assets"` – Logo-Datei in die Executable einbinden
- `--icon="assets/icon.ico"` – EXE-Icon festlegen
- `--name ini-file-editor` – Name des Executables

**Optional – Build mit der `.spec`-Datei (empfohlen):**

```bash
python -m pyinstaller ini-file-editor.spec
```

Die `.spec`-Datei generiert vor dem Kompilieren automatisch `version_info.txt` mit den Windows-EXE-Metadaten (Dateiversion, Produktname usw.). Die Patch-Version wird dabei aus der Anzahl der Git-Commits ermittelt. Haupt- und Nebenversion lassen sich über Umgebungsvariablen steuern:

```powershell
# Windows – Hauptversion 2, Nebenversion 1
$env:MAJOR_VERSION = "2"; $env:MINOR_VERSION = "1"
python -m pyinstaller ini-file-editor.spec
```

```bash
# Linux / macOS
MAJOR_VERSION=2 MINOR_VERSION=1 python -m pyinstaller ini-file-editor.spec
```

Ohne gesetzte Umgebungsvariablen werden die Standardwerte `1.0` verwendet.

---

## Verwendung

### GUI starten

```bash
python main.py
```

### Typischer Arbeitsablauf

1. **Datei öffnen** – `Datei → Öffnen` oder `Strg+O`
   → Die Beispieldatei `example.ini` eignet sich zum Testen
2. **Struktur erkunden** – Linkes Panel zeigt alle Abschnitte und Einträge
3. **Bearbeiten** – Doppelklick auf einen Eintrag öffnet den Editor-Dialog
4. **Sortierung wählen** – Dropdown oben links
5. **Format wählen** – Dropdown oben rechts, Vorschau aktualisiert sich live
6. **Speichern** – `Strg+S` (speichert als INI)
7. **Exportieren** – `Datei → Exportieren` (speichert im gewählten Format)

### Kommandozeilennutzung (headless / Skript)

```python
from src.ini_parser import IniParser, SortMode, ExportFormat

# Einlesen
doc = IniParser.parse_file("example.ini")

# Sortiert ausgeben
sorted_doc = doc.sorted_copy(SortMode.SECTIONS_AND_KEYS_ALPHA)

# Als verschiedene Formate ausgeben
print(sorted_doc.export(ExportFormat.INI))
print(sorted_doc.export(ExportFormat.JSON))
print(sorted_doc.export(ExportFormat.XML))
print(sorted_doc.export(ExportFormat.YAML))

# Einträge bearbeiten
section = doc.get_section("network")
section.set_entry("timeout", "60")

# Speichern
from pathlib import Path
Path("output.ini").write_text(doc.to_ini_string(), encoding="utf-8")
```

---

## Projektstruktur

```
ini-file-editor/
├── main.py                        # Einstiegspunkt
├── src/
│   ├── ini_parser.py              # Parser, Datenmodell, Export-Engine
│   ├── ini_diff.py                # Vergleichslogik für zwei IniDocument
│   ├── translations.py            # Language-Enum, UI-Strings (DE/EN), translate()
│   ├── highlighter.py             # IniHighlighter (Syntax-Highlighting für die Vorschau)
│   ├── dialogs.py                 # EntryEditDialog, SectionEditDialog, DiffSelectDialog
│   ├── ini_tree_widget.py         # IniTreeWidget (Struktur-Tree für Abschnitte/Einträge)
│   ├── find_bar.py                # FindBar (eingebettete Find/Replace-Leiste)
│   ├── document_tab.py            # DocumentTab (ein Editor-Pane pro Datei)
│   ├── diff_tab.py                # DiffTab (Side-by-Side-Vergleich zweier Dokumente)
│   └── main_window.py             # MainWindow + main() (Menüs, Toolbar, Tab-Verwaltung)
├── assets/                       # Logo (logo.png) und Icon (icon.png/icon.ico)
├── scripts/
│   └── generate_version_info.py  # Erzeugt version_info.txt für PyInstaller
├── tests/
│   ├── test_ini_parser.py         # Unit-Tests für Parser, Sortierung, Export
│   └── test_ini_diff.py           # Unit-Tests für die Diff-Logik
├── example.ini                    # Beispiel-INI (unstrukturiert, mit Kommentaren)
├── ini-file-editor.spec           # PyInstaller-Spec (erzeugt version_info.txt automatisch)
├── requirements.txt               # Laufzeit-Abhängigkeiten
├── requirements-dev.txt           # Entwicklungs- & CI-Abhängigkeiten
├── pyproject.toml                 # Paket-Metadaten, Black, isort, mypy, pytest
├── Dockerfile                     # Multi-Stage Build (Test + Runtime)
├── azure-pipelines.yml            # Azure DevOps Pipeline (Build + Versionierung)
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions Pipeline
├── .gitlab-ci.yml                 # GitLab CI Alternative
└── README.md
```

Die GUI ist auf mehrere kleine Module aufgeteilt, damit jede Datei eine klar abgegrenzte Verantwortung hat. `main_window.py` enthält nur noch das Haupt-`MainWindow` (Menü, Toolbar, Tab-Verwaltung); alle Widgets, Dialoge und Hilfsklassen liegen in eigenen Modulen.

---

## Architektur

```
┌─────────────────────────────────────────────────────────┐
│                      GUI-Schicht                         │
│  MainWindow  ←→  IniTreeWidget  ←→  EditDialoge         │
└─────────────────────┬───────────────────────────────────┘
                      │ benutzt
┌─────────────────────▼───────────────────────────────────┐
│                   Datenmodell                            │
│  IniDocument                                             │
│  ├── header_comments: list[str]                          │
│  ├── sections: list[IniSection]                          │
│  │   ├── name: str                                       │
│  │   ├── preceding_comments: list[str]                   │
│  │   ├── entries: list[IniEntry]                         │
│  │   │   ├── key, value: str                             │
│  │   │   ├── preceding_comments: list[str]               │
│  │   │   └── inline_comment: str                         │
│  │   └── trailing_comments: list[str]                    │
│  └── trailing_comments: list[str]                        │
└─────────────────────┬───────────────────────────────────┘
          ┌───────────┴───────────┐
          │                       │
┌─────────▼───────┐   ┌──────────▼──────────┐
│   IniParser     │   │   Export-Methoden    │
│  parse_file()   │   │  to_ini_string()     │
│  parse_string() │   │  to_json_string()    │
└─────────────────┘   │  to_xml_string()     │
                      │  to_yaml_string()    │
                      └─────────────────────┘
```

---

## Tests ausführen

```bash
# Alle Tests
pytest

# Mit Coverage-Report
pytest --cov=src --cov-report=term-missing

# Nur eine Testklasse
pytest tests/test_ini_parser.py::TestSorting -v

# Schnell (ohne Coverage)
pytest tests/ -q
```

Testabdeckung der Kern-Engine: **>95 %** (GUI-Code wird im Headless-CI übersprungen).

---

## Dokumentation bauen

Die API-Dokumentation wird mit [Sphinx](https://www.sphinx-doc.org/) aus den Google-Style-Docstrings im Quellcode generiert. Die Konfiguration liegt in [`docs/conf.py`](docs/conf.py); Theme: [Furo](https://pradyunsg.me/furo/).

**Voraussetzung** – Dev-Dependencies installieren:

```bash
pip install -r requirements-dev.txt
```

### Einmaliger Build (HTML)

```powershell
# Windows
.\docs\make.bat html

# Linux / macOS
make -C docs html
```

Plattformneutral und identisch zum Pipeline-Befehl:

```bash
sphinx-build -b html docs docs/_build/html
```

Ergebnis öffnen:

```powershell
# Windows
start docs\_build\html\index.html

# Linux / macOS
open docs/_build/html/index.html   # macOS
xdg-open docs/_build/html/index.html   # Linux
```

### Live-Vorschau via localhost

Während des Schreibens von Docstrings ist ein Live-Reload-Server am angenehmsten:

```bash
sphinx-autobuild docs docs/_build/html
```

Anschließend im Browser aufrufen:

```
http://127.0.0.1:8000
```

Bei jedem Speichern in `src/` oder `docs/` werden die Seiten automatisch neu gebaut und der Browser reloaded.

### Markdown-Build (für Azure DevOps Wiki)

Die Pipeline veröffentlicht zusätzlich eine Markdown-Variante im Project Wiki. Dasselbe Output lokal erzeugen:

```powershell
# Windows
.\docs\make.bat markdown

# Plattformneutral
sphinx-build -b markdown docs docs/_build/markdown
```

Pro RST-Quelldatei entsteht eine `.md`-Datei in [`docs/_build/markdown/`](docs/_build/markdown/). Die Pipeline pusht genau diese Dateien in den `<projekt>.wiki`-Git-Repo unter `API/`.

**Lokale Vorschau** der Markdown-Ausgabe (am nächsten an der Azure-DevOps-Wiki-Darstellung):

```bash
# In VS Code: Datei öffnen, Strg+Shift+V → Side-by-Side-Preview
# Oder mit grip im Browser (GitHub-Style-Renderer):
pip install grip
grip docs/_build/markdown/index.md
```

### Build-Verzeichnis aufräumen

```powershell
.\docs\make.bat clean
```

---

## DevOps / CI-CD Pipeline

### Azure Pipelines (`azure-pipelines.yml`)

Die primäre Build-Pipeline läuft auf Azure DevOps und erstellt bei jedem Commit auf `main` eine neue EXE mit eingebetteten Versions-Metadaten.

```
Commit auf main
   │
   ├─► Tests              pytest
   │
   ├─► Patch berechnen    git rev-list --count HEAD  →  PATCH_VERSION
   │
   ├─► version_info.txt   generate_version_info.py (MAJOR.MINOR.PATCH)
   │
   ├─► EXE bauen          pyinstaller ini-file-editor.spec
   │
   └─► Artefakt           ini-file-editor-build (Azure Artifacts)
```

### Versionierung

Die EXE-Metadaten (sichtbar unter *Eigenschaften → Details*) folgen **Semantic Versioning**:

| Feld in Dateieigenschaften | Wert | Beispiel |
|---|---|---|
| Dateiversion | `MAJOR.MINOR.PATCH` | `1.5.56` |
| Produktversion | `MAJOR.MINOR` | `1.5` |
| Produktname | statisch | `ini-file-editor` |

**Patch** wird automatisch pro Commit hochgezählt (`git rev-list --count HEAD`).  
**Hauptversion** und **Nebenversion** werden manuell in `azure-pipelines.yml` gesetzt:

```yaml
variables:
  MAJOR_VERSION: '1'
  MINOR_VERSION: '5'
```

Alternativ lassen sich diese Werte im Azure DevOps UI unter **Pipelines → Edit → Variables** überschreiben, ohne einen Commit zu benötigen – sinnvoll bei Releases.

Das Skript [`scripts/generate_version_info.py`](scripts/generate_version_info.py) kann auch lokal aufgerufen werden:

```bash
python scripts/generate_version_info.py 1 5 42
# → erzeugt version_info.txt mit Version 1.5.42
```

### Lokaler Build mit Docker

```bash
# Tests ausführen und Wheel bauen
docker build --target builder -t ini-file-editor-build .

# Headless-Export aus der Kommandozeile
docker build -t ini-file-editor .
docker run --rm -v $(pwd)/example.ini:/data/file.ini ini-file-editor /data/file.ini json
docker run --rm -v $(pwd)/example.ini:/data/file.ini ini-file-editor /data/file.ini yaml
```

---

## Lizenz

MIT License – siehe [LICENSE](LICENSE).
