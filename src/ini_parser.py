"""Comment-preserving INI parser with sorting and multi-format export.

This module exposes the data model (:class:`IniEntry`, :class:`IniSection`,
:class:`IniDocument`) used throughout the application, the :class:`IniParser`
that reads INI text into that model while preserving every comment, and the
:class:`SortMode` / :class:`ExportFormat` enums consumed by the GUI.

Round-trip guarantee: parsing an INI file and serializing it back via
:meth:`IniDocument.to_ini_string` reproduces the original document byte-for-byte
(modulo trailing whitespace).
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
    """Sort strategies applied by :meth:`IniDocument.sorted_copy`.

    Attributes:
        NONE: Preserve original order.
        SECTIONS_ALPHA: Sort sections by name; keep entry order inside each section.
        KEYS_ALPHA: Sort entries inside each section; keep section order.
        SECTIONS_AND_KEYS_ALPHA: Sort both sections and their entries.
    """

    NONE = auto()
    SECTIONS_ALPHA = auto()
    KEYS_ALPHA = auto()
    SECTIONS_AND_KEYS_ALPHA = auto()


class ExportFormat(Enum):
    """Serialization formats supported by :meth:`IniDocument.export`."""

    INI = "ini"
    JSON = "json"
    XML = "xml"
    YAML = "yaml"


class DuplicateKind(Enum):
    """Kind of duplicate detected by :class:`IniParser`."""

    SECTION = "section"
    KEY = "key"


@dataclass
class DuplicateRecord:
    """Record of a duplicate section header or key found during parsing.

    The Win32 ``GetPrivateProfileString`` API only sees the first occurrence
    of a section or key; later duplicates are unreachable. The parser
    preserves them in the model so the source file round-trips byte-for-byte,
    and emits one of these records per duplicate so the GUI can warn the user.

    Attributes:
        kind: Whether the duplicate is a section header or a key within a
            section.
        section: Name of the affected section.
        key: Key name (only for :attr:`DuplicateKind.KEY`; ``None`` for
            section duplicates).
        line: 1-based line number in the source file where the duplicate
            occurred.
    """

    kind: DuplicateKind
    section: str
    key: Optional[str] = None
    line: int = 0


@dataclass
class IniEntry:
    """A single ``key = value`` pair with attached comments.

    Attributes:
        key: The entry key, with leading/trailing whitespace stripped.
        value: The raw value text without the inline comment.
        preceding_comments: Comment lines that appeared immediately above this
            entry in the source file. Used to round-trip comments on export.
        inline_comment: Trailing comment on the same line, including the
            leading ``;`` or ``#`` character. Empty if the source had none.
    """

    key: str
    value: str
    preceding_comments: list[str] = field(default_factory=list)
    inline_comment: str = ""

    def clone(self) -> "IniEntry":
        """Return a deep copy with independent comment lists."""
        return IniEntry(
            key=self.key,
            value=self.value,
            preceding_comments=list(self.preceding_comments),
            inline_comment=self.inline_comment,
        )


@dataclass
class IniSection:
    """An INI ``[section]`` with its entries and comment blocks.

    Attributes:
        name: Section name without the surrounding brackets.
        preceding_comments: Comment / blank lines above the ``[section]`` header.
        entries: Ordered list of key-value pairs in this section.
        trailing_comments: Comment / blank lines after the last entry but
            before the next section header.
    """

    name: str
    preceding_comments: list[str] = field(default_factory=list)
    entries: list[IniEntry] = field(default_factory=list)
    trailing_comments: list[str] = field(default_factory=list)

    def clone(self) -> "IniSection":
        """Return a deep copy including independent entry clones."""
        return IniSection(
            name=self.name,
            preceding_comments=list(self.preceding_comments),
            entries=[e.clone() for e in self.entries],
            trailing_comments=list(self.trailing_comments),
        )

    def get_entry(self, key: str) -> Optional[IniEntry]:
        """Return the first entry matching ``key`` or ``None`` if absent."""
        for e in self.entries:
            if e.key == key:
                return e
        return None

    def set_entry(self, key: str, value: str, inline_comment: str = "") -> None:
        """Insert or update an entry in place.

        Args:
            key: Entry key to set.
            value: New value text.
            inline_comment: Optional inline comment. An existing inline
                comment is overwritten with this value.
        """
        for e in self.entries:
            if e.key == key:
                e.value = value
                e.inline_comment = inline_comment
                return
        self.entries.append(IniEntry(key=key, value=value, inline_comment=inline_comment))

    def remove_entry(self, key: str) -> bool:
        """Remove the first entry matching ``key``.

        Returns:
            ``True`` if an entry was removed, ``False`` if no match was found.
        """
        for i, e in enumerate(self.entries):
            if e.key == key:
                del self.entries[i]
                return True
        return False


@dataclass
class IniDocument:
    """Root container for a parsed INI file.

    Attributes:
        header_comments: Comment / blank lines at the very top of the file,
            before the first ``[section]``.
        sections: Ordered list of :class:`IniSection` instances. Duplicate
            section names are preserved as separate entries so the file
            round-trips byte-for-byte; lookup helpers like
            :meth:`get_section` always return the *first* match, matching
            Win32 ``GetPrivateProfileString`` semantics.
        trailing_comments: Comment / blank lines after the final entry.
        source_path: Original path of the file the document was loaded from,
            or ``None`` for documents created in memory.
        duplicates: Records of duplicate sections or duplicate keys observed
            during parsing. Empty for documents constructed in memory or
            files without duplicates. Used by the GUI to surface a warning;
            consumers may ignore it.
    """

    header_comments: list[str] = field(default_factory=list)
    sections: list[IniSection] = field(default_factory=list)
    trailing_comments: list[str] = field(default_factory=list)
    source_path: Optional[Path] = field(default=None, repr=False)
    duplicates: list[DuplicateRecord] = field(default_factory=list, repr=False)

    # ------------------------------------------------------------------ #
    # Lookup helpers
    # ------------------------------------------------------------------ #
    def get_section(self, name: str) -> Optional[IniSection]:
        """Return the section named ``name`` or ``None`` if absent."""
        for s in self.sections:
            if s.name == name:
                return s
        return None

    def get_or_create_section(self, name: str) -> IniSection:
        """Return the section named ``name``, creating an empty one if needed."""
        sec = self.get_section(name)
        if sec is None:
            sec = IniSection(name=name)
            self.sections.append(sec)
        return sec

    def remove_section(self, name: str) -> bool:
        """Remove the first section matching ``name``.

        Returns:
            ``True`` if a section was removed, ``False`` if no match was found.
        """
        for i, s in enumerate(self.sections):
            if s.name == name:
                del self.sections[i]
                return True
        return False

    def clone(self) -> "IniDocument":
        """Return a deep copy. Sections and entries are cloned recursively."""
        doc = IniDocument(
            header_comments=list(self.header_comments),
            trailing_comments=list(self.trailing_comments),
            source_path=self.source_path,
        )
        doc.sections = [s.clone() for s in self.sections]
        doc.duplicates = [
            DuplicateRecord(kind=d.kind, section=d.section, key=d.key, line=d.line)
            for d in self.duplicates
        ]
        return doc

    def merge_from(self, other: "IniDocument") -> None:
        """Merge another document into ``self`` without overwriting existing keys.

        Sections that already exist gain only the entries whose keys are not
        already present. Header / trailing comments from ``other`` are adopted
        only when ``self`` has none of its own.

        Args:
            other: Document to merge in. ``other`` is not modified.
        """
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
        """Return a sorted clone of this document.

        The original document is never mutated.

        Args:
            mode: Sort strategy to apply. See :class:`SortMode`.

        Returns:
            A new :class:`IniDocument` with sections and/or entries sorted
            according to ``mode``.
        """
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
        """Serialize the document to INI text with all comments preserved.

        Returns:
            The reconstructed INI source as a string with a trailing newline.
        """
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
        """Serialize sections and entries as a nested JSON object.

        Comments are not represented in JSON output.

        Args:
            indent: Number of spaces per indent level.
        """
        data: dict = {}
        for sec in self.sections:
            data[sec.name] = {e.key: e.value for e in sec.entries}
        return json.dumps(data, indent=indent, ensure_ascii=False)

    def to_xml_string(self) -> str:
        """Serialize the document as pretty-printed XML.

        The structure is ``<configuration><section name="..."><entry key="..."/>``.
        Comments are not represented in XML output.
        """
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
        """Serialize the document as YAML.

        Raises:
            RuntimeError: If PyYAML is not installed in the current environment.
        """
        if not YAML_AVAILABLE:
            raise RuntimeError("PyYAML is not installed. Run: pip install pyyaml")
        data: dict = {}
        for sec in self.sections:
            data[sec.name] = {e.key: e.value for e in sec.entries}
        return yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)

    def export(self, fmt: ExportFormat) -> str:
        """Dispatch serialization to the format-specific method.

        Args:
            fmt: Target output format.

        Returns:
            The serialized representation.

        Raises:
            ValueError: If ``fmt`` is not a member of :class:`ExportFormat`.
            RuntimeError: If ``fmt`` is :attr:`ExportFormat.YAML` and PyYAML
                is not installed.
        """
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
    """Reads INI text into an :class:`IniDocument`, preserving every comment.

    The parser is stateless and single-pass. Line classification is purely
    regex-based — no INI-specific lexer is required.
    """

    @staticmethod
    def parse_file(path: str | Path) -> IniDocument:
        """Read and parse an INI file from disk.

        Encoding is auto-detected: the parser tries UTF-8 (with and without
        BOM), then Windows-1252, then Latin-1 as a final fallback (which
        never fails).

        Args:
            path: File-system path to read.

        Returns:
            A populated :class:`IniDocument` whose
            :attr:`IniDocument.source_path` is set to ``path``.
        """
        path = Path(path)
        raw = path.read_bytes()
        for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = raw.decode("latin-1")  # latin-1 never fails
        doc = IniParser.parse_string(text)
        doc.source_path = path
        return doc

    @staticmethod
    def parse_string(text: str) -> IniDocument:
        """Parse INI text into an :class:`IniDocument`.

        Comments accumulate in a pending buffer and are attached to the next
        section or entry encountered. An inline comment is recognised only
        when preceded by two or more spaces, so the equals-sign value text
        is unambiguous.

        Duplicate section headers and duplicate keys within a section are
        preserved verbatim in the model so the file round-trips byte-for-
        byte. Each duplicate is also recorded in
        :attr:`IniDocument.duplicates` so the GUI can warn the user. Lookup
        helpers (:meth:`IniDocument.get_section`,
        :meth:`IniSection.get_entry`) return the *first* match — matching
        the Win32 ``GetPrivateProfileString`` semantics used by consumers
        of these files.

        Args:
            text: Raw INI source. May use ``\\n`` or ``\\r\\n`` line endings.

        Returns:
            The parsed document. :attr:`IniDocument.source_path` is left
            ``None`` — set it manually if needed.
        """
        doc = IniDocument()
        lines = text.splitlines()

        pending_comments: list[str] = []
        current_section: Optional[IniSection] = None
        seen_section_names: set[str] = set()

        for line_idx, raw in enumerate(lines):
            line = raw.rstrip()
            line_no = line_idx + 1

            # Empty line
            if not line.strip():
                pending_comments.append(line)
                continue

            # Comment-only line
            if _COMMENT_RE.match(line.strip()):
                pending_comments.append(line)
                continue

            # Section header
            m = _SECTION_RE.match(line.strip())
            if m:
                sec_name = m.group(1).strip()
                if sec_name in seen_section_names:
                    doc.duplicates.append(DuplicateRecord(
                        kind=DuplicateKind.SECTION,
                        section=sec_name,
                        line=line_no,
                    ))
                seen_section_names.add(sec_name)
                sec = IniSection(name=sec_name, preceding_comments=pending_comments)
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
                if any(e.key == key for e in current_section.entries):
                    doc.duplicates.append(DuplicateRecord(
                        kind=DuplicateKind.KEY,
                        section=current_section.name,
                        key=key,
                        line=line_no,
                    ))
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
