"""
tests/test_ini_diff.py – Unit tests for the IniDiff engine.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ini_diff import DiffStatus, IniDiff
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


if __name__ == "__main__":
    unittest.main()