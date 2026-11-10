"""ChatGPT-plan usage transport for a locally run open-source V11 tool.

This is the authenticated *inference* half of Sign in with ChatGPT, NOT an
OAuth implementation. A separate local credential manager must perform
PKCE + signed ID token verification + scope consent, then hand a short-lived
access token to PlanSession. Never use a normal ChatGPT web session cookie,
unofficial backend endpoint, or an OpenAI billing API key here.

Official contract: GET /v1/models, POST /v1/responses with store=false and
stream=true. No automatic paid fallback, no retries, no web_search tool until
its plan-sharing support is verified. No prompt, token, or raw error is logged.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Callable, Iterable
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from .ai_runtime import AIJob, AIProposal, ModelOption

API_ROOT = "https://api.openai.com/v1"
REQUIRED_SCOPE = "chatgpt.tokens.use.direct"
USAGE_SETTINGS = "https://chatgpt.com/#settings/Usage"
MAX_CATALOG_BYTES = 1024 * 1024
MAX_EVENT_BYTES = 2 * 1024 * 1024
MAX_OUTPUT_CHARS = 160000


class PlanRequestError(RuntimeError):
    """Stable status, without private model input or credential contents."""
    def __init__(self, code: str, hint: str):
        self.code = code
        super().__init__(hint)


@dataclass(frozen=True)
class PlanSession:
    # Never log or serialize the access token.
    access_token: str = field(repr=False)
    scopes: frozenset[str] = field(default_factory=frozenset)
    # This is the user's confirmation, not a server-side credit-state proof.
    credits_disabled_confirmed: bool = False

    def check(self):
        if not isinstance(self.access_token, str) or not self.access_token.strip():
            raise PlanRequestError("not_connected", "Complete official ChatGPT sign-in first")
        if REQUIRED_SCOPE not in self.scopes:
            raise PlanRequestError("permission_missing", "ChatGPT plan usage was not authorized")
        if self.credits_disabled_confirmed is not True:
            raise PlanRequestError(
                "credit_safety_not_confirmed",
                "Confirm in ChatGPT Settings > Usage that app credit use is OFF",
            )


def _safe_error(code: str, http_status: int | None = None) -> PlanRequestError:
    # Error descriptions are deliberately local constants; never forward
    # server response bodies that could include user content.
    messages = {
        "subscription_sharing_usage_limit_exceeded":
            "ChatGPT plan usage limit reached; save work and check Settings > Usage",
        "subscription_sharing_usage_unavailable":
            "ChatGPT plan usage availability could not be checked",
        "subscription_sharing_unsupported_capability":
            "Requested capability or model is not supported by plan sharing",
        "subscription_sharing_route_not_supported":
            "The requested API route is not available for plan sharing",
        "subscription_sharing_user_not_eligible":
            "Account or workspace is not eligible for this usage route",
        "subscription_sharing_invalid_user":
            "ChatGPT session is invalid; reconnect through official sign-in",
        "invalid_grant": "ChatGPT authorization expired; sign in again",
        "response_incomplete": "AI response did not complete; no proposal created",
        "stream_interrupted": "AI stream stopped before completion; no proposal created",
        "invalid_response": "AI returned invalid structured data; no proposal created",
    }
    return PlanRequestError(
        code if code in messages else "provider_http_error",
        messages.get(code, f"ChatGPT plan request failed (HTTP {http_status or 'unknown'})"),
    )


def _error_code(body: bytes) -> str:
    try:
        obj = json.loads(body.decode("utf-8"))
        error = obj.get("error", {})
        if not isinstance(error, dict):
            return ""
        value = error.get("code", "")
        return value if isinstance(value, str) else ""
    except (UnicodeError, json.JSONDecodeError, AttributeError):
        return ""


def _events(stream: Iterable[bytes]):
    """Read SSE until a blank line; reject oversized and malformed frames."""
    data, used = [], 0
    for raw in stream:
        if not isinstance(raw, bytes):
            raise _safe_error("invalid_response")
        used += len(raw)
        if used > MAX_EVENT_BYTES:
            raise _safe_error("invalid_response")
        try:
            line = raw.decode("utf-8").rstrip("\r\n")
        except UnicodeError:
            raise _safe_error("invalid_response") from None
        if not line:
            if data:
                try:
                    yield json.loads("\n".join(data))
                except json.JSONDecodeError:
                    raise _safe_error("invalid_response") from None
                data = []
            continue
        if line.startswith(":") or line.startswith("event:"):
            continue
        if line.startswith("data:"):
            value = line[5:].lstrip(" ")
            if value == "[DONE]":
                continue
            data.append(value)
        elif not line.startswith(("id:", "retry:")):
            raise _safe_error("invalid_response")
    # A complete response cannot depend on a truncated last event.
    if data:
        raise _safe_error("stream_interrupted")


def _extract_completed_text(event: dict) -> str:
    response = event.get("response", {})
    if not isinstance(response, dict):
        return ""
    strings = [
        segment["text"]
        for block in response.get("output", [])
        if isinstance(block, dict) and block.get("type") == "message"
        for segment in block.get("content", [])
        if isinstance(segment, dict) and segment.get("type") == "output_text"
        and isinstance(segment.get("text"), str)
    ]
    return "".join(strings)


class ChatGPTPlanProvider:
    """Requires a valid user-authorized OAuth session, never an API key."""
    def __init__(self, session: PlanSession, *, urlopen: Callable = urlrequest.urlopen):
        self._session = session
        self._urlopen = urlopen
        self._models: tuple[ModelOption, ...] = ()

    def _call(self, path: str, payload: dict | None = None):
        self._session.check()
        method = "GET" if payload is None else "POST"
        data = None if payload is None else json.dumps(
            payload, ensure_ascii=False,
        ).encode("utf-8")
        req = urlrequest.Request(
            API_ROOT + path, method=method, data=data,
            headers={
                "Authorization": "Bearer " + self._session.access_token,
                "Content-Type": "application/json",
            },
        )
        try:
            return self._urlopen(req, timeout=90)
        except HTTPError as exc:
            try:
                raw = exc.read(16384)
                code = _error_code(raw)
            except OSError:
                code = ""
            finally:
                exc.close()
            raise _safe_error(code, exc.code) from None
        except (URLError, OSError):
            raise PlanRequestError("transport_unavailable", "Network connection failed") from None

    def list_models(self) -> tuple[ModelOption, ...]:
        """Get real account-scoped model slugs. No Sol/Luna hardcoding."""
        with self._call("/models") as response:
            raw = response.read(MAX_CATALOG_BYTES + 1)
        if len(raw) > MAX_CATALOG_BYTES:
            raise _safe_error("invalid_response")
        try:
            body = json.loads(raw)
            models = body["models"]
        except (UnicodeError, KeyError, TypeError, json.JSONDecodeError):
            raise _safe_error("invalid_response") from None
        if not isinstance(models, list):
            raise _safe_error("invalid_response")
        result = []
        seen = set()
        for row in models:
            if not isinstance(row, dict) or row.get("visibility") != "list":
                continue
            slug = row.get("slug")
            label = row.get("display_name")
            if (not isinstance(slug, str) or not slug or len(slug) > 100
                    or not isinstance(label, str) or not label
                    or slug in seen):
                raise _safe_error("invalid_response")
            result.append(ModelOption(slug=slug, display_name=label))
            seen.add(slug)
        if not result:
            raise PlanRequestError("no_available_models", "No selectable models in this account")
        self._models = tuple(result)
        return self._models

    def propose(self, job: AIJob, *, model: str) -> AIProposal:
        if not isinstance(job, AIJob):
            raise ValueError("Expected a validated AIJob")
        self._session.check()
        if not self._models:
            raise PlanRequestError("models_not_loaded", "List account models before analysis")
        if model not in {m.slug for m in self._models}:
            raise PlanRequestError("model_not_available", "Model is not in the selected account catalog")
        # Do not enable web_search, background mode or other paid features.
        payload = {
            "model": model,
            "instructions": (
                "Return exactly one JSON object. Extract only facts supported by "
                "the supplied material. Preserve uncertainty and source disagreement. "
                "Never mark gameplay as verified or approved.\n" + job.instruction
            ),
            "input": job.source_text,
            "store": False,
            "stream": True,
        }
        completed = False
        chunks = []
        snapshot = ""
        # The request is attempted once; retrying may consume additional usage.
        with self._call("/responses", payload) as response:
            try:
                for event in _events(response):
                    kind = event.get("type")
                    if kind == "response.output_text.delta":
                        delta = event.get("delta")
                        if not isinstance(delta, str):
                            raise _safe_error("invalid_response")
                        chunks.append(delta)
                        if sum(map(len, chunks)) > MAX_OUTPUT_CHARS:
                            raise _safe_error("invalid_response")
                    elif kind == "response.failed":
                        err = event.get("response", {}).get("error") or {}
                        code = err.get("code", "") if isinstance(err, dict) else ""
                        raise _safe_error(code if isinstance(code, str) else "")
                    elif kind == "response.incomplete":
                        raise _safe_error("response_incomplete")
                    elif kind == "response.completed":
                        if completed:
                            raise _safe_error("invalid_response")
                        completed = True
                        snapshot = _extract_completed_text(event)
            except (UnicodeError, TypeError, AttributeError):
                raise _safe_error("invalid_response") from None
        if not completed:
            raise _safe_error("stream_interrupted")
        text = "".join(chunks) if chunks else snapshot
        if not isinstance(text, str) or not text or len(text) > MAX_OUTPUT_CHARS:
            raise _safe_error("invalid_response")
        try:
            candidate = json.loads(text)
        except json.JSONDecodeError:
            raise _safe_error("invalid_response") from None
        if not isinstance(candidate, dict):
            raise _safe_error("invalid_response")
        return AIProposal(
            provider="chatgpt_plan", model=model, operation=job.operation,
            candidate=candidate,
        )
