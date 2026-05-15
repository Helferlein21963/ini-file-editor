"""
tests/test_ini_diff.py – Unit tests for the IniDiff engine.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ini_diff import DiffStatus, DuplicateRole, IniDiff
from ini_parser import IniDocument, IniParser

INI_A = """\
[network]
host = localhost
port = 8080

[auth]
enabled = true
timeout = 30

[debug]
verbose = false
"""

INI_B = """\
[network]
host = prod.example.com
port = 8080
tls = true

[auth]
enabled = true

[logging]
level = INFO
"""


class TestDiffBasic(unittest.TestCase):
    def setUp(self):
        self.doc_a = IniParser.parse_string(INI_A)
        self.doc_b = IniParser.parse_string(INI_B)
        self.diff = IniDiff.compare(self.doc_a, self.doc_b)

    def test_section_order_a_first(self):
        names = [s.name for s in self.diff.sections]
        # A's sections come first; B-only section appended at end
        self.assertEqual(names.index("network"), 0)
        self.assertIn("logging", names)
        self.assertGreater(names.index("logging"), names.index("network"))

    def test_unchanged_section_detected(self):
        network = next(s for s in self.diff.sections if s.name == "network")
        # section has changes, so status is MODIFIED
        self.assertEqual(network.status, DiffStatus.MODIFIED)

    def test_modified_value(self):
        network = next(s for s in self.diff.sections if s.name == "network")
        host = next(e for e in network.entries if e.key == "host")
        self.assertEqual(host.status, DiffStatus.MODIFIED)
        self.assertEqual(host.value_a, "localhost")
        self.assertEqual(host.value_b, "prod.example.com")

    def test_unchanged_value(self):
        network = next(s for s in self.diff.sections if s.name == "network")
        port = next(e for e in network.entries if e.key == "port")
        self.assertEqual(port.status, DiffStatus.UNCHANGED)
        self.assertEqual(port.value_a, "8080")
        self.assertEqual(port.value_b, "8080")

    def test_added_key(self):
        network = next(s for s in self.diff.sections if s.name == "network")
        tls = next(e for e in network.entries if e.key == "tls")
        self.assertEqual(tls.status, DiffStatus.ADDED)
        self.assertIsNone(tls.value_a)
        self.assertEqual(tls.value_b, "true")

    def test_removed_key(self):
        auth = next(s for s in self.diff.sections if s.name == "auth")
        timeout = next(e for e in auth.entries if e.key == "timeout")
        self.assertEqual(timeout.status, DiffStatus.REMOVED)
        self.assertEqual(timeout.value_a, "30")
        self.assertIsNone(timeout.value_b)

    def test_removed_section(self):
        debug = next(s for s in self.diff.sections if s.name == "debug")
        self.assertEqual(debug.status, DiffStatus.REMOVED)
        for e in debug.entries:
            self.assertEqual(e.status, DiffStatus.REMOVED)

    def test_added_section(self):
        logging = next(s for s in self.diff.sections if s.name == "logging")
        self.assertEqual(logging.status, DiffStatus.ADDED)
        for e in logging.entries:
            self.assertEqual(e.status, DiffStatus.ADDED)
            self.assertIsNone(e.value_a)

    def test_unchanged_section_all_equal(self):
        # auth: only 'enabled' is shared, 'timeout' removed → section is MODIFIED
        auth = next(s for s in self.diff.sections if s.name == "auth")
        self.assertEqual(auth.status, DiffStatus.MODIFIED)
        enabled = next(e for e in auth.entries if e.key == "enabled")
        self.assertEqual(enabled.status, DiffStatus.UNCHANGED)


class TestDiffCounts(unittest.TestCase):
    def setUp(self):
        self.doc_a = IniParser.parse_string(INI_A)
        self.doc_b = IniParser.parse_string(INI_B)
        self.diff = IniDiff.compare(self.doc_a, self.doc_b)

    def test_counts_add_up(self):
        total = (
            self.diff.count_added()
            + self.diff.count_removed()
            + self.diff.count_modified()
            + self.diff.count_unchanged()
        )
        expected = sum(len(s.entries) for s in self.diff.sections)
        self.assertEqual(total, expected)

    def test_has_differences(self):
        self.assertTrue(self.diff.has_differences)

    def test_identical_docs_no_differences(self):
        doc = IniParser.parse_string(INI_A)
        diff = IniDiff.compare(doc, doc)
        self.assertFalse(diff.has_differences)
        self.assertEqual(diff.count_modified(), 0)
        self.assertEqual(diff.count_added(), 0)
        self.assertEqual(diff.count_removed(), 0)


class TestDiffEmptyDocs(unittest.TestCase):
    def test_both_empty(self):
        diff = IniDiff.compare(IniDocument(), IniDocument())
        self.assertEqual(diff.sections, [])
        self.assertFalse(diff.has_differences)

    def test_a_empty(self):
        doc_b = IniParser.parse_string("[x]\nk = v\n")
        diff = IniDiff.compare(IniDocument(), doc_b)
        self.assertEqual(len(diff.sections), 1)
        self.assertEqual(diff.sections[0].status, DiffStatus.ADDED)

    def test_b_empty(self):
        doc_a = IniParser.parse_string("[x]\nk = v\n")
        diff = IniDiff.compare(doc_a, IniDocument())
        self.assertEqual(len(diff.sections), 1)
        self.assertEqual(diff.sections[0].status, DiffStatus.REMOVED)


class TestDiffBOnlySectionOrder(unittest.TestCase):
    def test_b_only_sections_appended_in_b_order(self):
        doc_a = IniParser.parse_string("[alpha]\nk=1\n")
        doc_b = IniParser.parse_string("[alpha]\nk=1\n[beta]\nk=2\n[gamma]\nk=3\n")
        diff = IniDiff.compare(doc_a, doc_b)
        names = [s.name for s in diff.sections]
        self.assertEqual(names[0], "alpha")
        self.assertLess(names.index("beta"), names.index("gamma"))


class TestDiffWithDuplicates(unittest.TestCase):
    """The diff must mirror the parser/GUI: duplicate sections and keys are
    preserved as separate rows so the user sees them, the first occurrence
    is marked WINNER (yellow in the UI), later ones SHADOWED (red). The
    comparison itself uses first-wins (Win32 GetPrivateProfileString
    semantics), so shadowed rows visually mirror their winner.
    """

    def test_duplicate_section_in_a_produces_two_rows(self):
        doc_a = IniParser.parse_string("[foo]\na=1\n\n[foo]\nb=2\n")
        doc_b = IniParser.parse_string("[foo]\na=1\n")
        diff = IniDiff.compare(doc_a, doc_b)
        foo_sections = [s for s in diff.sections if s.name == "foo"]
        self.assertEqual(len(foo_sections), 2)
        self.assertEqual(foo_sections[0].duplicate_role, DuplicateRole.WINNER)
        self.assertEqual(foo_sections[1].duplicate_role, DuplicateRole.SHADOWED)

    def test_duplicate_section_in_b_produces_two_rows(self):
        doc_a = IniParser.parse_string("[foo]\na=1\n")
        doc_b = IniParser.parse_string("[foo]\na=1\n\n[foo]\nb=2\n")
        diff = IniDiff.compare(doc_a, doc_b)
        foo_sections = [s for s in diff.sections if s.name == "foo"]
        self.assertEqual(len(foo_sections), 2)
        self.assertEqual(foo_sections[0].duplicate_role, DuplicateRole.WINNER)
        self.assertEqual(foo_sections[1].duplicate_role, DuplicateRole.SHADOWED)

    def test_unique_section_has_role_none(self):
        doc_a = IniParser.parse_string("[foo]\na=1\n[bar]\nb=2\n")
        doc_b = IniParser.parse_string("[foo]\na=1\n[bar]\nb=2\n")
        diff = IniDiff.compare(doc_a, doc_b)
        for sec in diff.sections:
            self.assertEqual(sec.duplicate_role, DuplicateRole.NONE)

    def test_winner_row_does_first_wins_comparison(self):
        # A has k=one (winner) k=two (shadowed). B has k=one.
        # The WINNER row compares A's first vs B's first → UNCHANGED.
        doc_a = IniParser.parse_string("[foo]\nk=one\nk=two\n")
        doc_b = IniParser.parse_string("[foo]\nk=one\n")
        diff = IniDiff.compare(doc_a, doc_b)
        k_entries = [e for e in diff.sections[0].entries if e.key == "k"]
        self.assertEqual(len(k_entries), 2)
        winner, shadowed = k_entries
        self.assertEqual(winner.duplicate_role, DuplicateRole.WINNER)
        self.assertEqual(winner.status, DiffStatus.UNCHANGED)
        self.assertEqual(winner.value_a, "one")
        self.assertEqual(winner.value_b, "one")
        # The SHADOWED row reflects A's 2nd "k" paired with B's (missing)
        # 2nd "k". Crucially, it shows the *actual* shadowed value (`two`),
        # not the winner's value — that's what the user needs to see.
        self.assertEqual(shadowed.duplicate_role, DuplicateRole.SHADOWED)
        self.assertEqual(shadowed.status, DiffStatus.REMOVED)
        self.assertEqual(shadowed.value_a, "two")
        self.assertIsNone(shadowed.value_b)

    def test_duplicate_key_in_b_produces_two_rows(self):
        doc_a = IniParser.parse_string("[foo]\nk=alpha\n")
        doc_b = IniParser.parse_string("[foo]\nk=alpha\nk=beta\n")
        diff = IniDiff.compare(doc_a, doc_b)
        foo = diff.sections[0]
        k_entries = [e for e in foo.entries if e.key == "k"]
        self.assertEqual(len(k_entries), 2)
        self.assertEqual(k_entries[0].duplicate_role, DuplicateRole.WINNER)
        self.assertEqual(k_entries[1].duplicate_role, DuplicateRole.SHADOWED)

    def test_shadowed_row_uses_actual_occurrence_value(self):
        # A=[foo k=one k=two], B=[foo k=other]. Winner row is MODIFIED
        # (one vs other). Shadowed row pairs A's 2nd "k" (=two) with B's
        # missing 2nd → REMOVED. The user sees both real values, not the
        # winner's value mirrored onto the shadow.
        doc_a = IniParser.parse_string("[foo]\nk=one\nk=two\n")
        doc_b = IniParser.parse_string("[foo]\nk=other\n")
        diff = IniDiff.compare(doc_a, doc_b)
        winner, shadowed = [e for e in diff.sections[0].entries if e.key == "k"]
        self.assertEqual(winner.status, DiffStatus.MODIFIED)
        self.assertEqual(winner.value_a, "one")
        self.assertEqual(winner.value_b, "other")
        self.assertEqual(shadowed.status, DiffStatus.REMOVED)
        self.assertEqual(shadowed.value_a, "two")
        self.assertIsNone(shadowed.value_b)

    def test_shadowed_b_value_visible(self):
        # The bug the user reported: A has `name=MyApp` once, B has it
        # twice (`name=MyApp` then `name=ThomasIni`). The shadowed row
        # must show B's actual second value, not the first-wins value.
        doc_a = IniParser.parse_string("[app]\nname=MyApp\n")
        doc_b = IniParser.parse_string("[app]\nname=MyApp\nname=ThomasIni\n")
        diff = IniDiff.compare(doc_a, doc_b)
        winner, shadowed = [
            e for e in diff.sections[0].entries if e.key == "name"
        ]
        self.assertEqual(winner.value_b, "MyApp")
        self.assertEqual(shadowed.value_b, "ThomasIni")
        self.assertIsNone(shadowed.value_a)


if __name__ == "__main__":
    unittest.main()