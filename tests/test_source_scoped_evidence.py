"""Scope fidelity tests for WHML source evidence; no inferred rotation rules."""
import json
import unittest

from engine.source_editorial_packet import packet_from_html
from engine.source_scoped_evidence import scoped_from_packet, scoped_metadata, unbound_selector_impact


def capture(whml):
    html = ("<!doctype html><html><script>WH.markup.printHtml(" +
            json.dumps(whml) + ',"guide-body",false);</script></html>')
    return scoped_from_packet(packet_from_html(html))


class UnboundSelectorImpactTests(unittest.TestCase):
    def impact(self, whml):
        html = ('<!doctype html><html><script>WH.markup.printHtml('
                + json.dumps(whml) + ',"guide-body",false);</script></html>')
        packet = packet_from_html(html)
        scoped = scoped_from_packet(packet)
        return unbound_selector_impact(packet, scoped)

    def test_declared_options_in_real_ordered_steps_do_not_trigger_review(self):
        result = self.impact(
            '[display-option=Hero-A radio=hero checked]Option[/display-option]'
            '[ol][li display-options="Hero-A"][spell=101]Attack[/li][/ol]')
        self.assertEqual(result["unbound_selector_expression_occurrences"], 0)
        self.assertTrue(result["source_selector_references_resolved"])
        self.assertFalse(result["ordered_action_review_required"])

    def test_undeclared_option_on_ordered_spell_row_needs_review(self):
        result = self.impact(
            '[ol][li display-options=UnlistedHero][spell=101]Attack[/li][/ol]')
        self.assertEqual(result["unbound_selector_ordered_row_candidates"], 1)
        self.assertEqual(result["unbound_selector_ordered_ability_row_candidates"], 1)
        self.assertTrue(result["ordered_action_review_required"])
        self.assertFalse(result["gameplay_action_meaning_proven"])

    def test_unknown_explanatory_list_is_not_automatic_gameplay_failure(self):
        result = self.impact(
            '[ul][li display-options=NotesOnly][spell=101]Example[/li][/ul]')
        self.assertEqual(result["unbound_selector_expression_occurrences"], 1)
        self.assertEqual(result["unbound_selector_ordered_row_candidates"], 0)
        self.assertFalse(result["ordered_action_review_required"])
        self.assertFalse(result["source_selector_references_resolved"])

    def test_unknown_nested_span_within_ordered_row_is_detected(self):
        result = self.impact(
            '[ol][li]Start [span display-options=HiddenProc]'
            '[spell=101]Conditional[/span][/li][/ol]')
        self.assertEqual(result["unbound_selector_ordered_row_candidates"], 1)
        self.assertEqual(result["unbound_selector_ordered_ability_row_candidates"], 1)

    def test_standalone_unknown_step_requires_review(self):
        result = self.impact(
            '[rt-step=101 display-options=UnlistedStep]')
        self.assertEqual(result["unbound_selector_standalone_step_candidates"], 1)
        self.assertTrue(result["ordered_action_review_required"])

    def test_tooltip_ol_technique_explanation_is_not_execution_row(self):
        result = self.impact(
            '[tooltip name=T][ol][li display-options=Unlisted]'
            '[spell=101]Explanation[/li][/ol][/tooltip]')
        self.assertEqual(result["unbound_selector_ordered_row_candidates"], 0)
        self.assertFalse(result["ordered_action_review_required"])

    def test_unknown_ordered_plain_text_remains_review_without_spell_marker(self):
        result = self.impact(
            '[ol][li display-options=Unlisted]Use this action first[/li][/ol]')
        self.assertEqual(result["unbound_selector_ordered_row_candidates"], 1)
        self.assertEqual(result["unbound_selector_ordered_ability_row_candidates"], 0)
        self.assertTrue(result["ordered_action_review_required"])

    def test_safe_report_omits_original_text_and_selector_id(self):
        result = self.impact(
            '[ol][li display-options=PrivateTechnicalChoice]'
            '[spell=101]Protected text[/li][/ol]')
        public = json.dumps(result)
        self.assertNotIn("Protected text", public)
        self.assertNotIn("PrivateTechnicalChoice", public)
        self.assertFalse(result["source_text_in_report"])


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


    def test_historical_priority_rows_and_notes_do_not_share_list_identity(self):
        evidence = capture(
            '[tabs][tab name="ST"][div display-options=HeroA]'
            '[ol][li]Priority one[/li][li]Priority two[/li][/ol]'
            '[ul][li]Explanation, not priority[/li][/ul]'
            '[/div][/tab][/tabs]'
        )
        rows = evidence["payloads"][0]["source_list_rows"]
        self.assertEqual([x["containing_list"]["tag"] for x in rows],
                         ["ol", "ol", "ul"])
        self.assertEqual([x["containing_list"]["ordinal"] for x in rows],
                         [1, 2, 1])
        self.assertEqual(len({x["containing_list"]["start"] for x in rows}), 2)
        summary = scoped_metadata(evidence)
        self.assertEqual(summary["rows_in_ordered_lists"], 2)
        self.assertEqual(summary["rows_in_unordered_lists"], 1)
        self.assertFalse(summary["gameplay_action_interpreted"])

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
