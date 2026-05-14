"""Structural diff between two :class:`~ini_parser.IniDocument` instances.

Only the structural payload — sections and ``key=value`` pairs — is compared.
Comments are intentionally ignored so cosmetic changes do not appear as
content diffs.
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
    """Per-entry / per-section diff classification.

    Attributes:
        UNCHANGED: Present in both documents with equal value.
        ADDED: Present in document B only.
        REMOVED: Present in document A only.
        MODIFIED: Present in both, but the value differs (entries) or at
            least one child entry was added, removed, or modified (sections).
    """

    UNCHANGED = auto()
    ADDED = auto()
    REMOVED = auto()
    MODIFIED = auto()


@dataclass
class EntryDiff:
    """Diff record for a single ``key=value`` pair.

    Attributes:
        key: The entry key.
        status: Classification relative to documents A and B.
        value_a: Value in document A, or ``None`` if the entry was added in B.
        value_b: Value in document B, or ``None`` if the entry was removed in B.
    """

    key: str
    status: DiffStatus
    value_a: Optional[str] = None
    value_b: Optional[str] = None


@dataclass
class SectionDiff:
    """Diff record for a single section, with per-entry detail.

    Attributes:
        name: Section name.
        status: Overall section status. A section is ``MODIFIED`` if it
            exists in both documents but any child entry differs.
        entries: Per-entry diff records.
    """

    name: str
    status: DiffStatus
    entries: list[EntryDiff] = field(default_factory=list)


@dataclass
class DocumentDiff:
    """Diff result spanning every section of two compared documents.

    Attributes:
        sections: Per-section diff records in display order — sections of A
            first, then any sections that exist only in B.
    """

    sections: list[SectionDiff] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        """``True`` if any section is not ``UNCHANGED``."""
        return any(s.status != DiffStatus.UNCHANGED for s in self.sections)

    def count_added(self) -> int:
        """Number of entries present only in document B."""
        return sum(1 for s in self.sections for e in s.entries if e.status == DiffStatus.ADDED)

    def count_removed(self) -> int:
        """Number of entries present only in document A."""
        return sum(1 for s in self.sections for e in s.entries if e.status == DiffStatus.REMOVED)

    def count_modified(self) -> int:
        """Number of entries present in both but with a different value."""
        return sum(1 for s in self.sections for e in s.entries if e.status == DiffStatus.MODIFIED)

    def count_unchanged(self) -> int:
        """Number of entries with identical values in both documents."""
        return sum(1 for s in self.sections for e in s.entries if e.status == DiffStatus.UNCHANGED)


class IniDiff:
    """Structural comparator for :class:`~ini_parser.IniDocument` instances."""

    @staticmethod
    def compare(doc_a: IniDocument, doc_b: IniDocument) -> DocumentDiff:
        """Compute a structural diff of two documents.

        Args:
            doc_a: Left-hand side document.
            doc_b: Right-hand side document.

        Returns:
            A :class:`DocumentDiff` whose sections appear in A's order, then
            any sections unique to B in B's order.
        """
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