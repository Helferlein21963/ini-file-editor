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
- [DevOps / CI-CD Pipeline](#devops--cicd-pipeline)
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

### GUI (`main_window.py`)

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
git clone https://
cd ini-file-editor

# Virtuelle Umgebung empfohlen
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Option C – vorkompiliertes Binary (Releases-Seite)

Laden Sie das passende Binary von der [DevOps Releases](https://) Seite herunter – kein Python-Setup erforderlich.

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

Bevor die EXE gebaut wird, muss das PNG-Icon in das Windows-ICO-Format konvertiert werden.

```bash
python src/convert_icon.py
```

Das Skript liest `src/icon.png` und schreibt `src/icon.ico`.

### Executable mit PyInstaller bauen

**Voraussetzungen:**
- Virtual Environment aktiviert
- `pyinstaller` installiert: `pip install pyinstaller` (oder `pip install -r requirements-dev.txt`)

**Executable erstellen (empfohlen):**

```bash
python -m pyinstaller --onefile --windowed --add-data "src/logo.png;src" --icon="src/icon.ico" --name ini-file-editor main.py
```

Das Executable wird erstellt in: `dist/ini-file-editor.exe`

**Optionen erklärt:**
- `--onefile` – Alles in eine einzelne `.exe` packen
- `--windowed` – Keine Konsole anzeigen (nur GUI)
- `--add-data "src/logo.png;src"` – Logo-Datei in die Executable einbinden
- `--icon="src/icon.ico"` – EXE-Icon festlegen
- `--name ini-file-editor` – Name des Executables

**Optional – Build mit der `.spec`-Datei:**

```bash
python -m pyinstaller ini-file-editor.spec
```

Hierbei muss `ini-file-editor.spec` die Icon-Datei (`icon='src\\icon.ico'`) und die Daten-Datei `src/logo.png` enthalten.

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
│   └── main_window.py             # PyQt6 GUI (MainWindow, Dialoge, Tree)
├── tests/
│   └── test_ini_parser.py         # 20 Unit-Tests (Parser, Sortierung, Export)
├── example.ini                    # Beispiel-INI (unstrukturiert, mit Kommentaren)
├── requirements.txt               # Laufzeit-Abhängigkeiten
├── requirements-dev.txt           # Entwicklungs- & CI-Abhängigkeiten
├── pyproject.toml                 # Paket-Metadaten, Black, isort, mypy, pytest
├── Dockerfile                     # Multi-Stage Build (Test + Runtime)
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions Pipeline
├── .gitlab-ci.yml                 # GitLab CI Alternative
└── README.md
```

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

## DevOps / CI-CD Pipeline

### GitHub Actions (`.github/workflows/ci.yml`)

Die Pipeline läuft automatisch bei jedem Push und Pull Request:

```
Push / PR
   │
   ├─► lint          black · isort · flake8 · mypy
   │
   ├─► test          Python 3.11 + 3.12  ×  Ubuntu · Windows · macOS
   │                 (Headless via xvfb unter Linux)
   │                 Coverage-Upload zu Codecov
   │
   ├─► build         python -m build  →  sdist + wheel
   │
   ├─► build-exe     PyInstaller  →  Standalone-Binary pro OS
   │
   └─► publish       (nur bei GitHub Release Tag)
                     PyPI via OIDC Trusted Publishing
```

### GitLab CI (`.gitlab-ci.yml`)

Identischer Ablauf, angepasst für GitLab-Infrastruktur mit Cobertura Coverage-Report.

### Lokaler Build mit Docker

```bash
# Tests ausführen und Wheel bauen
docker build --target builder -t ini-file-editor-build .

# Headless-Export aus der Kommandozeile
docker build -t ini-file-editor .
docker run --rm -v $(pwd)/example.ini:/data/file.ini ini-file-editor /data/file.ini json
docker run --rm -v $(pwd)/example.ini:/data/file.ini ini-file-editor /data/file.ini yaml
```

### Umgebungsvariablen für CI

| Variable | Beschreibung | Wo setzen |
|---|---|---|
| `PYPI_TOKEN` | API-Token für PyPI-Upload | GitHub/GitLab Secret |
| `CODECOV_TOKEN` | Codecov Upload-Token | GitHub Secret (optional) |

---

## Beitragen

1. Fork erstellen
2. Feature-Branch: `git checkout -b feature/mein-feature`
3. Änderungen committen: `git commit -m "feat: mein neues Feature"`
4. Formatierung prüfen: `black src/ tests/ && isort src/ tests/`
5. Tests ausführen: `pytest`
6. Pull Request öffnen

---

## Lizenz

MIT License – siehe [LICENSE](LICENSE).
