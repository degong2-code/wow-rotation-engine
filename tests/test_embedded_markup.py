"""Synthetic embedded WHML tests; not a live WoW guide."""
import json
import unittest
from engine.embedded_markup import inspect_embedded_whml
from engine.source_structure import inspect_html


def fixture(body=None):
    if body is None:
        body = ('[tabs][tab]Example[/tab][/tabs][toggler id=panel]'
                '[tooltip name=first]Synthetic unique hidden explanation.[/tooltip]'
                '[tooltip name=second]Another synthetic note.[/tooltip]'
                '[span tooltip=first tooltip2=second]?[/span]')
    return '<script>WH.markup.printHtml(' + json.dumps(body) + ', "guide-body", false);</script>'


class EmbeddedWhmlTests(unittest.TestCase):
    def test_literal_payload_and_multiple_tooltips(self):
        data = inspect_embedded_whml(fixture())
        self.assertEqual((data["literal_call_candidates"], data["decoded_payloads"]), (1, 1))
        p = data["payloads"][0]
        self.assertEqual(p["target"], "guide-body")
        self.assertEqual(p["named_tooltip_definitions"], ["first", "second"])
        self.assertEqual([x["attribute"] for x in p["tooltip_references"]], ["tooltip", "tooltip2"])
        self.assertEqual(p["components"]["toggler"], 1)
        self.assertEqual(p["unresolved_reference_names"], [])

    def test_unresolved_and_duplicate_names(self):
        data = inspect_embedded_whml(fixture("[span tooltip=missing tooltip2=second]?[/span]"))
        self.assertEqual(data["payloads"][0]["unresolved_reference_names"], ["missing", "second"])
        data = inspect_embedded_whml(fixture(
            "[tooltip name=a]One[/tooltip][tooltip name=a]Two[/tooltip]"))
        self.assertEqual(data["payloads"][0]["duplicate_definition_names"], ["a"])

    def test_nonliteral_source_never_executes(self):
        data = inspect_embedded_whml("<script>WH.markup.printHtml(variable, 'guide-body');</script>")
        self.assertEqual(data["decoded_payloads"], 0)
        self.assertEqual(data["unsupported_nonliteral_calls"], 1)
        self.assertFalse(data["javascript_executed"])

    def test_no_copyright_text_in_report(self):
        payload = "[tooltip name=x]Private synthetic source phrase SHOULD NOT LEAK.[/tooltip]"
        report = json.dumps(inspect_embedded_whml(fixture(payload)))
        self.assertNotIn("Private synthetic source phrase", report)

    def test_integrates_with_html_structure_inspector(self):
        result = inspect_html(fixture())
        self.assertEqual(result["embedded_whml"]["decoded_payloads"], 1)
        self.assertTrue(result["static_embedded_whml_decoded"])
        self.assertFalse(result["live_ui_completeness_verified"])

    def test_separate_sidebar_and_guide(self):
        data = inspect_embedded_whml(
            '<script>WH.markup.printHtml("[tooltip name=a]X[/tooltip]", "sidebar");'
            'WH.markup.printHtml("[span tooltip=b]Y[/span]", "guide-body");</script>')
        self.assertEqual([p["target"] for p in data["payloads"]], ["sidebar", "guide-body"])

    def test_escaped_quoted_attribute(self):
        payload = '[tooltip name="tip"]"Escaped" content[/tooltip][span tooltip=tip]?[/span]'
        p = inspect_embedded_whml(fixture(payload))["payloads"][0]
        self.assertEqual(p["named_tooltip_definitions"], ["tip"])
        self.assertEqual(p["unresolved_reference_names"], [])


if __name__ == "__main__":
    unittest.main()
