"""Synthetic tests of AI proposal transport, evidence, approval, and safe V11 patch."""
from copy import deepcopy
import hashlib
import json
import unittest

from engine.v2.ai_proposals import (
    apply_approval, canonical_sha, prepare_request, review_report,
    suggest_via_openai, validate_proposal, _replacement_in_text_node,
)

ICON = (
    '<span data-spell="test"><img src="https://example.org/icon.png" '
    'onerror="this.hidden=true"/></span>'
)
SOURCE = "최신 제공 자료의 명시적인 조건은 변경 조건을 우선한다는 것입니다."
QUOTE = "변경 조건을 우선한다는 것입니다"


def fixture():
    return {
        "schema_version": "v11-private-detail-v1",
        "guide_id": "rogue",
        "baseline_v11_sha256": "a" * 64,
        "public_storage_allowed": False,
        "rotation_groups": [{
            "id": "rogue:rogue-rotation:table-1",
            "rules": [{
                "id": "rogue:rogue-rotation:table-1:row-1",
                "condition_html": "<b>기존 조건</b>" + ICON + " 참고",
                "condition_text_ko": "기존 조건 참고",
                "action_text_ko": "합성 기술",
                "source_fragment_sha256": "b" * 64,
            }, {
                "id": "rogue:rogue-rotation:table-1:row-2",
                "condition_html": "다른 규칙 그대로",
                "condition_text_ko": "다른 규칙 그대로",
                "action_text_ko": "두번째 합성 기술",
                "source_fragment_sha256": "d" * 64,
            }],
        }],
        "advanced_guidance": [{
            "id": "rogue:rogue-advanced:tip-1",
            "topic": "시험 심화",
            "html": '<p class="sample">기존 팁 설명입니다.</p>',
            "text_ko": "기존 팁 설명입니다.",
            "source_fragment_sha256": "c" * 64,
        }],
    }


RULE_ID = "rogue:rogue-rotation:table-1:row-1"
TIP_ID = "rogue:rogue-advanced:tip-1"


def suggestion(prepared):
    return {
        "schema_version": "v11-ai-proposal-v1",
        "guide_id": prepared["guide_id"],
        "source_sha256": prepared["source_sha256"],
        "updates": [{
            "id": RULE_ID,
            "kind": "rule",
            "old_text": "기존 조건",
            "new_text": "변경 조건",
            "evidence_quote": QUOTE,
            "rationale": "제공 자료의 조건 문구가 달라짐",
            "confidence": "medium",
        }],
    }


class AIProposalTests(unittest.TestCase):
    def setUp(self):
        self.old = fixture()
        self.req = prepare_request(self.old, SOURCE, [RULE_ID, TIP_ID])
        self.proposal = suggestion(self.req)

    def test_preparation_sends_only_explicit_selected_ids_and_source(self):
        self.assertEqual(self.req["source_sha256"], hashlib.sha256(
            SOURCE.encode("utf-8")).hexdigest())
        self.assertEqual([x["id"] for x in self.req["targets"]], [RULE_ID, TIP_ID])
        self.assertEqual(self.req["targets"][0]["old_text"], "기존 조건 참고")
        self.assertNotIn(ICON, json.dumps(self.req, ensure_ascii=False))

    def test_no_source_excerpts_over_twelve_thousand_chars(self):
        with self.assertRaisesRegex(ValueError, "12,000"):
            prepare_request(self.old, "A" * 12001, [RULE_ID])

    def test_evidence_quote_and_target_are_required(self):
        self.assertEqual(validate_proposal(self.req, self.proposal, self.old),
                         self.proposal["updates"])
        wrong = deepcopy(self.proposal)
        wrong["updates"][0]["evidence_quote"] = "존재하지 않는 독자 생성 문장"
        with self.assertRaisesRegex(ValueError, "evidence quote"):
            validate_proposal(self.req, wrong, self.old)
        unknown = deepcopy(self.proposal)
        unknown["updates"][0]["id"] = "rogue:other:tip-5"
        with self.assertRaisesRegex(ValueError, "Unknown or repeated"):
            validate_proposal(self.req, unknown, self.old)

    def test_ambiguous_old_text_rejected(self):
        wrong = deepcopy(self.proposal)
        wrong["updates"][0]["old_text"] = "없던 조건"
        with self.assertRaisesRegex(ValueError, "exactly once"):
            validate_proposal(self.req, wrong, self.old)

    def test_review_does_not_modify_or_auto_approve(self):
        before = deepcopy(self.old)
        report = review_report(self.req, self.proposal, self.old)
        self.assertTrue(report["approval_required"])
        self.assertFalse(report["auto_applied"])
        self.assertEqual(self.old, before)
        self.assertEqual(report["proposal_sha256"], canonical_sha(self.proposal))

    def test_approval_changes_only_one_text_node_and_retains_icons(self):
        decision = {
            "schema_version": "v11-ai-approval-v1",
            "proposal_sha256": canonical_sha(self.proposal),
            "approved_ids": [RULE_ID],
        }
        changed = apply_approval(self.req, self.proposal, decision, self.old)
        self.assertEqual(changed["rotation_groups"][0]["rules"][0]["condition_html"],
                         "<b>변경 조건</b>" + ICON + " 참고")
        self.assertEqual(changed["rotation_groups"][0]["rules"][0]["condition_text_ko"],
                         "변경 조건 참고")
        self.assertEqual(changed["rotation_groups"][0]["rules"][1],
                         self.old["rotation_groups"][0]["rules"][1])
        self.assertEqual(changed["advanced_guidance"], self.old["advanced_guidance"])
        self.assertEqual(self.old["rotation_groups"][0]["rules"][0][
            "condition_text_ko"], "기존 조건 참고")

    def test_approval_requires_matching_proposal_sha(self):
        wrong = {
            "schema_version": "v11-ai-approval-v1",
            "proposal_sha256": "0" * 64,
            "approved_ids": [RULE_ID],
        }
        with self.assertRaisesRegex(ValueError, "approval file"):
            apply_approval(self.req, self.proposal, wrong, self.old)

    def test_empty_approval_changes_nothing(self):
        decision = {
            "schema_version": "v11-ai-approval-v1",
            "proposal_sha256": canonical_sha(self.proposal),
            "approved_ids": [],
        }
        self.assertEqual(apply_approval(self.req, self.proposal, decision, self.old),
                         self.old)

    def test_text_node_replacement_escapes_ampersand_and_preserves_markup(self):
        result = _replacement_in_text_node(
            "<b>옛 조건</b>" + ICON, "옛 조건", "새 조건 & 단서"
        )
        self.assertEqual(result, "<b>새 조건 &amp; 단서</b>" + ICON)

    def test_old_text_cannot_cross_tags_or_change_attributes(self):
        with self.assertRaisesRegex(ValueError, "exactly once"):
            _replacement_in_text_node("<b>기존</b> 조건", "기존 조건", "새 조건")
        with self.assertRaisesRegex(ValueError, "exactly once"):
            _replacement_in_text_node('<span data-note="옛 조건">다른 문장</span>',
                                      "옛 조건", "새 조건")

    def test_openai_transport_is_opt_in_and_disables_server_storage(self):
        sent = {}

        class FakeResponse:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, *args):
                return json.dumps({
                    "status": "completed",
                    "output": [{
                        "type": "message",
                        "content": [{
                            "type": "output_text",
                            "text": json.dumps(self_proposal, ensure_ascii=False),
                        }],
                    }],
                }).encode("utf-8")

        self_proposal = self.proposal

        def fake_urlopen(request, timeout):
            sent["url"] = request.full_url
            sent["timeout"] = timeout
            sent["body"] = json.loads(request.data)
            return FakeResponse()

        result = suggest_via_openai(
            self.req, "example-model-v1", "fake-api-key", urlopen=fake_urlopen
        )
        self.assertEqual(result, self.proposal)
        self.assertEqual(sent["url"], "https://api.openai.com/v1/responses")
        self.assertIs(sent["body"]["store"], False)
        self.assertEqual(sent["body"]["text"]["format"]["type"], "json_schema")
        self.assertEqual(sent["body"]["tool_choice"], "none")
        self.assertEqual(json.loads(sent["body"]["input"]), self.req)
        with self.assertRaisesRegex(ValueError, "Explicit API key"):
            suggest_via_openai(self.req, "example-model-v1", "")


if __name__ == "__main__":
    unittest.main()
