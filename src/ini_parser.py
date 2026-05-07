"""
ini_parser.py – Comment-preserving INI parser with sorting and export capabilities.
"""
from __future__ import annotations

import json
import re
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class SortMode(Enum):
    NONE = auto()
    SECTIONS_ALPHA = auto()
    KEYS_ALPHA = auto()
    SECTIONS_AND_KEYS_ALPHA = auto()


class ExportFormat(Enum):
    INI = "ini"
    JSON = "json"
    XML = "xml"
    YAML = "yaml"


@dataclass
class IniEntry:
    """A single key=value pair with optional inline comment and preceding comment lines."""
    key: str
    value: str
    preceding_comments: list[str] = field(default_factory=list)
    inline_comment: str = ""

    def clone(self) -> "IniEntry":
        return IniEntry(
            key=self.key,
            value=self.value,
            preceding_comments=list(self.preceding_comments),
            inline_comment=self.inline_comment,
        )


@dataclass
class IniSection:
    """A [section] with its header comments, entries, and trailing comment block."""
    name: str
    preceding_comments: list[str] = field(default_factory=list)
    entries: list[IniEntry] = field(default_factory=list)
    trailing_comments: list[str] = field(default_factory=list)

    def clone(self) -> "IniSection":
        return IniSection(
            name=self.name,
            preceding_comments=list(self.preceding_comments),
            entries=[e.clone() for e in self.entries],
            trailing_comments=list(self.trailing_comments),
        )

    def get_entry(self, key: str) -> Optional[IniEntry]:
        for e in self.entries:
            if e.key == key:
                return e
        return None

    def set_entry(self, key: str, value: str, inline_comment: str = "") -> None:
        for e in self.entries:
            if e.key == key:
                e.value = value
                e.inline_comment = inline_comment
                return
        self.entries.append(IniEntry(key=key, value=value, inline_comment=inline_comment))

    def remove_entry(self, key: str) -> bool:
        for i, e in enumerate(self.entries):
            if e.key == key:
                del self.entries[i]
                return True
        return False


@dataclass
class IniDocument:
    """Full parsed INI document."""
    header_comments: list[str] = field(default_factory=list)
    sections: list[IniSection] = field(default_factory=list)
    trailing_comments: list[str] = field(default_factory=list)
    source_path: Optional[Path] = field(default=None, repr=False)

    # ------------------------------------------------------------------ #
    # Lookup helpers
    # ------------------------------------------------------------------ #
    def get_section(self, name: str) -> Optional[IniSection]:
        for s in self.sections:
            if s.name == name:
                return s
        return None

    def get_or_create_section(self, name: str) -> IniSection:
        sec = self.get_section(name)
        if sec is None:
            sec = IniSection(name=name)
            self.sections.append(sec)
        return sec

    def remove_section(self, name: str) -> bool:
        for i, s in enumerate(self.sections):
            if s.name == name:
                del self.sections[i]
                return True
        return False

    def merge_from(self, other: "IniDocument") -> None:
        if not self.header_comments and other.header_comments:
            self.header_comments = list(other.header_comments)

        for other_sec in other.sections:
            target_sec = self.get_section(other_sec.name)
            if target_sec is None:
                self.sections.append(other_sec.clone())
                continue

            for other_entry in other_sec.entries:
                if target_sec.get_entry(other_entry.key) is None:
                    target_sec.entries.append(other_entry.clone())

        if not self.trailing_comments and other.trailing_comments:
            self.trailing_comments = list(other.trailing_comments)

    # ------------------------------------------------------------------ #
    # Sorting
    # ------------------------------------------------------------------ #
    def sorted_copy(self, mode: SortMode) -> "IniDocument":
        doc = IniDocument(
            header_comments=list(self.header_comments),
            trailing_comments=list(self.trailing_comments),
            source_path=self.source_path,
        )
        sections = [s.clone() for s in self.sections]

        if mode in (SortMode.SECTIONS_ALPHA, SortMode.SECTIONS_AND_KEYS_ALPHA):
            sections.sort(key=lambda s: s.name.lower())

        if mode in (SortMode.KEYS_ALPHA, SortMode.SECTIONS_AND_KEYS_ALPHA):
            for s in sections:
                s.entries.sort(key=lambda e: e.key.lower())

        doc.sections = sections
        return doc

    # ------------------------------------------------------------------ #
    # Export
    # ------------------------------------------------------------------ #
    def to_ini_string(self) -> str:
        lines: list[str] = []

        for c in self.header_comments:
            lines.append(c)
        if self.header_comments:
            lines.append("")

        for sec in self.sections:
            for c in sec.preceding_comments:
                lines.append(c)
            lines.append(f"[{sec.name}]")
            for entry in sec.entries:
                for c in entry.preceding_comments:
                    lines.append(c)
                if entry.inline_comment:
                    lines.append(f"{entry.key} = {entry.value}  {entry.inline_comment}")
                else:
                    lines.append(f"{entry.key} = {entry.value}")
            for c in sec.trailing_comments:
                lines.append(c)
            lines.append("")

        for c in self.trailing_comments:
            lines.append(c)

        return "\n".join(lines).rstrip() + "\n"

    def to_json_string(self, indent: int = 2) -> str:
        data: dict = {}
        for sec in self.sections:
            data[sec.name] = {e.key: e.value for e in sec.entries}
        return json.dumps(data, indent=indent, ensure_ascii=False)

    def to_xml_string(self) -> str:
        root = ET.Element("configuration")
        for sec in self.sections:
            sec_el = ET.SubElement(root, "section", name=sec.name)
            for entry in sec.entries:
                entry_el = ET.SubElement(sec_el, "entry", key=entry.key)
                entry_el.text = entry.value
        raw = ET.tostring(root, encoding="unicode")
        dom = minidom.parseString(raw)
        return dom.toprettyxml(indent="  ")

    def to_yaml_string(self) -> str:
        if not YAML_AVAILABLE:
            raise RuntimeError("PyYAML is not installed. Run: pip install pyyaml")
        data: dict = {}
        for sec in self.sections:
            data[sec.name] = {e.key: e.value for e in sec.entries}
        return yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)

    def export(self, fmt: ExportFormat) -> str:
        if fmt == ExportFormat.INI:
            return self.to_ini_string()
        if fmt == ExportFormat.JSON:
            return self.to_json_string()
        if fmt == ExportFormat.XML:
            return self.to_xml_string()
        if fmt == ExportFormat.YAML:
            return self.to_yaml_string()
        raise ValueError(f"Unknown format: {fmt}")


# ------------------------------------------------------------------ #
# Parser
# ------------------------------------------------------------------ #
_SECTION_RE = re.compile(r"^\[([^\]]+)\]")
_KV_RE = re.compile(r"^([^=]+)=(.*)$")
_COMMENT_RE = re.compile(r"^[;#]")
_INLINE_COMMENT_RE = re.compile(r"\s{2,}[;#]")


class IniParser:
    """Reads an INI file (or string) into an IniDocument, preserving all comments."""

    @staticmethod
    def parse_file(path: str | Path) -> IniDocument:
        path = Path(path)
        text = path.read_text(encoding="utf-8")
        doc = IniParser.parse_string(text)
        doc.source_path = path
        return doc

    @staticmethod
    def parse_string(text: str) -> IniDocument:
        doc = IniDocument()
        lines = text.splitlines()

        pending_comments: list[str] = []
        current_section: Optional[IniSection] = None

        for raw in lines:
            line = raw.rstrip()

            # Empty line
            if not line.strip():
                if current_section is None:
                    pending_comments.append(line)
                else:
                    pending_comments.append(line)
                continue

            # Comment-only line
            if _COMMENT_RE.match(line.strip()):
                pending_comments.append(line)
                continue

            # Section header
            m = _SECTION_RE.match(line.strip())
            if m:
                sec = IniSection(name=m.group(1).strip(), preceding_comments=pending_comments)
                pending_comments = []
                if current_section is None:
                    # flush header comments (empty lines before first section)
                    doc.header_comments = [c for c in sec.preceding_comments
                                           if not c.strip() or _COMMENT_RE.match(c.strip())]
                    sec.preceding_comments = [c for c in sec.preceding_comments
                                              if c not in doc.header_comments]
                doc.sections.append(sec)
                current_section = sec
                continue

            # Key=value
            m = _KV_RE.match(line)
            if m and current_section is not None:
                key = m.group(1).strip()
                rest = m.group(2)
                inline_match = _INLINE_COMMENT_RE.search(rest)
                if inline_match:
                    value = rest[:inline_match.start()].strip()
                    inline_comment = rest[inline_match.start():].strip()
                else:
                    value = rest.strip()
                    inline_comment = ""
                entry = IniEntry(
                    key=key,
                    value=value,
                    preceding_comments=pending_comments,
                    inline_comment=inline_comment,
                )
                pending_comments = []
                current_section.entries.append(entry)
                continue

            # Anything else treated as a comment
            pending_comments.append(line)

        # Remaining pending comments → trailing
        if pending_comments:
            if current_section:
                current_section.trailing_comments.extend(pending_comments)
            else:
                doc.trailing_comments.extend(pending_comments)

        # If no sections found, put all in header
        if not doc.sections and pending_comments:
            doc.header_comments = pending_comments

        return doc
