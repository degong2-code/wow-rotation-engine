"""No game rules: only exact WHML preservation and source offsets."""
import json
import unittest

from engine.source_editorial_packet import packet_from_html
from engine.source_page_acquire import SourceAccessError

WHML = ('[h2]Synthetic opener[/h2]'
        '[display-option="HeroA" radio="Hero" checked]Hero A[/display-option]'
        '[display-option="HeroB" radio="Hero"]Hero B[/display-option]'
        '[li display-options="HeroA&!HeroB"]Synthetic first action[/li]'
        '[tooltip name="Why"]A complete fictional tooltip body.[/tooltip]'
        '[span tooltip=Why]?</span>')


def document(body=WHML):
    return ('<!doctype html><html><script>WH.markup.printHtml('
            + json.dumps(body) + ',"guide-body",false);</script></html>')


class SourceEditorialPacketTests(unittest.TestCase):
    def test_raw_whml_preserved_with_reference_offsets(self):
        pkt = packet_from_html(document())
        self.assertEqual(pkt["schema_version"], "source-editorial-evidence-private-v1")
        raw = pkt["payloads"][0]["original_whml"]
        self.assertEqual(raw, WHML)
        self.assertEqual(pkt["payloads"][0]["tooltip_definitions"][0]["body_whml"],
                         "A complete fictional tooltip body.")
        refs = pkt["payloads"][0]["tooltip_references"]
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]["definition_name"], "Why")
        self.assertEqual(raw[refs[0]["position"]:][:5], "[span")
        self.assertFalse(pkt["gameplay_meaning_verified"])

    def test_conditional_expression_position_and_options(self):
        pkt = packet_from_html(document())["payloads"][0]
        self.assertEqual(len(pkt["option_definitions"]), 2)
        self.assertTrue(pkt["option_definitions"][0]["default_checked"])
        self.assertFalse(pkt["option_definitions"][1]["default_checked"])
        self.assertEqual(pkt["conditional_expressions"][0]["expression"], "HeroA&!HeroB")
        start = pkt["conditional_expressions"][0]["position"]
        self.assertTrue(pkt["original_whml"][start:].startswith("[li display-options="))

    def test_missing_literal_source_fails_closed(self):
        with self.assertRaises(SourceAccessError):
            packet_from_html("<html><body>Access denied</body></html>")

    def test_non_guide_markup_not_collected(self):
        doc = ('<html><script>WH.markup.printHtml(' +
               json.dumps("[tooltip name=Secret]Private[/tooltip]") +
               ',"sidebar",false);</script></html>')
        with self.assertRaises(SourceAccessError):
            packet_from_html(doc)

    def test_private_fields_explicitly_forbid_publication(self):
        pkt = packet_from_html(document())
        self.assertTrue(pkt["source_text_in_file"])
        self.assertFalse(pkt["source_text_may_be_public"])
        self.assertFalse(pkt["automatic_publish_allowed"])


if __name__ == "__main__":
    unittest.main()
