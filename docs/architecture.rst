Architecture overview
=====================

Three-layer design:

1. **Data model** (:mod:`ini_parser`) — :class:`~ini_parser.IniEntry`,
   :class:`~ini_parser.IniSection`, and :class:`~ini_parser.IniDocument`
   classes that hold the parsed structure together with all preserved
   comments. Sorting and transformations always return new instances via
   ``clone()`` / ``sorted_copy()``.

2. **Parser & export engine** (:mod:`ini_parser`) —
   :class:`~ini_parser.IniParser` reads INI text into the data model, and
   :meth:`~ini_parser.IniDocument.export` dispatches to per-format
   serializers (INI, JSON, XML, YAML). ``parse_file`` / ``parse_string``
   accept an optional ``progress_callback(current_line, total_lines)`` for
   driving UI progress bars on large files.

3. **GUI layer** — PyQt6 main window, tabs, dialogs, tree widget, find bar,
   syntax highlighter, and diff view. One :class:`~document_tab.DocumentTab`
   exists per open file with its own undo/redo stacks.

Round-trip guarantee: parse → serialize → re-parse produces an identical
document — duplicates included.

Win32 ``GetPrivateProfileString`` semantics
-------------------------------------------

INI files are commonly consumed by Win32 applications via
``GetPrivateProfileString``, which only ever returns the **first**
occurrence of a duplicated section or key. The data model mirrors this:

- Duplicate section names and duplicate keys within a section are kept as
  separate :class:`~ini_parser.IniSection` / :class:`~ini_parser.IniEntry`
  instances — nothing is silently merged.
- Lookup helpers (:meth:`~ini_parser.IniDocument.get_section`,
  :meth:`~ini_parser.IniSection.get_entry`, ``set_entry``, ``remove_entry``)
  return / mutate the first match.
- The parser records every duplicate it sees in
  :attr:`~ini_parser.IniDocument.duplicates` as a
  :class:`~ini_parser.DuplicateRecord` (``kind``, ``section``, ``key``,
  ``line``). The GUI uses this list to surface a status-bar notice and
  highlight the affected rows in the structure tree and preview pane (first
  occurrence = winner in yellow / bold; later occurrences = shadowed in red
  / italic, plus a ★ / ↓ symbol).
- :class:`~ini_diff.IniDiff` pairs A's N-th occurrence of a name with B's
  N-th occurrence (occurrence-index pairing), so shadowed rows in the diff
  show the *actual* shadowed value rather than mirroring the winner. Each
  diff row carries a :class:`~ini_diff.DuplicateRole`
  (``NONE`` / ``WINNER`` / ``SHADOWED``) for the GUI to render bold/italic
  font and ★/↓ symbol in a dedicated "Duplicate (Win32 call)" column.
