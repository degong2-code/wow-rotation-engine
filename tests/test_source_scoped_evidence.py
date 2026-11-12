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
        self.assertEqual(meta["source_condition_expression_count"], 1)
        self.assertEqual(meta["unassigned_conditional_expressions"], 1)
        self.assertEqual(meta["structure_issue_positions"][0]["open_tag"], "div")

    def test_unknown_inline_condition_is_not_falsely_assigned_to_entire_scope(self):
        p = capture(
            '[tabs][tab name=AoE][div][rt-step display-options="PotionA"'
            ' spell=123]Continue[/div][/tab][/tabs]'
        )
        payload = p["payloads"][0]
        self.assertEqual(payload["unresolved_structure_issues"], [])
        self.assertEqual(len(payload["standalone_condition_markers"]), 1)
        self.assertTrue(payload["standalone_condition_markers"][0]["scope_unverified"])
        summary = scoped_metadata(p)
        self.assertEqual(summary["standalone_conditional_markers"], 1)
        self.assertEqual(summary["source_condition_expression_count"], 1)
        self.assertEqual(summary["unassigned_conditional_expressions"], 0)
        self.assertEqual(summary["standalone_conditional_marker_types"], {"rt-step": 1})
        self.assertFalse(summary["automatic_publish_allowed"])

    def test_unknown_conditional_marker_inside_row_requires_separate_review(self):
        p = capture(
            '[li]Start [rt-step display-options="PotionB" spell=42] More[/li]'
        )
        row = p["payloads"][0]["source_list_rows"][0]
        self.assertEqual(row["active_display_scopes"], [])
        self.assertTrue(row["contains_multiple_visibility_cases"])
        self.assertEqual(row["standalone_condition_markers_inside_row"][0]["expression"], "PotionB")

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
