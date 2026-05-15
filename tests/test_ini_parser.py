"""
tests/test_ini_parser.py – Unit tests for the INI parser and export functions.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ini_parser import (
    DuplicateKind,
    ExportFormat,
    IniDocument,
    IniParser,
    IniSection,
    SortMode,
)


SAMPLE_INI = """\
; Global header comment
; Line 2 of header

[bravo]
; Comment before key
z_key = last  ; inline note
a_key = first

[alpha]
m_key = middle
a_key = alpha_val
"""


class TestParsing(unittest.TestCase):
    def setUp(self):
        self.doc = IniParser.parse_string(SAMPLE_INI)

    def test_section_count(self):
        self.assertEqual(len(self.doc.sections), 2)

    def test_section_names(self):
        names = [s.name for s in self.doc.sections]
        self.assertIn("bravo", names)
        self.assertIn("alpha", names)

    def test_header_comments_preserved(self):
        self.assertTrue(any("Global header" in c for c in self.doc.header_comments))

    def test_preceding_comment_on_entry(self):
        bravo = self.doc.get_section("bravo")
        z_entry = bravo.get_entry("z_key")
        self.assertTrue(any("Comment before key" in c for c in z_entry.preceding_comments))

    def test_inline_comment(self):
        bravo = self.doc.get_section("bravo")
        z_entry = bravo.get_entry("z_key")
        self.assertIn("inline note", z_entry.inline_comment)

    def test_values(self):
        bravo = self.doc.get_section("bravo")
        self.assertEqual(bravo.get_entry("z_key").value, "last")
        self.assertEqual(bravo.get_entry("a_key").value, "first")

    def test_roundtrip(self):
        """Serialise and re-parse; sections and keys must survive."""
        rendered = self.doc.to_ini_string()
        doc2 = IniParser.parse_string(rendered)
        self.assertEqual(
            {s.name for s in self.doc.sections},
            {s.name for s in doc2.sections},
        )


class TestSorting(unittest.TestCase):
    def setUp(self):
        self.doc = IniParser.parse_string(SAMPLE_INI)

    def test_sort_sections_alpha(self):
        sorted_doc = self.doc.sorted_copy(SortMode.SECTIONS_ALPHA)
        names = [s.name for s in sorted_doc.sections]
        self.assertEqual(names, sorted(names, key=str.lower))

    def test_sort_keys_alpha(self):
        sorted_doc = self.doc.sorted_copy(SortMode.KEYS_ALPHA)
        for sec in sorted_doc.sections:
            keys = [e.key for e in sec.entries]
            self.assertEqual(keys, sorted(keys, key=str.lower))

    def test_sort_both(self):
        sorted_doc = self.doc.sorted_copy(SortMode.SECTIONS_AND_KEYS_ALPHA)
        names = [s.name for s in sorted_doc.sections]
        self.assertEqual(names, sorted(names, key=str.lower))
        for sec in sorted_doc.sections:
            keys = [e.key for e in sec.entries]
            self.assertEqual(keys, sorted(keys, key=str.lower))

    def test_sort_none_preserves_order(self):
        sorted_doc = self.doc.sorted_copy(SortMode.NONE)
        self.assertEqual(
            [s.name for s in self.doc.sections],
            [s.name for s in sorted_doc.sections],
        )


class TestExport(unittest.TestCase):
    def setUp(self):
        self.doc = IniParser.parse_string(SAMPLE_INI)

    def test_json_export(self):
        output = self.doc.to_json_string()
        data = json.loads(output)
        self.assertIn("bravo", data)
        self.assertEqual(data["bravo"]["z_key"], "last")

    def test_xml_export(self):
        output = self.doc.to_xml_string()
        self.assertIn("<configuration>", output)
        self.assertIn('name="bravo"', output)
        self.assertIn("last", output)

    def test_yaml_export(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")
        output = self.doc.to_yaml_string()
        data = yaml.safe_load(output)
        self.assertIn("bravo", data)
        self.assertEqual(data["bravo"]["z_key"], "last")

    def test_ini_export_contains_headers(self):
        output = self.doc.to_ini_string()
        self.assertIn("[bravo]", output)
        self.assertIn("[alpha]", output)
        self.assertIn("; Global header", output)

    def test_export_dispatch(self):
        for fmt in ExportFormat:
            if fmt == ExportFormat.YAML:
                try:
                    import yaml
                except ImportError:
                    continue
            result = self.doc.export(fmt)
            self.assertIsInstance(result, str)
            self.assertTrue(len(result) > 0)


class TestDocumentMutation(unittest.TestCase):
    def setUp(self):
        self.doc = IniParser.parse_string(SAMPLE_INI)

    def test_add_section(self):
        sec = self.doc.get_or_create_section("new_section")
        self.assertIsNotNone(sec)
        self.assertEqual(len([s for s in self.doc.sections if s.name == "new_section"]), 1)

    def test_set_entry(self):
        bravo = self.doc.get_section("bravo")
        bravo.set_entry("new_key", "new_value")
        self.assertEqual(bravo.get_entry("new_key").value, "new_value")

    def test_remove_entry(self):
        bravo = self.doc.get_section("bravo")
        removed = bravo.remove_entry("a_key")
        self.assertTrue(removed)
        self.assertIsNone(bravo.get_entry("a_key"))

    def test_remove_section(self):
        removed = self.doc.remove_section("alpha")
        self.assertTrue(removed)
        self.assertIsNone(self.doc.get_section("alpha"))

    def test_merge_from_adds_missing_sections_and_entries(self):
        base = IniDocument()
        other = IniParser.parse_string(
            "[one]\na=1\n[two]\nb=2\n"
        )
        base.merge_from(other)
        self.assertIsNotNone(base.get_section("one"))
        self.assertIsNotNone(base.get_section("two"))
        self.assertEqual(base.get_section("one").get_entry("a").value, "1")
        self.assertEqual(base.get_section("two").get_entry("b").value, "2")

    def test_merge_from_preserves_existing_values(self):
        base = IniParser.parse_string("[alpha]\na=original\n")
        other = IniParser.parse_string("[alpha]\na=updated\nb=added\n")
        base.merge_from(other)
        self.assertEqual(base.get_section("alpha").get_entry("a").value, "original")
        self.assertEqual(base.get_section("alpha").get_entry("b").value, "added")


class TestDuplicates(unittest.TestCase):
    """Win32 GetPrivateProfileString returns the first occurrence of a section
    or key. The parser preserves duplicates verbatim (so the file round-trips)
    and records each one in ``IniDocument.duplicates`` for the GUI to surface.
    """

    DUP_SECTION_INI = (
        "[foo]\n"
        "a=1\n"
        "\n"
        "[foo]\n"
        "b=2\n"
    )

    DUP_KEY_INI = (
        "[foo]\n"
        "a=first\n"
        "a=second\n"
        "b=other\n"
    )

    def test_duplicate_section_preserved_as_separate_section(self):
        doc = IniParser.parse_string(self.DUP_SECTION_INI)
        foo_sections = [s for s in doc.sections if s.name == "foo"]
        self.assertEqual(len(foo_sections), 2)
        self.assertEqual([e.key for e in foo_sections[0].entries], ["a"])
        self.assertEqual([e.key for e in foo_sections[1].entries], ["b"])

    def test_duplicate_section_lookup_returns_first(self):
        doc = IniParser.parse_string(self.DUP_SECTION_INI)
        first = doc.get_section("foo")
        self.assertIsNotNone(first)
        self.assertEqual([e.key for e in first.entries], ["a"])
        self.assertIsNone(first.get_entry("b"))

    def test_duplicate_section_recorded(self):
        doc = IniParser.parse_string(self.DUP_SECTION_INI)
        section_dups = [d for d in doc.duplicates if d.kind == DuplicateKind.SECTION]
        self.assertEqual(len(section_dups), 1)
        self.assertEqual(section_dups[0].section, "foo")
        self.assertEqual(section_dups[0].line, 4)

    def test_duplicate_section_roundtrip(self):
        doc = IniParser.parse_string(self.DUP_SECTION_INI)
        rendered = doc.to_ini_string()
        self.assertEqual(rendered.count("[foo]"), 2)
        doc2 = IniParser.parse_string(rendered)
        self.assertEqual(len([s for s in doc2.sections if s.name == "foo"]), 2)

    def test_duplicate_key_preserved_in_order(self):
        doc = IniParser.parse_string(self.DUP_KEY_INI)
        foo = doc.get_section("foo")
        keys_and_values = [(e.key, e.value) for e in foo.entries]
        self.assertEqual(
            keys_and_values, [("a", "first"), ("a", "second"), ("b", "other")]
        )

    def test_duplicate_key_lookup_returns_first(self):
        doc = IniParser.parse_string(self.DUP_KEY_INI)
        foo = doc.get_section("foo")
        self.assertEqual(foo.get_entry("a").value, "first")

    def test_duplicate_key_recorded(self):
        doc = IniParser.parse_string(self.DUP_KEY_INI)
        key_dups = [d for d in doc.duplicates if d.kind == DuplicateKind.KEY]
        self.assertEqual(len(key_dups), 1)
        self.assertEqual(key_dups[0].section, "foo")
        self.assertEqual(key_dups[0].key, "a")
        self.assertEqual(key_dups[0].line, 3)

    def test_duplicate_key_roundtrip(self):
        doc = IniParser.parse_string(self.DUP_KEY_INI)
        rendered = doc.to_ini_string()
        self.assertEqual(rendered.count("a = first"), 1)
        self.assertEqual(rendered.count("a = second"), 1)
        doc2 = IniParser.parse_string(rendered)
        foo = doc2.get_section("foo")
        self.assertEqual([e.value for e in foo.entries if e.key == "a"], ["first", "second"])

    def test_no_duplicates_when_file_is_clean(self):
        doc = IniParser.parse_string(SAMPLE_INI)
        self.assertEqual(doc.duplicates, [])

    def test_clone_copies_duplicates(self):
        doc = IniParser.parse_string(self.DUP_KEY_INI)
        clone = doc.clone()
        self.assertEqual(len(clone.duplicates), len(doc.duplicates))
        self.assertIsNot(clone.duplicates, doc.duplicates)
        clone.duplicates.clear()
        self.assertEqual(len(doc.duplicates), 1)


if __name__ == "__main__":
    unittest.main()
