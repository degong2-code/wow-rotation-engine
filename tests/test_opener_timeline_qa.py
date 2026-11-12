"""Synthetic normal/negative controls for generic opener transition QA.

These are illustrative event models, NEVER copied source or gameplay proof.
The 12-context fixture tests cardinality and branch isolation, not the full
real Enhancement Shaman opener sequence.
"""
import json
from hashlib import sha256
import unittest

from engine.opener_timeline_qa import SCHEMA, assess_opener_timeline

SOURCE = ("[li][spell=101]Fictional attack[/li]\n"
          "[li][spell=102]Fictional potion[/li]\n"
          "[li][spell=103]Fictional prepull[/li]\n"
          "[li][spell=104]Fictional proc spender[/li]\n")
DIGEST = sha256(SOURCE.encode()).hexdigest()
PACKET = {
    "schema_version": "source-editorial-evidence-private-v1",
    "payloads": [{"original_whml": SOURCE, "sha256": DIGEST}],
}


def event(ident, action, marker, beat, phase, lane, *, when=None,
          set_state=None, time_ms=None, time_anchor=None):
    begin = SOURCE.index(marker)
    entry = {
        "id": ident, "action": action, "beat": beat, "phase": phase,
        "lane": lane, "when": when or [], "set_state": set_state or {},
        "evidence": [{
            "payload_sha256": DIGEST, "start": begin, "end": begin + len(marker)
        }],
        "action_source_marker": marker,
    }
    if time_ms is not None:
        entry.update(time_ms=time_ms, time_anchor=time_anchor)
    return entry


def expected(e):
    return {k: e[k] for k in ("action", "beat", "phase", "lane",
                              "time_ms", "time_anchor") if k in e}


def branch(context, events):
    return {"context": context, "events": events}


def case(ident, context, events, state=None):
    return {"id": ident, "context": context, "initial_state": state or {},
            "expected_events": [expected(e) for e in events]}


def run(branches, cases, packet=PACKET):
    return assess_opener_timeline(packet, {
        "schema_version": SCHEMA, "source_sha256": DIGEST,
        "branches": branches, "cases": cases,
    })


class OpenerTimelineTests(unittest.TestCase):
    def test_twelve_nested_choice_contexts_are_distinct(self):
        """Synthetic 2 x 2 x 3 matrix; only one known timing contrast modeled."""
        branches, cases = [], []
        for hero in ("storm", "totem"):
            for targets in ("single", "aoe"):
                for potion in ("luster", "recklessness", "potential"):
                    context = {"hero": hero, "targets": targets,
                               "potion": potion}
                    # Illustrative proxy for historical Storm AoE timing change.
                    early = (hero, targets, potion) == (
                        "storm", "aoe", "recklessness")
                    move = event("attack", "Fictional attack", "[spell=101]",
                                 0 if early else 1,
                                 "prepull" if early else "pull", "gcd",
                                 time_ms=-1000 if early else 0,
                                 time_anchor="start")
                    items = [move]
                    branches.append(branch(context, items))
                    cases.append(case("-".join((hero, targets, potion)), context, items))
        report = run(branches, cases)
        self.assertEqual(report["branch_count"], 12)
        self.assertEqual(report["case_outcome_counts"], {"matched": 12})
        self.assertTrue(report["all_declared_cases_matched"])
        self.assertFalse(report["timing_and_gcd_game_mechanics_verified"])

    def test_potion_choice_does_not_merge_exclusive_sequences(self):
        ca = {"potion": "A"}
        cb = {"potion": "B"}
        before = event("a", "Fictional potion", "[spell=102]",
                       0, "prepull", "off_gcd", time_ms=-12000,
                       time_anchor="use")
        at_pull = event("b", "Fictional potion", "[spell=102]",
                        1, "pull", "off_gcd", time_ms=0, time_anchor="use")
        result = run([branch(ca, [before]), branch(cb, [at_pull])],
                     [case("A", ca, [before]), case("B", cb, [at_pull])])
        self.assertTrue(result["all_declared_cases_matched"])

    def test_optional_cast_changes_next_beat(self):
        ctx = {"hero": "sample"}
        flag = {"field": "ready", "op": "eq", "value": True}
        prep = event("optional", "Fictional prepull", "[spell=103]",
                     0, "prepull", "gcd", when=[flag],
                     set_state={"proc": True})
        spend = event("spender", "Fictional proc spender", "[spell=104]",
                      1, "combat", "gcd",
                      when=[{"field": "proc", "op": "eq", "value": True}])
        result = run([branch(ctx, [prep, spend])], [
            case("proc", ctx, [prep, spend], {"ready": True, "proc": False}),
            case("not-ready", ctx, [], {"ready": False, "proc": False}),
        ])
        self.assertEqual(result["case_outcome_counts"], {"matched": 2})
        self.assertEqual(result["unexercised_event_count"], 0)

    def test_missing_guard_state_is_not_assumed_false(self):
        ctx = {"hero": "sample"}
        optional = event("optional", "Fictional prepull", "[spell=103]",
                         0, "prepull", "gcd",
                         when=[{"field": "ready", "op": "eq", "value": True}])
        result = run([branch(ctx, [optional])],
                     [case("unknown", ctx, [], {})])
        self.assertEqual(result["case_results"][0]["result"], "underdetermined")

    def test_gcd_and_off_gcd_can_share_beat(self):
        ctx = {"hero": "sample"}
        attack = event("attack", "Fictional attack", "[spell=101]",
                       1, "combat", "gcd")
        potion = event("potion", "Fictional potion", "[spell=102]",
                       1, "combat", "off_gcd")
        result = run([branch(ctx, [attack, potion])],
                     [case("concurrent", ctx, [potion, attack])])
        self.assertTrue(result["all_declared_cases_matched"])

    def test_two_gcd_actions_in_same_beat_are_ambiguous(self):
        ctx = {"hero": "sample"}
        attack = event("attack", "Fictional attack", "[spell=101]",
                       1, "combat", "gcd")
        other = event("other", "Fictional prepull", "[spell=103]",
                      1, "combat", "gcd")
        result = run([branch(ctx, [attack, other])],
                     [case("conflict", ctx, [attack, other])])
        self.assertEqual(result["case_results"][0]["result"], "ambiguous")

    def test_two_concurrent_events_cannot_write_conflicting_states(self):
        ctx = {"hero": "sample"}
        attack = event("attack", "Fictional attack", "[spell=101]",
                       1, "combat", "gcd", set_state={"proc": True})
        item = event("item", "Fictional potion", "[spell=102]",
                     1, "combat", "off_gcd", set_state={"proc": False})
        result = run([branch(ctx, [attack, item])],
                     [case("conflict", ctx, [])])
        self.assertEqual(result["case_results"][0]["result"], "ambiguous")

    def test_state_in_one_beat_is_not_visible_within_same_beat(self):
        ctx = {"hero": "sample"}
        attack = event("attack", "Fictional attack", "[spell=101]",
                       1, "combat", "gcd", set_state={"proc": True})
        item = event("item", "Fictional potion", "[spell=102]",
                     1, "combat", "off_gcd",
                     when=[{"field": "proc", "op": "eq", "value": True}])
        result = run([branch(ctx, [attack, item])],
                     [case("prebeat", ctx, [attack], {"proc": False})])
        self.assertFalse(result["all_declared_cases_matched"])
        # Unexecuted conditional branch remains unreviewed, not PASS.
        self.assertIn("unexercised_timeline_events", result["blocker_codes"])

    def test_incorrect_explicit_prepull_timing_is_detected(self):
        ctx = {"hero": "sample"}
        early = event("potion", "Fictional potion", "[spell=102]",
                      0, "prepull", "off_gcd",
                      time_ms=-12000, time_anchor="use")
        late = dict(expected(early), time_ms=-1000)
        result = run([branch(ctx, [early])],
                     [{"id": "bad", "context": ctx, "initial_state": {},
                       "expected_events": [late]}])
        self.assertEqual(result["case_results"][0]["result"], "mismatch")

    def test_time_anchor_must_be_explicit_and_phase_consistent(self):
        ctx = {"hero": "sample"}
        malformed = event("potion", "Fictional potion", "[spell=102]",
                          0, "prepull", "off_gcd",
                          time_ms=1000, time_anchor="use")
        with self.assertRaisesRegex(ValueError, "contradicts phase"):
            run([branch(ctx, [malformed])],
                [case("bad", ctx, [malformed])])

    def test_uncovered_choice_is_a_blocker(self):
        a = {"potion": "A"}
        b = {"potion": "B"}
        ea = event("a", "Fictional attack", "[spell=101]",
                   1, "combat", "gcd")
        eb = event("b", "Fictional potion", "[spell=102]",
                   0, "prepull", "off_gcd")
        result = run([branch(a, [ea]), branch(b, [eb])],
                     [case("A", a, [ea])])
        self.assertEqual(result["unreviewed_branch_count"], 1)
        self.assertIn("unreviewed_branch_contexts", result["blocker_codes"])

    def test_source_marker_must_be_in_first_citation(self):
        ctx = {"hero": "sample"}
        bad = event("bad", "Fictional potion", "[spell=102]",
                    1, "combat", "off_gcd")
        bad["action_source_marker"] = "[spell=104]"
        report = run([branch(ctx, [bad])], [case("bad", ctx, [bad])])
        self.assertIn("action_not_in_cited_source_span", report["blocker_codes"])

    def test_source_revision_lock_rejects_mismatch(self):
        ctx = {"hero": "sample"}
        item = event("item", "Fictional attack", "[spell=101]",
                     1, "combat", "gcd")
        with self.assertRaisesRegex(ValueError, "lock exactly one"):
            assess_opener_timeline(PACKET, {
                "schema_version": SCHEMA, "source_sha256": "0" * 64,
                "branches": [branch(ctx, [item])],
                "cases": [case("x", ctx, [item])],
            })

    def test_duplicate_case_ids_are_rejected(self):
        ctx = {"hero": "sample"}
        item = event("item", "Fictional attack", "[spell=101]",
                     1, "combat", "gcd")
        with self.assertRaisesRegex(ValueError, "Duplicate case id"):
            run([branch(ctx, [item])], [case("same", ctx, [item]),
                                        case("same", ctx, [item])])

    def test_same_schema_for_unrelated_spec_and_no_source_text_leak(self):
        ctx = {"spec": "other", "build": "unrelated"}
        item = event("item", "Copyrighted private ability", "[spell=101]",
                     1, "combat", "gcd")
        report = run([branch(ctx, [item])],
                     [case("private secret case", ctx, [item])])
        serialized = json.dumps(report)
        self.assertTrue(report["all_declared_cases_matched"])
        self.assertNotIn("Copyrighted private ability", serialized)
        self.assertNotIn("private secret case", serialized)
        self.assertFalse(report["automatic_publish_allowed"])


if __name__ == "__main__":
    unittest.main()
