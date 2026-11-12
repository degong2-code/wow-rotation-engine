"""Scope fidelity tests for WHML source evidence; no inferred rotation rules."""
import json
import unittest

from engine.source_editorial_packet import packet_from_html
from engine.source_scoped_evidence import scoped_from_packet, scoped_metadata


def capture(whml):
    html = ("<!doctype html><html><script>WH.markup.printHtml(" +
            json.dumps(whml) + ',"guide-body",false);</script></html>')
    return scoped_from_packet(packet_from_html(html))


class ScopeEvidenceTests(unittest.TestCase):
    def test_inherited_and_local_visibility_are_separate(self):
        p = capture(
            '[h2]Opener[/h2][div display-options="HeroA"]'
            '[ol][li]Always for Hero A[/li]'
            '[li display-options="PotionA"]Potion A only[/li]'
            '[/ol][/div]'
        )
        rows = p["payloads"][0]["source_list_rows"]
        self.assertEqual(len(rows), 2)
        self.assertEqual([s["expression"] for s in rows[0]["active_display_scopes"]], ["HeroA"])
        self.assertEqual([s["expression"] for s in rows[1]["active_display_scopes"]],
                         ["HeroA", "PotionA"])
        self.assertEqual(rows[1]["previous_heading"]["body_whml"], "Opener")
        self.assertFalse(rows[1]["contains_multiple_visibility_cases"])
        self.assertFalse(rows[1]["gameplay_action_interpreted"])

    def test_nested_conditional_fragment_does_not_masquerade_as_whole_row(self):
        p = capture(
            '[li]A common step [span display-options="PotionA"]'
            'different instant[/span] then shared[/li]'
        )
        r = p["payloads"][0]["source_list_rows"][0]
        self.assertEqual(r["active_display_scopes"], [])
        self.assertEqual(len(r["nested_display_fragments"]), 1)
        self.assertTrue(r["contains_multiple_visibility_cases"])
        self.assertEqual(r["nested_display_fragments"][0]["expression"], "PotionA")
        self.assertIn("different instant", r["original_whml_fragment"])

    def test_tabs_and_source_tooltip_associations(self):
        p = capture(
            '[tabs][tab name="ST"][ol][li]First '
            '[span tooltip=Reason]?[/span][/li][/ol][/tab]'
            '[tab name="AOE"][ol][li]Second[/li][/ol][/tab][/tabs]'
            '[tooltip name=Reason]Fictional explanation[/tooltip]'
        )
        rows = p["payloads"][0]["source_list_rows"]
        self.assertEqual([r["containing_tabs"][0]["label_whml"] for r in rows], ["ST", "AOE"])
        self.assertEqual(rows[0]["tooltip_references"][0]["definition_name"], "Reason")
        self.assertEqual(rows[1]["tooltip_references"], [])

    def test_tooltip_definition_li_is_not_action(self):
        p = capture('[tooltip name=Advanced][li]Explains only[/li][/tooltip]')
        r = p["payloads"][0]["source_list_rows"][0]
        self.assertTrue(r["inside_tooltip_definition"])
        self.assertFalse(r["gameplay_action_interpreted"])

    def test_unclosed_scope_is_review_not_pass(self):
        p = capture('[div display-options="A"][li]Missing both closing tags')
        issue = p["payloads"][0]["unresolved_structure_issues"]
        self.assertIn("unclosed_relevant_scopes", issue)
        meta = scoped_metadata(p)
        self.assertIn("unclosed_relevant_scopes", meta["structure_issue_types"])
        self.assertEqual(meta["structure_issue_positions"][0]["open_tag"], "div")

    def test_public_summary_has_no_copyrighted_text(self):
        p = capture('[h2]Secret heading[/h2][li display-options="SecretChoice"]'
                    'Copyright-restricted synthetic material[/li]')
        m = scoped_metadata(p)
        wire = json.dumps(m)
        self.assertNotIn("Copyright-restricted", wire)
        self.assertNotIn("SecretChoice", wire)
        self.assertFalse(m["automatic_publish_allowed"])
        self.assertEqual(m["rows_under_display_predicates"], 1)

    def test_table_rows_are_indexed_without_claiming_gameplay_semantics(self):
        p = capture(
            '[table][tr display-options=HeroB][td]A[/td][td]B[/td][/tr][/table]'
        )
        r = p["payloads"][0]["source_list_rows"][0]
        self.assertEqual(r["kind"], "source_table_row")
        self.assertEqual(r["active_display_scopes"][0]["expression"], "HeroB")
        self.assertFalse(p["gameplay_meaning_verified"])


if __name__ == "__main__":
    unittest.main()
