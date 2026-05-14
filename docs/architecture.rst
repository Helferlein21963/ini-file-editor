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
   serializers (INI, JSON, XML, YAML).

3. **GUI layer** — PyQt6 main window, tabs, dialogs, tree widget, find bar,
   syntax highlighter, and diff view. One :class:`~document_tab.DocumentTab`
   exists per open file with its own undo/redo stacks.

Round-trip guarantee: parse → serialize → re-parse produces an identical
document.
