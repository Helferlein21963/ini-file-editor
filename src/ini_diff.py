"""
ini_diff.py – Structural diff between two IniDocument instances.
Compares only sections and key/value pairs; comments are intentionally ignored.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

try:
    from src.ini_parser import IniDocument
except ModuleNotFoundError:
    from ini_parser import IniDocument  # type: ignore[no-redef]


class DiffStatus(Enum):
    UNCHANGED = auto()
    ADDED = auto()    # exists in B only
    REMOVED = auto()  # exists in A only
    MODIFIED = auto() # exists in both, value differs


@dataclass
class EntryDiff:
    key: str
    status: DiffStatus
    value_a: Optional[str] = None
    value_b: Optional[str] = None


@dataclass
class SectionDiff:
    name: str
    status: DiffStatus
    entries: list[EntryDiff] = field(default_factory=list)


@dataclass
class DocumentDiff:
    sections: list[SectionDiff] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return any(s.status != DiffStatus.UNCHANGED for s in self.sections)

    def count_added(self) -> int:
        return sum(1 for s in self.sections for e in s.entries if e.status == DiffStatus.ADDED)

    def count_removed(self) -> int:
        return sum(1 for s in self.sections for e in s.entries if e.status == DiffStatus.REMOVED)

    def count_modified(self) -> int:
        return sum(1 for s in self.sections for e in s.entries if e.status == DiffStatus.MODIFIED)

    def count_unchanged(self) -> int:
        return sum(1 for s in self.sections for e in s.entries if e.status == DiffStatus.UNCHANGED)


class IniDiff:
    """Compares two IniDocument instances structurally (sections and key/value pairs only)."""

    @staticmethod
    def compare(doc_a: IniDocument, doc_b: IniDocument) -> DocumentDiff:
        result = DocumentDiff()

        names_a = {s.name for s in doc_a.sections}
        # Sections in A first, then B-only sections in B's order
        all_names: list[str] = [s.name for s in doc_a.sections]
        for s in doc_b.sections:
            if s.name not in names_a:
                all_names.append(s.name)

        for name in all_names:
            sec_a = doc_a.get_section(name)
            sec_b = doc_b.get_section(name)

            if sec_b is None:
                assert sec_a is not None
                sec_diff = SectionDiff(name=name, status=DiffStatus.REMOVED)
                for e in sec_a.entries:
                    sec_diff.entries.append(
                        EntryDiff(key=e.key, status=DiffStatus.REMOVED, value_a=e.value)
                    )
            elif sec_a is None:
                sec_diff = SectionDiff(name=name, status=DiffStatus.ADDED)
                for e in sec_b.entries:
                    sec_diff.entries.append(
                        EntryDiff(key=e.key, status=DiffStatus.ADDED, value_b=e.value)
                    )
            else:
                sec_diff = SectionDiff(name=name, status=DiffStatus.UNCHANGED)
                keys_a = {e.key for e in sec_a.entries}
                all_keys: list[str] = [e.key for e in sec_a.entries]
                for e in sec_b.entries:
                    if e.key not in keys_a:
                        all_keys.append(e.key)

                for key in all_keys:
                    entry_a = sec_a.get_entry(key)
                    entry_b = sec_b.get_entry(key)

                    if entry_a is None:
                        assert entry_b is not None
                        sec_diff.entries.append(
                            EntryDiff(key=key, status=DiffStatus.ADDED, value_b=entry_b.value)
                        )
                        sec_diff.status = DiffStatus.MODIFIED
                    elif entry_b is None:
                        sec_diff.entries.append(
                            EntryDiff(key=key, status=DiffStatus.REMOVED, value_a=entry_a.value)
                        )
                        sec_diff.status = DiffStatus.MODIFIED
                    elif entry_a.value != entry_b.value:
                        sec_diff.entries.append(
                            EntryDiff(
                                key=key,
                                status=DiffStatus.MODIFIED,
                                value_a=entry_a.value,
                                value_b=entry_b.value,
                            )
                        )
                        sec_diff.status = DiffStatus.MODIFIED
                    else:
                        sec_diff.entries.append(
                            EntryDiff(
                                key=key,
                                status=DiffStatus.UNCHANGED,
                                value_a=entry_a.value,
                                value_b=entry_b.value,
                            )
                        )

            result.sections.append(sec_diff)

        return result