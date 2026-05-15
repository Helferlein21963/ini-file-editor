# Benutzerhandbuch – INI-File-Editor

Ein kommentarerhaltender INI-Datei-Editor mit grafischer Oberfläche, flexibler Sortierung, Dateivergleich und Export in mehrere Formate.

---

## Inhaltsverzeichnis

1. [Programmstart](#1-programmstart)
2. [Oberfläche im Überblick](#2-oberfläche-im-überblick)
3. [Dateien öffnen und anlegen](#3-dateien-öffnen-und-anlegen)
4. [Struktur-Übersicht (Baum)](#4-struktur-übersicht-baum)
5. [Abschnitte und Einträge bearbeiten](#5-abschnitte-und-einträge-bearbeiten)
6. [Vorschau und Export-Formate](#6-vorschau-und-export-formate)
7. [Sortierung](#7-sortierung)
8. [Suchen und Ersetzen](#8-suchen-und-ersetzen)
9. [Dateien vergleichen (Diff)](#9-dateien-vergleichen-diff)
10. [Mehrere Dateien zusammenführen (Merge)](#10-mehrere-dateien-zusammenführen-merge)
11. [Rückgängig und Wiederholen](#11-rückgängig-und-wiederholen)
12. [Sprache wechseln](#12-sprache-wechseln)
13. [Tastaturkürzel](#13-tastaturkürzel)
14. [Hinweise zu Zeichenkodierungen](#14-hinweise-zu-zeichenkodierungen)
15. [Umgang mit Duplikaten (Win32-Konvention)](#15-umgang-mit-duplikaten-win32-konvention)

---

## 1. Programmstart
Ausführen der Executable oder des Projekts mit

```bash
python main.py
```

Beim Start öffnet sich das Hauptfenster mit einem leeren, unbenannten Dokument.

---

## 2. Oberfläche im Überblick

```
┌─────────────────────────────────────────────────────────────────┐
│  Menüleiste:  Datei │ Bearbeiten │ Ansicht │ Hilfe              │
│  Werkzeugleiste:  📁 Öffnen  💾 Speichern  🔀 Vergleichen       │
│                   ⤵ Exportieren  ➕ Abschnitt  ✏️ Abschnitt    │
│                   ➕ Schlüssel  ✏️ Eintrag                      │
├──────────────┬──────────────────────┬───────────────────────────┤
│  🔀 Sortie-  │  📋 Export-Format   │  🌍 Sprache               │
│  rung        │  INI ▼  ⤵ Export   │  Deutsch ▼                │
├──────────────┴──────────────────────┴───────────────────────────┤
│  [Tab 1: datei.ini] [Tab 2: andere.ini] [Tab 3: ⇔ Vergleich]   │
├─────────────────────────┬───────────────────────────────────────┤
│  📋 Struktur-Übersicht  │  👁 Vorschau  │  📝 Header-Kommentare │
│                         │                                        │
│  ▼ [database]           │  ; Kommentar                          │
│      host = localhost   │  [database]                           │
│      port = 5432        │  host = localhost                     │
│  ▼ [logging]            │  port = 5432                          │
│      level = INFO       │                                        │
└─────────────────────────┴───────────────────────────────────────┘
│  🔍 Suchleiste (Strg+F, ausgeblendet bis zur Aktivierung)       │
└─────────────────────────────────────────────────────────────────┘
```

**Linke Seite** – Struktur-Übersicht: Alle Abschnitte und Schlüssel als aufklappbarer Baum.

**Rechte Seite** – zwei Reiter:
- **Vorschau**: Live-Darstellung der Datei im gewählten Format mit Syntax-Highlighting.
- **Header-Kommentare**: Globale Kommentare am Dateianfang (vor dem ersten Abschnitt).

**Steuerleiste oben**: Sortierung, Export-Format und Sprache.

---

## 3. Dateien öffnen und anlegen

### Neue Datei erstellen

- Menü **Datei → Neu** (`Strg+N`) – ersetzt den Inhalt des aktiven Tabs.
- Menü **Datei → Neuer Tab** (`Strg+T`) – öffnet einen weiteren leeren Tab.

### Datei öffnen

- Menü **Datei → Öffnen** (`Strg+O`) – öffnet eine INI-Datei im aktuellen Tab.
- Menü **Datei → In neuem Tab öffnen** (`Strg+Umschalt+O`) – öffnet in einem separaten Tab.
- **Drag & Drop**: Eine oder mehrere `.ini`-, `.cfg`- oder `.conf`-Dateien direkt ins Fenster ziehen.

> **Zeichenkodierung**: Der Editor erkennt UTF-8, UTF-8-BOM, Windows-ANSI (cp1252) und latin-1 automatisch. Es ist keine manuelle Auswahl notwendig.

> **Fortschrittsanzeige**: Beim Laden großer Dateien erscheint rechts in der Statusleiste eine Fortschrittsleiste, die Parser- und UI-Aufbau-Phasen abbildet.

> **Duplikat-Erkennung**: Werden beim Parsen doppelte Sections oder Keys gefunden (siehe [Kapitel 15](#15-umgang-mit-duplikaten-win32-konvention)), zeigt die Statusleiste einen Hinweis und die betroffenen Zeilen werden in Strukturübersicht und Vorschau hervorgehoben.

### Datei speichern

- **Speichern** (`Strg+S`) – speichert die Datei am ursprünglichen Ort als INI.
- **Speichern als** (`Strg+Umschalt+S`) – wählt einen neuen Speicherort.

Tabs mit ungespeicherten Änderungen werden mit einem **`*`** im Titel markiert. Beim Schließen eines solchen Tabs erscheint eine Sicherheitsabfrage.

### Tab schließen

- Klick auf das **×** im Tab-Reiter.
- Menü **Datei → Tab schließen** (`Strg+W`).

---

## 4. Struktur-Übersicht (Baum)

Der Baum auf der linken Seite zeigt die Datei hierarchisch:

```
▼ [database]                ← Abschnitt (fett, klickbar)
      host    localhost      ← Schlüssel │ Wert │ Kommentar
      port    5432
▼ [logging]
      level   INFO          ; Logging-Level
```

**Spalten**: Schlüssel / Abschnitt | Wert | Kommentar | Duplikat-Symbol

Die schmale letzte Spalte ohne Header zeigt die Duplikat-Rolle: **★** für das erste Vorkommen (was Win32 sieht, fett dargestellt) und **↓** für geschattete Duplikate (kursiv dargestellt). Die Zeile ist zusätzlich farblich hinterlegt (gelblich/rötlich). Details siehe [Kapitel 15](#15-umgang-mit-duplikaten-win32-konvention).

**Navigation**:
- Klick auf den Pfeil `▼` / `▶` klappt einen Abschnitt auf oder zu.
- **Alle aufklappen/einklappen**: Menü **Ansicht → Alle aufklappen / Alle einklappen**.

**Synchronisiertes Scrollen** (nur im INI-Format): Wenn man im Baum scrollt, springt die Vorschau zur entsprechenden Stelle – und umgekehrt.

---

## 5. Abschnitte und Einträge bearbeiten

### Bearbeiten per Doppelklick

- **Doppelklick auf einen Abschnitt** → Öffnet den Abschnitts-Dialog.
- **Doppelklick auf einen Eintrag** → Öffnet den Eintrags-Dialog.

### Bearbeiten per Kontextmenü, Menü oder Werkzeugleiste

Rechtsklick auf einen Abschnitt oder Eintrag öffnet ein Menü mit:

| Aktion | Beschreibung |
|---|---|
| ➕ Abschnitt hinzufügen | Neuen Abschnitt am Ende anlegen |
| ✏️ Abschnitt bearbeiten | Name und Kommentare des Abschnitts ändern |
| ➕ Schlüssel hinzufügen | Neuen Eintrag im gewählten Abschnitt anlegen |
| ✏️ Eintrag bearbeiten | Schlüssel, Wert und Kommentare ändern |
| 🗑️ Abschnitt löschen | Abschnitt mit allen Einträgen entfernen |
| 🗑️ Eintrag löschen | Einzelnen Schlüssel entfernen |

Die vier Bearbeiten-Aktionen (Abschnitt hinzufügen / Abschnitt bearbeiten / Schlüssel hinzufügen / Eintrag bearbeiten) sind zusätzlich im Menü **Bearbeiten** und in der Werkzeugleiste verfügbar. Sie sind **kontextabhängig** und werden abgedimmt dargestellt, wenn sie auf die aktuelle Auswahl nicht angewendet werden können:

| Auswahl | ➕ Abschnitt | ✏️ Abschnitt | ➕ Schlüssel | ✏️ Eintrag |
|---|:---:|:---:|:---:|:---:|
| nichts ausgewählt | aktiv | aus | aus | aus |
| Abschnitt | aktiv | aktiv | aktiv | aus |
| Eintrag | aktiv | aktiv¹ | aktiv² | aktiv |
| Compare-Tab aktiv | aus | aus | aus | aus |

¹ Bei einem markierten Eintrag bearbeitet **✏️ Abschnitt bearbeiten** die übergeordnete Section.  
² Der neue Schlüssel wird in die übergeordnete Section des markierten Eintrags eingefügt.

### Eintrags-Dialog

```
Schlüssel:            [timeout              ]
Wert:                 [30                   ]
Inline-Kommentar:     [Timeout in Sekunden  ]
Vorherige Kommentare: [; Netzwerk-Einstellung]
                      [; bitte nicht ändern  ]
```

- **Inline-Kommentar**: Kommentar am Ende der Zeile, z. B. `timeout = 30  ; Sekunden`
- **Vorherige Kommentare**: Kommentarzeilen direkt über dem Eintrag (eine pro Zeile)

### Abschnitts-Dialog

```
Abschnittsname:            [database              ]
Kommentare (vor Header):   [; Datenbankverbindung  ]
Kommentare (nach Einträgen):[; Ende Datenbankconfig]
```

### Header-Kommentare bearbeiten

Im rechten Reiter **📝 Header-Kommentare** können globale Kommentare am Dateianfang (vor dem ersten Abschnitt) frei bearbeitet werden.

---

## 6. Vorschau und Export-Formate

Die **Vorschau** rechts zeigt die Datei live im gewählten Format. Das Format wird über das Dropdown **📋 Export-Format** oben ausgewählt.

### Verfügbare Formate

| Format | Beschreibung |
|---|---|
| **INI** | Originalformat mit allen Kommentaren und korrekter Struktur |
| **JSON** | Kompaktes JSON: `{ "abschnitt": { "schlüssel": "wert" } }` |
| **XML** | Valides XML mit `<configuration><section><entry>` |
| **YAML** | Lesbares YAML (erfordert PyYAML) |

> **Hinweis**: Kommentare sind nur im INI-Format erhalten. JSON, XML und YAML enthalten ausschließlich Schlüssel-Wert-Paare.

> **Duplikat-Hervorhebung im INI-Format**: Doppelte Section-Header und doppelte Keys werden in der Vorschau farbig unterlegt — gelblich für das erste Vorkommen, rötlich für die geschatteten Duplikate. In JSON/XML/YAML entfällt das, da diese Formate Wörterbuch-Semantik haben und Duplikate gar nicht abbilden können. Siehe [Kapitel 15](#15-umgang-mit-duplikaten-win32-konvention).

### Datei exportieren

1. Format im Dropdown auswählen.
2. Auf **⤵ Exportieren** klicken oder Menü **Datei → Exportieren** (`Strg+E`).
3. Speicherort und Dateiname wählen.

Die Sortierung (sofern aktiv) wird beim Export übernommen.

---

## 7. Sortierung

Das Dropdown **🔀 Sortierung** oben links steuert die Reihenfolge in Baum und Vorschau:

| Option | Wirkung |
|---|---|
| Keine Sortierung | Originalreihenfolge der Datei |
| Abschnitte alphabetisch | Abschnitte von A–Z, Einträge in Originalreihenfolge |
| Schlüssel alphabetisch | Originalreihenfolge der Abschnitte, Schlüssel von A–Z |
| Abschnitte & Schlüssel alphabetisch | Beides alphabetisch |

> Die Sortierung verändert **nicht** die Originaldatei. Sie wirkt sich auf die Vorschau und den Export aus. Erst beim Speichern wird die gewählte Reihenfolge festgeschrieben.

---

## 8. Suchen und Ersetzen

### Suchen

`Strg+F` öffnet die Suchleiste am unteren Rand.

```
🔍 Suchtext: [________] ◀ ▶  □ Groß-/Kleinschreibung  3 Treffer gefunden  ✖
```

- **◀ / ▶**: vorheriger / nächster Treffer
- **Enter**: nächster Treffer
- **Escape**: Suchleiste schließen
- Die Suche arbeitet auf dem **Vorschau-Text** im INI-Format.

### Suchen & Ersetzen

`Strg+H` öffnet zusätzlich die Ersetzen-Zeile:

```
Ersetzen durch: [________]  [Ersetzen]  [Alle ersetzen]
```

- **Ersetzen**: ersetzt den aktuell markierten Treffer und springt zum nächsten.
- **Alle ersetzen**: ersetzt alle Vorkommen auf einmal. Die Anzahl der Ersetzungen wird angezeigt.

> Nach dem Ersetzen wird der Text neu geparst und der Baum aktualisiert.

---

## 9. Dateien vergleichen (Diff)

Der Diff-Modus vergleicht zwei geöffnete Dokumente Abschnitt für Abschnitt und Eintrag für Eintrag.

### Vergleich starten

1. Mindestens **zwei Dateien** in separaten Tabs öffnen.
2. Menü **Bearbeiten → 🔀 Dateien vergleichen**.
3. Im Dialog Datei A (links) und Datei B (rechts) auswählen.
4. Ein neuer Tab `⇔ A ↔ B` öffnet sich.

### Diff-Ansicht

```
A: config_prod.ini                                B: config_test.ini
□ Nur Unterschiede zeigen  🔀 Sortierung: Keine Sortierung ▼   2 geändert · 1 hinzugefügt
┌────────────────────┬───────────────┬───────────────┬────┬─────────┐
│ Abschnitt/Schlüssel│ Wert A        │ Wert B        │    │ Duplikat│
│                    │               │               │    │ (Win32) │
├────────────────────┼───────────────┼───────────────┼────┼─────────┤
│ [database]         │               │               │  ＝ │         │
│   host             │ prod-db.int   │ test-db.int   │  ≠ │         │
│   port             │ 5432          │ 5432          │  ＝ │         │
│ [cache]            │               │               │  ＋ │         │  ← nur in B
│ [application]      │               │               │  ＝ │   ★    │  ← Duplikat-Winner
│   name             │ App           │ App           │  ＝ │   ★    │     (fett)
│   name             │               │ ThomasIni     │  ＋ │   ↓    │  ← geschattetes
└────────────────────┴───────────────┴───────────────┴────┴─────────┘     Duplikat (kursiv)
```

### Farbkodierung (Diff-Status)

| Farbe | Bedeutung | Symbol |
|---|---|---|
| Grün | Nur in Datei B vorhanden (hinzugefügt) | ＋ |
| Rot | Nur in Datei A vorhanden (entfernt) | － |
| Gelb | Wert unterschiedlich (geändert) | ≠ |
| Keine | Identisch | ＝ |

### Duplikat-Spalte „Duplikat (Win32-Aufruf)"

Diese zusätzliche Spalte am rechten Rand zeigt, wie sich Win32-Anwendungen (`GetPrivateProfileString`) bei doppelten Sections oder Keys verhalten:

| Symbol | Schrift | Bedeutung |
|---|---|---|
| **★** | fett | Erstes Vorkommen — das, was Win32 tatsächlich liest |
| **↓** | kursiv | Geschattetes Duplikat — physisch in der Datei, aber für Win32 unsichtbar |
| (leer) | normal | Eindeutiger Eintrag, kein Duplikat |

Im Diff-Tab wird die Duplikat-Rolle bewusst **ohne** Hintergrundfarbe dargestellt, damit sie nicht mit der Diff-Status-Farbe (Grün/Rot/Gelb) kollidiert. Der Vergleich pairt die N-te Instanz aus A mit der N-ten Instanz aus B — eine geschattete Zeile zeigt also den *tatsächlichen* Wert dieses Vorkommens und nicht den Winner-Wert. Mehr dazu in [Kapitel 15](#15-umgang-mit-duplikaten-win32-konvention).

### Optionen im Diff-Tab

**Nur Unterschiede zeigen**: Blendet identische Einträge aus, sodass nur Abweichungen sichtbar bleiben.

**Sortierung**: Unabhängig vom Quell-Tab kann für den Vergleich eine Sortierung gewählt werden. So lassen sich z. B. zwei Dateien mit unterschiedlicher Schlüsselreihenfolge rein inhaltlich vergleichen.

### Suchen im Diff

`Strg+F` öffnet eine eingebettete Suchleiste direkt im Diff-Tab:

```
Suchtext: [________] ◀ ▶  □ Groß-/Kleinschreibung  5 Treffer gefunden (2/5)  ✖
```

Die Suche durchsucht Abschnittsnamen, Schlüsselnamen und Werte in allen Spalten.

### Live-Aktualisierung

Der Diff-Tab aktualisiert sich automatisch, sobald eine der Quelldateien bearbeitet wird.

---

## 10. Mehrere Dateien zusammenführen (Merge)

Mit der Merge-Funktion können mehrere INI-Dateien zu einem einzigen Dokument kombiniert werden.

1. Menü **Bearbeiten → 🔁 Mehrere Dateien zusammenführen**.
2. Eine oder mehrere INI-Dateien auswählen (Mehrfachauswahl möglich).
3. Alle Abschnitte und Einträge werden in das aktive Dokument eingebunden.

> **First-wins beim Merge**: Bereits vorhandene Schlüssel im Zieldokument bleiben unverändert — die Merge-Funktion fügt nur fehlende Einträge hinzu. Dieses Verhalten entspricht der Win32-Konvention (siehe [Kapitel 15](#15-umgang-mit-duplikaten-win32-konvention)) und sorgt dafür, dass beim Zusammenführen mehrerer Konfigurationsstände die zuerst geladene Variante die maßgebliche bleibt. Werden mehrere Dateien in einen leeren Tab gemergt, gewinnt die zuerst geladene Datei — `QFileDialog` gibt Mehrfachauswahlen in der Regel alphabetisch sortiert zurück, sodass typischerweise die alphabetisch früheste Datei die maßgebliche bleibt.

---

## 11. Rückgängig und Wiederholen

| Aktion | Kürzel |
|---|---|
| Rückgängig | `Strg+Z` |
| Wiederholen | `Strg+Y` |

Jeder Bearbeitungsschritt (Hinzufügen, Löschen, Bearbeiten, Ersetzen) wird als Snapshot gespeichert. Die History wird beim Schließen des Tabs verworfen.

---

## 12. Sprache wechseln

Das Dropdown **🌍 Sprache** oben rechts schaltet die gesamte Oberfläche sofort um:

- **Deutsch**
- **English**

---

## 13. Tastaturkürzel

| Aktion | Windows / Linux | macOS |
|---|---|---|
| Neu | `Strg+N` | `Cmd+N` |
| Neuer Tab | `Strg+T` | `Cmd+T` |
| Öffnen | `Strg+O` | `Cmd+O` |
| In neuem Tab öffnen | `Strg+Umschalt+O` | `Cmd+Shift+O` |
| Speichern | `Strg+S` | `Cmd+S` |
| Speichern als | `Strg+Umschalt+S` | `Cmd+Shift+S` |
| Tab schließen | `Strg+W` | `Cmd+W` |
| Beenden | `Strg+Q` | `Cmd+Q` |
| Rückgängig | `Strg+Z` | `Cmd+Z` |
| Wiederholen | `Strg+Y` | `Cmd+Y` |
| Suchen | `Strg+F` | `Cmd+F` |
| Suchen & Ersetzen | `Strg+H` | `Cmd+H` |
| Suchleiste schließen | `Escape` | `Escape` |

---

## 14. Hinweise zu Zeichenkodierungen

Der Editor erkennt die Kodierung einer Datei automatisch beim Öffnen und probiert der Reihe nach:

| Reihenfolge | Kodierung | Typischer Einsatz |
|---|---|---|
| 1 | UTF-8 mit BOM | Windows-Tools, die BOM schreiben |
| 2 | UTF-8 | Standard auf Linux, macOS, moderne Windows-Tools |
| 3 | Windows-1252 (ANSI) | Ältere Windows-Programme, deutsche Sonderzeichen |
| 4 | Latin-1 | Westeuropäische Systeme, universeller Fallback |

Gespeichert wird immer als **UTF-8** (ohne BOM). Wer eine ANSI-Datei bearbeitet und speichert, erhält danach eine UTF-8-Datei – der Inhalt bleibt korrekt erhalten.

> Sonderzeichen wie `ä`, `ö`, `ü`, `ß` und `€` aus ANSI-Dateien werden korrekt erkannt und angezeigt.

---

## 15. Umgang mit Duplikaten (Win32-Konvention)

INI-Dateien werden in der Praxis häufig von Win32-Anwendungen über `GetPrivateProfileString` gelesen. Diese API hat eine sehr spezifische Semantik bei doppelten Sections und doppelten Keys, die der Editor exakt nachbildet — denn was beim Bearbeiten in der GUI sichtbar ist, soll dem entsprechen, was die produktive Anwendung später tatsächlich liest.

### Was Win32 tatsächlich sieht

`GetPrivateProfileString` durchsucht die Datei sequentiell von oben und liefert **den ersten Treffer**:

1. Die erste `[section]` mit dem gesuchten Namen wird gefunden.
2. Innerhalb dieser Section wird der erste passende Key zurückgegeben.
3. **Findet der Key dort nicht, wird *nicht* in einer späteren gleichnamigen Section weitergesucht** — es kommt der Default-Wert zurück.

Konsequenz: Ein zweiter Block `[foo]` mit komplett anderen Keys ist für Win32 **unsichtbar**, solange seine Keys nicht zufällig auch im ersten Block existieren.

### Wie der Editor das abbildet

| Aspekt | Verhalten |
|---|---|
| **Parsen** | Duplizierte Sections und Keys bleiben verbatim erhalten — als separate `IniSection`/`IniEntry`-Instanzen im Datenmodell. Es wird *nichts* still zusammengeführt. |
| **Lookup** | `IniDocument.get_section(name)` und `IniSection.get_entry(key)` liefern den **ersten** Treffer (genau wie Win32). Auch `set_entry` und `remove_entry` arbeiten nur auf dem ersten Vorkommen. |
| **Round-Trip** | Beim Speichern wird die Datei byte-für-byte rekonstruiert, inklusive aller Duplikate. Es geht nichts verloren. |
| **Erkennung** | Während des Parsens werden Duplikate in `IniDocument.duplicates` als `DuplicateRecord(kind, section, key, line)` aufgezeichnet. Die GUI fragt diese Liste ab, um den Anwender zu informieren. |

### Visuelle Markierung in der GUI

Sobald Duplikate erkannt werden, kommuniziert der Editor das gleichzeitig auf drei Wegen:

1. **Statusleiste** unten zeigt „N Duplikat(e) erkannt — betroffene Zeilen sind in Vorschau und Strukturansicht hervorgehoben."
2. **Strukturübersicht (Tree)**: Betroffene Zeilen bekommen einen farbigen Hintergrund und ein Symbol in der schmalen letzten Spalte:
   - **★** (fett) auf gelblichem Hintergrund — *Winner*, das was Win32 sieht
   - **↓** (kursiv) auf rötlichem Hintergrund — *Shadowed*, für Win32 unsichtbar
3. **Vorschau** (nur INI-Format): Die entsprechenden Zeilen werden ebenfalls hinterlegt — gelb für den Winner, rot für jedes geschattete Duplikat.

Wenn Sie über eine markierte Zeile hovern, erklärt ein Tooltip die Bedeutung.

### Beispiel

```ini
[application]
name = MeineApp
session_timeout = 60          ; ← Winner: das sieht Win32
session_timeout = 90          ; ← Shadowed: für Win32 unsichtbar
secret_key = abc

[network]                     ; ← Winner-Section
host = prod-server-01

[network]                     ; ← Shadowed-Section: kompletter Block für Win32 unsichtbar
failover_host = prod-server-02
timeout = 99
```

In diesem Beispiel:
- Win32-Lookup `application/session_timeout` liefert `60` (nicht `90`).
- Win32-Lookup `network/host` liefert `prod-server-01`.
- Win32-Lookup `network/failover_host` liefert den **Default-Wert** — die zweite `[network]`-Section ist komplett unsichtbar, obwohl sie in der Datei steht.

### Verhalten beim Vergleich (Diff)

Der Diff-Modus berücksichtigt Win32-Semantik bei der Wertvergleichs-Logik: Es wird die N-te Instanz aus Datei A mit der N-ten Instanz aus Datei B verglichen (Pairing per Occurrence-Index). Praktische Folge:

- Hat A `name = MyApp` einmal und B hat `name = MyApp` plus `name = ThomasIni`, dann erscheinen im Diff **zwei** `name`-Zeilen: die erste als Winner (★, beide gleich), die zweite als Shadowed (↓) mit `ThomasIni` auf der B-Seite.
- Geschattete Werte werden also explizit angezeigt — nicht durch den Winner-Wert maskiert.

### Verhalten beim Speichern/Export

- **INI-Export**: Round-trip-treu, Duplikate bleiben.
- **JSON / XML / YAML**: Diese Formate haben Dictionary-Semantik und können Duplikate gar nicht abbilden. Beim Export gewinnt der erste Eintrag (Win32-konform); spätere gleichnamige Einträge gehen verloren. Das ist beabsichtigt — ein JSON-Konsument soll denselben Wert sehen wie ein Win32-Konsument.

### Wann sind Duplikate problematisch?

Doppelte Einträge entstehen oft unbeabsichtigt, z.B. durch nachträgliches Anhängen von Patches an eine Datei. Sie sind nicht zwingend ein Fehler — der Editor erlaubt sie bewusst, weil sie in Bestandskonfigurationen vorkommen und manchmal als Form von Dokumentation dienen („alter Wert noch sichtbar, neuer Wert aktiv"). Wer Duplikate aktiv loswerden will, kann sie in der Strukturübersicht über das Kontextmenü löschen.