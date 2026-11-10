"""Synthetic AI-provider bridge tests: model text never edits private V11."""
from copy import deepcopy
import json
import unittest

from engine.v2.ai_runtime import AIJob, AIProposal
from engine.v2.ai_update_bridge import prepare_update_with_provider
from engine.v2.ai_proposals import canonical_sha

RULE_ID = "test:rotation:table-1:row-1"
QUOTE = "변경 규칙을 적용"
EXCERPT = "공략 원문에 따르면 변경 규칙을 적용해야 한다."
SECRET_HTML = '<span class="spell"><img src="private-icon.png"></span>'


def detail():
    return {
        "schema_version": "v11-private-detail-v1",
        "guide_id": "test",
        "baseline_v11_sha256": "a" * 64,
        "public_storage_allowed": False,
        "rotation_groups": [{
            "id": "test:rotation:table-1",
            "rules": [{
                "id": RULE_ID,
                "condition_html": "<b>기존 조건</b>" + SECRET_HTML + " 참고",
                "condition_text_ko": "기존 조건 참고",
                "action_text_ko": "가상 기술",
                "source_fragment_sha256": "b" * 64,
            }],
        }],
        "advanced_guidance": [],
    }


class StubProvider:
    def __init__(self, *, corrupt_quote=False, wrong_operation=False):
        self.last_job = None
        self.corrupt_quote = corrupt_quote
        self.wrong_operation = wrong_operation

    def list_models(self):
        return ()

    def propose(self, job: AIJob, *, model: str):
        self.last_job = job
        prepared = json.loads(job.source_text)
        output = {
            "schema_version": "v11-ai-proposal-v1",
            "guide_id": prepared["guide_id"],
            "source_sha256": prepared["source_sha256"],
            "updates": [{
                "id": RULE_ID,
                "kind": "rule",
                "old_text": "기존 조건",
                "new_text": "변경 규칙",
                "evidence_quote": "가짜 인용" if self.corrupt_quote else QUOTE,
                "rationale": "출처의 조건이 달라짐",
                "confidence": "medium",
            }],
        }
        return AIProposal(
            provider="synthetic", model=model,
            operation="extract" if self.wrong_operation else "update",
            candidate=output,
        )


class PlanToUpdateBridgeTests(unittest.TestCase):
    def test_update_is_prepared_reviewed_but_never_applied(self):
        before = detail()
        snapshot = deepcopy(before)
        provider = StubProvider()
        result = prepare_update_with_provider(
            before, EXCERPT, [RULE_ID],
            provider=provider, model="test-model-only",
        )
        self.assertEqual(before, snapshot)
        self.assertEqual(result.review["schema_version"], "v11-ai-review-v1")
        self.assertTrue(result.review["approval_required"])
        self.assertFalse(result.review["auto_applied"])
        self.assertTrue(result.requires_human_approval)
        self.assertFalse(result.published)
        self.assertEqual(result.review["proposal_sha256"],
                         canonical_sha(result.proposal))
        self.assertEqual(result.model, "test-model-only")
        self.assertEqual(provider.last_job.operation, "update")

    def test_only_explicit_selected_id_and_user_excerpt_are_sent(self):
        provider = StubProvider()
        prepare_update_with_provider(
            detail(), EXCERPT, [RULE_ID],
            provider=provider, model="test-model-only",
        )
        transmitted = provider.last_job.source_text
        self.assertIn(EXCERPT, transmitted)
        self.assertIn(RULE_ID, transmitted)
        self.assertNotIn(SECRET_HTML, transmitted)
        self.assertNotIn("private-icon.png", transmitted)
        self.assertNotIn("condition_html", transmitted)

    def test_missing_evidence_quote_fails_review(self):
        provider = StubProvider(corrupt_quote=True)
        with self.assertRaisesRegex(ValueError, "evidence quote"):
            prepare_update_with_provider(
                detail(), EXCERPT, [RULE_ID],
                provider=provider, model="test-model-only",
            )

    def test_wrong_operation_is_rejected_before_review(self):
        with self.assertRaisesRegex(ValueError, "wrong operation"):
            prepare_update_with_provider(
                detail(), EXCERPT, [RULE_ID],
                provider=StubProvider(wrong_operation=True),
                model="test-model-only",
            )

    def test_missing_ids_fail_before_provider_invocation(self):
        provider = StubProvider()
        with self.assertRaisesRegex(ValueError, "Unknown"):
            prepare_update_with_provider(
                detail(), EXCERPT, ["made-up:rule"],
                provider=provider, model="test-model-only",
            )
        self.assertIsNone(provider.last_job)


if __name__ == "__main__":
    unittest.main()
