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
    from src.ini_parser import IniDocument, IniEntry, IniSection
except ModuleNotFoundError:
    from ini_parser import IniDocument, IniEntry, IniSection  # type: ignore[no-redef]


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


class DuplicateRole(Enum):
    """Visual marker for duplicate sections / keys inside a diff result.

    Attributes:
        NONE: The section name (or key) appears at most once on each side —
            no special highlighting.
        WINNER: First occurrence of a name that has 2+ occurrences across
            A and B combined. This is the entry Win32
            ``GetPrivateProfileString`` actually returns.
        SHADOWED: Second or later occurrence — present in the file but
            invisible to Win32 lookups.
    """

    NONE = auto()
    WINNER = auto()
    SHADOWED = auto()


@dataclass
class EntryDiff:
    """Diff record for a single ``key=value`` pair.

    Attributes:
        key: The entry key.
        status: Classification relative to documents A and B. The status
            always reflects a *first-wins* comparison even on shadowed rows,
            so duplicate rows visually mirror their winner.
        value_a: Value in document A, or ``None`` if the entry was added in B.
        value_b: Value in document B, or ``None`` if the entry was removed in B.
        duplicate_role: Whether this row represents a unique entry, the
            first-wins occurrence of a duplicated key, or a shadowed
            duplicate.
    """

    key: str
    status: DiffStatus
    value_a: Optional[str] = None
    value_b: Optional[str] = None
    duplicate_role: DuplicateRole = DuplicateRole.NONE


@dataclass
class SectionDiff:
    """Diff record for a single section, with per-entry detail.

    Attributes:
        name: Section name.
        status: Overall section status. A section is ``MODIFIED`` if it
            exists in both documents but any child entry differs.
        entries: Per-entry diff records.
        duplicate_role: Whether this row represents a unique section, the
            first-wins occurrence of a duplicated section name, or a
            shadowed duplicate.
    """

    name: str
    status: DiffStatus
    entries: list[EntryDiff] = field(default_factory=list)
    duplicate_role: DuplicateRole = DuplicateRole.NONE


@dataclass
class DocumentDiff:
    """Diff result spanning every section of two compared documents.

    Attributes:
        sections: Per-section diff records in display order — sections of A
            first (preserving duplicate occurrences), then any sections that
            exist only in B (also preserving B's duplicates).
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

        Section names and keys with duplicates produce one diff row per
        physical occurrence. Sections are paired between A and B by
        *occurrence index* — A's first ``[foo]`` is compared with B's first
        ``[foo]`` (this is the Win32 first-wins comparison), A's second
        ``[foo]`` with B's second, and so on. If one side has fewer
        occurrences, the excess rows are one-sided (REMOVED / ADDED).

        The :attr:`duplicate_role` on each row marks the row as
        :attr:`DuplicateRole.WINNER` (first occurrence of a name with 2+
        occurrences across A and B), :attr:`DuplicateRole.SHADOWED` (later
        occurrence — invisible to Win32 ``GetPrivateProfileString``), or
        :attr:`DuplicateRole.NONE` (unique). This lets the GUI colour the
        rows yellow / red while keeping the underlying values truthful.

        Args:
            doc_a: Left-hand side document.
            doc_b: Right-hand side document.

        Returns:
            A :class:`DocumentDiff` listing sections in A's order
            (preserving duplicates), then any B-only sections or
            B-excess occurrences in B's order.
        """
        a_total = IniDiff._counts_by_name(s.name for s in doc_a.sections)
        b_total = IniDiff._counts_by_name(s.name for s in doc_b.sections)

        # Pair sections by occurrence index: walk A in order, look up B's
        # matching N-th occurrence; then append B's excess occurrences.
        section_rows: list[tuple[str, Optional[IniSection], Optional[IniSection]]] = []
        b_by_name: dict[str, list[IniSection]] = {}
        for sec in doc_b.sections:
            b_by_name.setdefault(sec.name, []).append(sec)

        a_seen: dict[str, int] = {}
        for sec_a in doc_a.sections:
            idx = a_seen.get(sec_a.name, 0)
            a_seen[sec_a.name] = idx + 1
            b_list = b_by_name.get(sec_a.name, [])
            sec_b = b_list[idx] if idx < len(b_list) else None
            section_rows.append((sec_a.name, sec_a, sec_b))

        b_seen: dict[str, int] = {}
        for sec_b in doc_b.sections:
            idx = b_seen.get(sec_b.name, 0)
            b_seen[sec_b.name] = idx + 1
            if idx >= a_total.get(sec_b.name, 0):
                section_rows.append((sec_b.name, None, sec_b))

        result = DocumentDiff()
        emit_idx: dict[str, int] = {}
        for name, sec_a, sec_b in section_rows:
            occ = emit_idx.get(name, 0)
            emit_idx[name] = occ + 1
            total = max(a_total.get(name, 0), b_total.get(name, 0))
            sec_role = IniDiff._role_for(total, occ)

            if sec_a is not None and sec_b is not None:
                sec_diff = SectionDiff(
                    name=name, status=DiffStatus.UNCHANGED, duplicate_role=sec_role,
                )
                sec_diff.entries.extend(IniDiff._build_compare_entries(sec_a, sec_b))
                if any(e.status != DiffStatus.UNCHANGED for e in sec_diff.entries):
                    sec_diff.status = DiffStatus.MODIFIED
            elif sec_a is not None:
                sec_diff = SectionDiff(
                    name=name, status=DiffStatus.REMOVED, duplicate_role=sec_role,
                )
                sec_diff.entries.extend(IniDiff._build_one_sided_entries(
                    sec_a, side_is_a=True,
                ))
            else:
                assert sec_b is not None
                sec_diff = SectionDiff(
                    name=name, status=DiffStatus.ADDED, duplicate_role=sec_role,
                )
                sec_diff.entries.extend(IniDiff._build_one_sided_entries(
                    sec_b, side_is_a=False,
                ))
            result.sections.append(sec_diff)

        return result

    @staticmethod
    def _counts_by_name(names) -> dict[str, int]:
        out: dict[str, int] = {}
        for n in names:
            out[n] = out.get(n, 0) + 1
        return out

    @staticmethod
    def _role_for(total: int, occurrence: int) -> DuplicateRole:
        """Map a total-occurrences-count and 0-based occurrence to a role."""
        if total <= 1:
            return DuplicateRole.NONE
        return DuplicateRole.WINNER if occurrence == 0 else DuplicateRole.SHADOWED

    @staticmethod
    def _build_one_sided_entries(
        section: IniSection, *, side_is_a: bool,
    ) -> list[EntryDiff]:
        """Build entry rows for a section that exists in only one document.

        Duplicate keys produce one row each so the user can see them; their
        roles follow the same WINNER / SHADOWED scheme.
        """
        counts = IniDiff._counts_by_name(e.key for e in section.entries)
        status = DiffStatus.REMOVED if side_is_a else DiffStatus.ADDED
        seen: dict[str, int] = {}
        out: list[EntryDiff] = []
        for entry in section.entries:
            occ = seen.get(entry.key, 0)
            seen[entry.key] = occ + 1
            role = IniDiff._role_for(counts[entry.key], occ)
            out.append(EntryDiff(
                key=entry.key,
                status=status,
                value_a=entry.value if side_is_a else None,
                value_b=entry.value if not side_is_a else None,
                duplicate_role=role,
            ))
        return out

    @staticmethod
    def _build_compare_entries(
        sec_a: IniSection, sec_b: IniSection,
    ) -> list[EntryDiff]:
        """Pair entries between two specific section instances by occurrence.

        Like the section-level pairing in :meth:`compare`, but for keys
        within a single same-named section pair: A's N-th ``k=`` is paired
        with B's N-th ``k=``. The N-th occurrence's *actual* values drive
        the row's value_a / value_b — shadowed rows therefore show the
        shadowed instance's content, not the winner's value.
        """
        a_total = IniDiff._counts_by_name(e.key for e in sec_a.entries)
        b_total = IniDiff._counts_by_name(e.key for e in sec_b.entries)

        rows: list[tuple[str, Optional[IniEntry], Optional[IniEntry]]] = []
        b_by_key: dict[str, list[IniEntry]] = {}
        for entry in sec_b.entries:
            b_by_key.setdefault(entry.key, []).append(entry)

        a_seen: dict[str, int] = {}
        for entry_a in sec_a.entries:
            idx = a_seen.get(entry_a.key, 0)
            a_seen[entry_a.key] = idx + 1
            b_list = b_by_key.get(entry_a.key, [])
            entry_b = b_list[idx] if idx < len(b_list) else None
            rows.append((entry_a.key, entry_a, entry_b))

        b_seen: dict[str, int] = {}
        for entry_b in sec_b.entries:
            idx = b_seen.get(entry_b.key, 0)
            b_seen[entry_b.key] = idx + 1
            if idx >= a_total.get(entry_b.key, 0):
                rows.append((entry_b.key, None, entry_b))

        out: list[EntryDiff] = []
        emit_idx: dict[str, int] = {}
        for key, ea, eb in rows:
            occ = emit_idx.get(key, 0)
            emit_idx[key] = occ + 1
            total = max(a_total.get(key, 0), b_total.get(key, 0))
            role = IniDiff._role_for(total, occ)

            if ea is None:
                assert eb is not None
                out.append(EntryDiff(
                    key=key, status=DiffStatus.ADDED,
                    value_b=eb.value, duplicate_role=role,
                ))
            elif eb is None:
                out.append(EntryDiff(
                    key=key, status=DiffStatus.REMOVED,
                    value_a=ea.value, duplicate_role=role,
                ))
            elif ea.value != eb.value:
                out.append(EntryDiff(
                    key=key, status=DiffStatus.MODIFIED,
                    value_a=ea.value, value_b=eb.value,
                    duplicate_role=role,
                ))
            else:
                out.append(EntryDiff(
                    key=key, status=DiffStatus.UNCHANGED,
                    value_a=ea.value, value_b=eb.value,
                    duplicate_role=role,
                ))
        return out
