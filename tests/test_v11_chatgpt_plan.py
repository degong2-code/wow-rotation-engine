"""Offline integration tests for ChatGPT plan adapter.

All network requests are synthetic and no OAuth token, AI prompt or private V11
content is sent to the network or committed to GitHub.
"""
from __future__ import annotations

from dataclasses import replace
from io import BytesIO
import json
from urllib.error import HTTPError
import unittest

from engine.v2.ai_runtime import AIJob, AIProposal
from engine.v2.chatgpt_plan import (
    ChatGPTPlanProvider, PlanSession, PlanRequestError, REQUIRED_SCOPE,
    _safe_error,
)

TEST_TOKEN = "synthetic-SECRET-token-DO-NOT-LOG"
MODELS = {
    "models": [
        {"slug": "test-model-fast", "display_name": "Fast", "visibility": "list"},
        {"slug": "test-model-careful", "display_name": "Careful", "visibility": "list"},
        {"slug": "test-model-hidden", "display_name": "Hidden", "visibility": "hidden"},
    ]
}


def sse(*events):
    return b"".join(
        b"event: " + e["type"].encode("utf-8") + b"\n"
        + b"data: " + json.dumps(e, ensure_ascii=False).encode("utf-8")
        + b"\n\n"
        for e in events
    )


def good_stream():
    return sse(
        {"type": "response.output_text.delta", "delta": '{"rules":'},
        {"type": "response.output_text.delta", "delta": '[{"id":"test"}]}'},
        {"type": "response.completed", "response": {"output": []}},
    )


class FakeHTTP:
    def __init__(self, post_stream=None, *, models=MODELS):
        self.calls = []
        self.post_stream = good_stream() if post_stream is None else post_stream
        self.models = models

    def __call__(self, request, timeout):
        self.calls.append(request)
        path = request.full_url
        if path.endswith("/models"):
            return BytesIO(json.dumps(self.models).encode("utf-8"))
        if path.endswith("/responses"):
            return BytesIO(self.post_stream)
        raise AssertionError("unexpected endpoint: " + path)


class PlanAdapterTests(unittest.TestCase):
    def setUp(self):
        self.session = PlanSession(
            access_token=TEST_TOKEN,
            scopes=frozenset({REQUIRED_SCOPE}),
            credits_disabled_confirmed=True,
        )
        self.fake = FakeHTTP()
        self.provider = ChatGPTPlanProvider(self.session, urlopen=self.fake)
        self.job = AIJob(
            operation="extract",
            instruction="Extract safely; cite uncertainty",
            source_text="Synthetic priority row. Unverified.",
        )

    def test_model_discovery_is_account_specific(self):
        models = self.provider.list_models()
        self.assertEqual([m.slug for m in models],
                         ["test-model-fast", "test-model-careful"])
        self.assertEqual([m.display_name for m in models], ["Fast", "Careful"])
        self.assertEqual(self.fake.calls[0].get_method(), "GET")
        self.assertEqual(self.fake.calls[0].full_url,
                         "https://api.openai.com/v1/models")

    def test_streaming_plan_request_is_private_and_review_only(self):
        self.provider.list_models()
        candidate = self.provider.propose(self.job, model="test-model-careful")
        self.assertEqual(candidate.candidate, {"rules": [{"id": "test"}]})
        self.assertEqual(candidate.status, "review_required")
        self.assertFalse(candidate.gameplay_verified)
        self.assertFalse(candidate.auto_applied)
        self.assertFalse(candidate.auto_published)
        self.assertEqual(candidate.model, "test-model-careful")
        self.assertEqual(len(self.fake.calls), 2)
        request = self.fake.calls[1]
        self.assertEqual(request.full_url, "https://api.openai.com/v1/responses")
        self.assertEqual(request.get_method(), "POST")
        body = json.loads(request.data.decode("utf-8"))
        self.assertIs(body["store"], False)
        self.assertIs(body["stream"], True)
        self.assertNotIn("tools", body)
        self.assertNotIn("background", body)
        self.assertEqual(body["model"], "test-model-careful")
        self.assertNotIn(TEST_TOKEN, json.dumps(body))
        self.assertEqual(request.get_header("Authorization"), "Bearer " + TEST_TOKEN)

    def test_no_consent_no_request(self):
        missing = replace(self.session, scopes=frozenset())
        fake = FakeHTTP()
        with self.assertRaisesRegex(PlanRequestError, "not authorized"):
            ChatGPTPlanProvider(missing, urlopen=fake).list_models()
        self.assertEqual(fake.calls, [])

    def test_no_credit_safety_confirmation_no_request(self):
        not_confirmed = replace(self.session, credits_disabled_confirmed=False)
        fake = FakeHTTP()
        with self.assertRaisesRegex(PlanRequestError, "OFF"):
            ChatGPTPlanProvider(not_confirmed, urlopen=fake).list_models()
        self.assertEqual(fake.calls, [])

    def test_model_must_come_from_live_catalog(self):
        self.provider.list_models()
        with self.assertRaisesRegex(PlanRequestError, "not in"):
            self.provider.propose(self.job, model="gpt-invented")
        self.assertEqual(len(self.fake.calls), 1)

    def test_discovery_must_precede_inference(self):
        with self.assertRaisesRegex(PlanRequestError, "List account models"):
            self.provider.propose(self.job, model="test-model-fast")
        self.assertEqual(self.fake.calls, [])

    def test_429_limit_stops_without_retry_or_fallback(self):
        class UsageLimitHTTP(FakeHTTP):
            def __call__(self, request, timeout):
                self.calls.append(request)
                if request.full_url.endswith("/models"):
                    return BytesIO(json.dumps(MODELS).encode("utf8"))
                body = json.dumps({
                    "error": {"code": "subscription_sharing_usage_limit_exceeded"}
                }).encode("utf8")
                raise HTTPError(request.full_url, 429, "limit", {}, BytesIO(body))

        fake = UsageLimitHTTP()
        p = ChatGPTPlanProvider(self.session, urlopen=fake)
        p.list_models()
        with self.assertRaises(PlanRequestError) as info:
            p.propose(self.job, model="test-model-fast")
        self.assertEqual(info.exception.code, "subscription_sharing_usage_limit_exceeded")
        self.assertEqual(len(fake.calls), 2)
        self.assertNotIn(TEST_TOKEN, str(info.exception))
        self.assertNotIn("Synthetic priority", str(info.exception))

    def test_midstream_limit_has_no_partial_candidate(self):
        failed = sse(
            {"type": "response.output_text.delta", "delta": '{"rules":['},
            {"type": "response.failed", "response": {
                "error": {"code": "subscription_sharing_usage_limit_exceeded"}
            }},
        )
        p = ChatGPTPlanProvider(self.session, urlopen=FakeHTTP(failed))
        p.list_models()
        with self.assertRaises(PlanRequestError) as info:
            p.propose(self.job, model="test-model-fast")
        self.assertEqual(info.exception.code, "subscription_sharing_usage_limit_exceeded")

    def test_interrupted_and_incomplete_streams_fail_closed(self):
        for stream, code in [
            (sse({"type": "response.output_text.delta", "delta": '{"x":1}'}), "stream_interrupted"),
            (sse({"type": "response.incomplete"}), "response_incomplete"),
            (sse({"type": "response.completed", "response": {"output": []}}), "invalid_response"),
        ]:
            with self.subTest(code=code):
                p = ChatGPTPlanProvider(self.session, urlopen=FakeHTTP(stream))
                p.list_models()
                with self.assertRaises(PlanRequestError) as info:
                    p.propose(self.job, model="test-model-fast")
                self.assertEqual(info.exception.code, code)

    def test_response_completed_without_delta_can_use_message_content(self):
        data = sse({"type": "response.completed", "response": {
            "output": [{"type": "message", "content": [
                {"type": "output_text", "text": '{"ok":true}'}
            ]}]
        }})
        p = ChatGPTPlanProvider(self.session, urlopen=FakeHTTP(data))
        p.list_models()
        self.assertEqual(p.propose(self.job, model="test-model-fast").candidate, {"ok": True})

    def test_non_json_and_json_arrays_are_rejected(self):
        for text in ("No", '["not a proposal"]'):
            with self.subTest(text=text):
                stream = sse(
                    {"type": "response.output_text.delta", "delta": text},
                    {"type": "response.completed", "response": {"output": []}},
                )
                p = ChatGPTPlanProvider(self.session, urlopen=FakeHTTP(stream))
                p.list_models()
                with self.assertRaises(PlanRequestError) as info:
                    p.propose(self.job, model="test-model-fast")
                self.assertEqual(info.exception.code, "invalid_response")

    def test_bad_model_list_never_falls_back_to_default_model(self):
        for models in ({"models": []}, {"data": MODELS["models"]},
                       {"models": [{"slug": "x", "visibility": "list"}]}):
            with self.subTest(models=models):
                fake = FakeHTTP(models=models)
                with self.assertRaises(PlanRequestError):
                    ChatGPTPlanProvider(self.session, urlopen=fake).list_models()
                self.assertEqual(len(fake.calls), 1)

    def test_secret_is_redacted_from_session_and_errors(self):
        self.assertNotIn(TEST_TOKEN, repr(self.session))
        self.assertNotIn(TEST_TOKEN, str(_safe_error("unknown_failure", 500)))
        with self.assertRaises(ValueError):
            AIProposal(
                provider="test", model="test-model-fast", operation="extract",
                candidate={}, status="approved",
            )

    def test_ai_job_is_bounded_and_cannot_approve_directly(self):
        with self.assertRaises(ValueError):
            AIJob(operation="publish", instruction="go", source_text="raw")
        with self.assertRaises(ValueError):
            AIJob(operation="extract", instruction="go", source_text="x" * 160001)


if __name__ == "__main__":
    unittest.main()
