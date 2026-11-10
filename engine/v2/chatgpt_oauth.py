"""Official ChatGPT plan OAuth authorization-code/PKCE and OIDC identity checks.

No chat cookies, developer API key, unverified JWT payloads or arbitrary
authorization endpoints. This core is network-neutral except injectable calls
to the pinned OpenAI token / JWKS endpoints. It does not run inference or grant
publishing rights. Use a maintained PyJWT cryptography verifier.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import base64
import hashlib
import hmac
import json
import re
import secrets
from typing import Callable
from urllib import parse, request as urlrequest
from urllib.error import HTTPError, URLError
from uuid import uuid4

import jwt

from .chatgpt_plan import PlanSession, REQUIRED_SCOPE

ISSUER = "https://auth.openai.com"
AUTHORIZE_URL = ISSUER + "/api/accounts/authorize"
TOKEN_URL = ISSUER + "/api/accounts/oauth/token"
JWKS_URL = ISSUER + "/.well-known/jwks.json"
RESOURCE = "https://api.openai.com/v1"
DYNAMIC_CLIENT = "dynamic_agent_client"
APP_NAME = "WoW Rotation Textbook"
CALLBACK_PATH = "/auth/callback"
SCOPES = frozenset({
    "openid", "profile", "email", "offline_access",
    "resource.invoke", REQUIRED_SCOPE,
})
MAX_JSON_BYTES = 64 * 1024
ISSUED_ID = re.compile(r"^oaiapp_[A-Za-z0-9_-]{3,256}$")
HOST_UUID = re.compile(r"^urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


class OAuthError(RuntimeError):
    """A non-sensitive failure code safe to show to the user."""
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def fresh_host_id() -> str:
    return "urn:uuid:" + str(uuid4())


def _callback_uri(port: int) -> str:
    if type(port) is not int or not 1 <= port <= 65535:
        raise OAuthError("invalid_loopback_port")
    return f"http://127.0.0.1:{port}{CALLBACK_PATH}"


def _base64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")


@dataclass(frozen=True)
class PendingAuth:
    state: str = field(repr=False)
    nonce: str = field(repr=False)
    verifier: str = field(repr=False)
    redirect_uri: str
    client_id: str
    host_id: str
    # Save the expected sub only for reauthorization, not first sign-in.
    expected_subject: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class AuthorizationResult:
    code: str = field(repr=False)
    client_id: str


@dataclass(frozen=True)
class OAuthTokens:
    access_token: str = field(repr=False)
    refresh_token: str = field(repr=False)
    id_token: str = field(repr=False)
    scopes: frozenset[str]
    expires_in: int
    earliest_refresh_at: int | None = None


@dataclass(frozen=True)
class VerifiedConnection:
    subject: str
    client_id: str
    host_id: str
    tokens: OAuthTokens = field(repr=False)
    email: str | None = None

    @property
    def plan_enabled(self) -> bool:
        return REQUIRED_SCOPE in self.tokens.scopes

    def to_plan_session(self, *, credits_disabled_confirmed: bool) -> PlanSession:
        # Identity sign-in alone does not grant subscription inference.
        if not self.plan_enabled:
            raise OAuthError("plan_scope_not_granted")
        return PlanSession(
            access_token=self.tokens.access_token,
            scopes=self.tokens.scopes,
            oauth_verified=True,
            credits_disabled_confirmed=credits_disabled_confirmed,
        )


def begin_login(port: int, host_id: str, *,
                issued_client_id: str | None = None,
                expected_subject: str | None = None,
                id_token_hint: str | None = None,
                login_hint: str | None = None) -> tuple[PendingAuth, str]:
    """Start a one-shot OAuth transaction. Caller starts listener FIRST."""
    if not isinstance(host_id, str) or not HOST_UUID.fullmatch(host_id):
        raise OAuthError("host_id_not_persisted")
    if issued_client_id is not None and not ISSUED_ID.fullmatch(issued_client_id):
        raise OAuthError("invalid_registered_client")
    if expected_subject is not None and (not issued_client_id
                                           or not isinstance(expected_subject, str)
                                           or not expected_subject.strip()):
        raise OAuthError("invalid_account_binding")
    if (id_token_hint or login_hint) and issued_client_id is None:
        raise OAuthError("account_hint_without_registration")
    for hint in (id_token_hint, login_hint):
        if hint is not None and (not isinstance(hint, str) or len(hint) > 4096):
            raise OAuthError("invalid_login_hint")
    state, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)  # 86 chars, RFC 7636 compliant
    challenge = _base64url(hashlib.sha256(verifier.encode("ascii")).digest())
    client = issued_client_id or DYNAMIC_CLIENT
    redirect_uri = _callback_uri(port)
    params = {
        "client_id": client,
        "ext_agent_host_id": host_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(sorted(SCOPES)),
        "resource": RESOURCE,
        "state": state,
        "nonce": nonce,
        "code_challenge_method": "S256",
        "code_challenge": challenge,
    }
    if client == DYNAMIC_CLIENT:
        params["agent_name_hint"] = APP_NAME
    if id_token_hint:
        params["id_token_hint"] = id_token_hint
    if login_hint:
        params["login_hint"] = login_hint
    return (
        PendingAuth(state, nonce, verifier, redirect_uri, client, host_id, expected_subject),
        AUTHORIZE_URL + "?" + parse.urlencode(params),
    )


def callback_result(pending: PendingAuth, callback_target: str) -> AuthorizationResult:
    """Validate loopback path, unique query values, state and registered ID.

    A caller must consume PendingAuth at most once regardless of success.
    Do not trust callback scope; token response grants are authoritative.
    """
    if not isinstance(callback_target, str) or len(callback_target) > 16384:
        raise OAuthError("invalid_callback")
    parsed = parse.urlsplit(callback_target)
    if parsed.scheme or parsed.netloc or parsed.path != CALLBACK_PATH or parsed.fragment:
        raise OAuthError("wrong_callback_path")
    try:
        fields = parse.parse_qs(parsed.query, strict_parsing=True,
                               keep_blank_values=True, max_num_fields=12)
    except ValueError:
        raise OAuthError("invalid_callback") from None
    if any(len(vals) != 1 for vals in fields.values()):
        raise OAuthError("duplicate_callback_parameter")
    state = fields.get("state", [""])[0]
    if not hmac.compare_digest(pending.state, state):
        raise OAuthError("state_mismatch")
    if "error" in fields:
        if "code" in fields:
            raise OAuthError("conflicting_callback")
        raise OAuthError("consent_declined" if fields["error"][0] == "access_denied"
                         else "authorization_failed")
    code = fields.get("code", [""])[0]
    if not code or len(code) > 4096:
        raise OAuthError("authorization_code_missing")
    returned_id = fields.get("client_id", [""])[0]
    if pending.client_id == DYNAMIC_CLIENT:
        if not ISSUED_ID.fullmatch(returned_id):
            raise OAuthError("issued_client_id_missing")
        client_id = returned_id
    else:
        if returned_id and returned_id != pending.client_id:
            raise OAuthError("registered_client_changed")
        client_id = pending.client_id
    return AuthorizationResult(code=code, client_id=client_id)


def _read_json(response, *, size=MAX_JSON_BYTES) -> dict:
    try:
        raw = response.read(size + 1)
        if len(raw) > size:
            raise OAuthError("oauth_response_too_large")
        body = json.loads(raw.decode("utf-8"))
        if not isinstance(body, dict):
            raise OAuthError("invalid_oauth_response")
        return body
    except (UnicodeError, json.JSONDecodeError):
        raise OAuthError("invalid_oauth_response") from None


def _post_form(fields: dict, *, urlopen: Callable, token_url=TOKEN_URL) -> dict:
    req = urlrequest.Request(
        token_url,
        data=parse.urlencode(fields).encode("ascii"),
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "Accept": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=30) as response:
            return _read_json(response)
    except HTTPError as exc:
        # Never reflect secret-containing token errors.
        error = "token_exchange_failed"
        if exc.code == 400:
            error = "authorization_code_expired"
        exc.close()
        raise OAuthError(error) from None
    except (OSError, URLError):
        raise OAuthError("token_endpoint_unavailable") from None


def _tokens(body: dict) -> OAuthTokens:
    for field_name in ("access_token", "refresh_token", "id_token", "scope"):
        if not isinstance(body.get(field_name), str) or not body[field_name]:
            raise OAuthError("incomplete_token_grant")
    expiry = body.get("expires_in")
    if type(expiry) is not int or not 1 <= expiry <= 86400:
        raise OAuthError("invalid_token_lifetime")
    if body.get("token_type", "").lower() != "bearer":
        raise OAuthError("invalid_token_type")
    # Scopes are those actually granted, not those originally requested.
    scopes = frozenset(body["scope"].split())
    if "openid" not in scopes:
        raise OAuthError("openid_scope_missing")
    earliest = body.get("earliest_refresh_at")
    if earliest is not None and type(earliest) is not int:
        raise OAuthError("invalid_refresh_time")
    if body["access_token"].startswith("sk-"):
        raise OAuthError("billing_key_not_oauth")
    return OAuthTokens(
        body["access_token"], body["refresh_token"], body["id_token"],
        scopes, expiry, earliest,
    )


def exchange_code(pending: PendingAuth, result: AuthorizationResult,
                  *, urlopen: Callable = urlrequest.urlopen) -> OAuthTokens:
    if pending.client_id != DYNAMIC_CLIENT and pending.client_id != result.client_id:
        raise OAuthError("registered_client_changed")
    if not ISSUED_ID.fullmatch(result.client_id):
        raise OAuthError("issued_client_id_missing")
    body = _post_form({
        "grant_type": "authorization_code",
        "client_id": result.client_id,
        "code": result.code,
        "code_verifier": pending.verifier,
        "redirect_uri": pending.redirect_uri,
        "resource": RESOURCE,
    }, urlopen=urlopen)
    return _tokens(body)


def verify_id_token(id_token: str, *, client_id: str, nonce: str,
                    jwks: dict) -> dict:
    """Reject unverified or unsigned tokens. No algorithm from JWT is trusted."""
    if not isinstance(id_token, str) or len(id_token) > 20000:
        raise OAuthError("invalid_identity_token")
    try:
        header = jwt.get_unverified_header(id_token)
        alg, kid = header.get("alg"), header.get("kid")
        if alg not in ("RS256", "ES256") or not isinstance(kid, str) or not kid:
            raise OAuthError("unsupported_jwt_algorithm")
        keys = jwks.get("keys") if isinstance(jwks, dict) else None
        if not isinstance(keys, list) or len(keys) > 25:
            raise OAuthError("invalid_jwks")
        choices = [
            k for k in keys if isinstance(k, dict)
            and k.get("kid") == kid and k.get("alg", alg) == alg
            and k.get("use", "sig") == "sig"
        ]
        if len(choices) != 1:
            raise OAuthError("identity_signing_key_not_found")
        key = jwt.PyJWK.from_dict(choices[0], algorithm=alg).key
        claims = jwt.decode(
            id_token, key=key, algorithms=[alg], issuer=ISSUER,
            audience=client_id, leeway=5,
            options={"require": ["iss", "sub", "aud", "exp", "iat", "nonce"]},
        )
    except OAuthError:
        raise
    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        raise OAuthError("identity_signature_or_claims_invalid") from None
    if not isinstance(claims.get("sub"), str) or not claims["sub"]:
        raise OAuthError("identity_subject_missing")
    if not isinstance(claims.get("nonce"), str) or not hmac.compare_digest(claims["nonce"], nonce):
        raise OAuthError("nonce_mismatch")
    if "sid" in claims and (not isinstance(claims["sid"], str)
                            or not claims["sid"].strip()):
        raise OAuthError("invalid_oidc_session_id")
    return claims


def fetch_jwks(*, urlopen: Callable = urlrequest.urlopen) -> dict:
    req = urlrequest.Request(JWKS_URL, headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=15) as response:
            return _read_json(response)
    except (HTTPError, OSError, URLError):
        raise OAuthError("jwks_unavailable") from None


def verified_connection(pending: PendingAuth, result: AuthorizationResult,
                        tokens: OAuthTokens, *,
                        jwks: dict) -> VerifiedConnection:
    claims = verify_id_token(tokens.id_token, client_id=result.client_id,
                             nonce=pending.nonce, jwks=jwks)
    if pending.expected_subject is not None and not hmac.compare_digest(
        pending.expected_subject, claims["sub"]
    ):
        raise OAuthError("reauthorized_account_mismatch")
    # A valid identity token without subscription scope is sign-in only.
    # Never infer plan permission from callback scope or ID token identity.
    return VerifiedConnection(
        subject=claims["sub"], client_id=result.client_id,
        host_id=pending.host_id, tokens=tokens,
        email=claims.get("email") if isinstance(claims.get("email"), str) else None,
    )
