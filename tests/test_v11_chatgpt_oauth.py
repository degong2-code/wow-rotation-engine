"""Synthetic OAuth/PKCE/JWKS tests. No real ChatGPT login, model call or tokens."""
from dataclasses import replace
from io import BytesIO
import json
import os
from pathlib import Path
import stat
from tempfile import TemporaryDirectory
import time
import unittest
from urllib import parse
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from engine.v2.chatgpt_oauth import (
    APP_NAME, CALLBACK_PATH, DYNAMIC_CLIENT, ISSUER, OAuthError,
    OAuthTokens, RESOURCE, SCOPES, begin_login, callback_result,
    exchange_code, fetch_jwks, fresh_host_id, verify_id_token,
    verified_connection,
)
from engine.v2.chatgpt_local_store import LocalAuthStore

ISSUED = "oaiapp_test-account_XY1234"
ISSUED_2 = "oaiapp_different-account_XY5678"


def b64(number):
    import base64
    data = number.to_bytes((number.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def signed_fixture(client_id, nonce, *, subject="subject-1",
                   issuer=ISSUER, expiry=3600):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = key.public_key().public_numbers()
    jwks = {"keys": [{
        "kty": "RSA", "kid": "synthetic-kid-1", "use": "sig",
        "alg": "RS256", "n": b64(pub.n), "e": b64(pub.e),
    }]}
    now = int(time.time())
    id_token = jwt.encode({
        "iss": issuer, "sub": subject, "aud": client_id,
        "nonce": nonce, "iat": now, "exp": now + expiry,
        "email": "synthetic@example.invalid",
    }, key, algorithm="RS256", headers={"kid": "synthetic-kid-1"})
    return id_token, jwks


def token_grant(id_token, *, scopes=None):
    return {
        "access_token": "synthetic-oauth-access",
        "refresh_token": "synthetic-refresh",
        "id_token": id_token,
        "scope": " ".join(sorted(scopes if scopes is not None else SCOPES)),
        "token_type": "Bearer",
        "expires_in": 3600,
        "earliest_refresh_at": 12,
    }


class CaptureHttp:
    def __init__(self, response: dict):
        self.response = response
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append(request)
        return BytesIO(json.dumps(self.response).encode())


class OAuthCoreTests(unittest.TestCase):
    def setUp(self):
        self.host_id = fresh_host_id()
        self.pending, self.auth_url = begin_login(43432, self.host_id)
        self.identity, self.jwks = signed_fixture(ISSUED, self.pending.nonce)
        self.callback = (
            CALLBACK_PATH + "?" + parse.urlencode({
                "code": "synthetic-code",
                "state": self.pending.state,
                "client_id": ISSUED,
                # Callback scopes must not be trusted.
                "scope": "chatgpt.tokens.use.direct",
            })
        )

    def test_initial_authorization_uses_documented_full_parameters(self):
        url = parse.urlsplit(self.auth_url)
        self.assertEqual(url.scheme, "https")
        self.assertEqual(url.netloc, "auth.openai.com")
        p = parse.parse_qs(url.query)
        self.assertEqual(p["client_id"], [DYNAMIC_CLIENT])
        self.assertEqual(p["agent_name_hint"], [APP_NAME])
        self.assertEqual(p["ext_agent_host_id"], [self.host_id])
        self.assertEqual(p["redirect_uri"],
                         [f"http://127.0.0.1:43432{CALLBACK_PATH}"])
        self.assertEqual(p["scope"][0].split(), sorted(SCOPES))
        self.assertEqual(p["resource"], [RESOURCE])
        self.assertEqual(p["response_type"], ["code"])
        self.assertEqual(p["code_challenge_method"], ["S256"])
        self.assertNotEqual(p["state"][0], p["nonce"][0])
        self.assertNotIn("code_verifier", p)
        self.assertNotIn("sk-", self.auth_url)

    def test_fresh_attempt_changes_pkce_state_and_nonce(self):
        another, url = begin_login(43432, self.host_id)
        self.assertNotEqual(another.state, self.pending.state)
        self.assertNotEqual(another.nonce, self.pending.nonce)
        self.assertNotEqual(another.verifier, self.pending.verifier)

    def test_callback_checks_state_and_issued_dynamic_client(self):
        out = callback_result(self.pending, self.callback)
        self.assertEqual(out.client_id, ISSUED)
        self.assertEqual(out.code, "synthetic-code")
        for invalid, error in [
            (self.callback.replace(self.pending.state, "attacker"), "state_mismatch"),
            (CALLBACK_PATH + "?state=" + self.pending.state + "&code=x", "issued_client_id_missing"),
            (self.callback + "&state=duplicate", "duplicate_callback_parameter"),
            ("/callback?" + parse.urlsplit(self.callback).query, "wrong_callback_path"),
            (CALLBACK_PATH + "?state=" + self.pending.state
             + "&error=access_denied", "consent_declined"),
        ]:
            with self.subTest(error=error), self.assertRaises(OAuthError) as caught:
                callback_result(self.pending, invalid)
            self.assertEqual(caught.exception.code, error)

    def test_reauthorization_reuses_id_and_rejects_account_swap(self):
        pending, url = begin_login(
            43433, self.host_id, issued_client_id=ISSUED,
            expected_subject="subject-1", login_hint="synthetic@example.invalid",
        )
        q = parse.parse_qs(parse.urlsplit(url).query)
        self.assertEqual(q["client_id"], [ISSUED])
        self.assertNotIn("agent_name_hint", q)
        self.assertEqual(callback_result(
            pending, CALLBACK_PATH + "?" + parse.urlencode({
                "state": pending.state, "code": "code",
            })
        ).client_id, ISSUED)
        with self.assertRaises(OAuthError) as caught:
            callback_result(pending, CALLBACK_PATH + "?" + parse.urlencode({
                "state": pending.state, "code": "code", "client_id": ISSUED_2,
            }))
        self.assertEqual(caught.exception.code, "registered_client_changed")

    def test_token_exchange_has_pkce_and_original_redirect_only(self):
        result = callback_result(self.pending, self.callback)
        http = CaptureHttp(token_grant(self.identity))
        tokens = exchange_code(self.pending, result, urlopen=http)
        self.assertEqual(tokens.access_token, "synthetic-oauth-access")
        self.assertEqual(len(http.requests), 1)
        req = http.requests[0]
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.full_url,
                         "https://auth.openai.com/api/accounts/oauth/token")
        params = parse.parse_qs(req.data.decode("ascii"))
        self.assertEqual(params["client_id"], [ISSUED])
        self.assertEqual(params["grant_type"], ["authorization_code"])
        self.assertEqual(params["code_verifier"], [self.pending.verifier])
        self.assertEqual(params["redirect_uri"], [self.pending.redirect_uri])
        self.assertEqual(params["resource"], [RESOURCE])
        self.assertNotIn("client_secret", params)

    def test_valid_signed_identity_and_scopes_create_plan_session(self):
        result = callback_result(self.pending, self.callback)
        http = CaptureHttp(token_grant(self.identity))
        tokens = exchange_code(self.pending, result, urlopen=http)
        conn = verified_connection(self.pending, result, tokens, jwks=self.jwks)
        self.assertTrue(conn.plan_enabled)
        self.assertEqual(conn.subject, "subject-1")
        self.assertEqual(conn.client_id, ISSUED)
        session = conn.to_plan_session(credits_disabled_confirmed=True)
        session.check()
        self.assertTrue(session.oauth_verified)
        self.assertNotIn("synthetic-oauth-access", repr(session))

    def test_missing_direct_scope_does_not_authorize_inference(self):
        result = callback_result(self.pending, self.callback)
        reduced = SCOPES.difference({"chatgpt.tokens.use.direct"})
        token = exchange_code(self.pending, result, urlopen=CaptureHttp(
            token_grant(self.identity, scopes=reduced)
        ))
        conn = verified_connection(self.pending, result, token, jwks=self.jwks)
        self.assertFalse(conn.plan_enabled)
        with self.assertRaises(OAuthError) as info:
            conn.to_plan_session(credits_disabled_confirmed=True)
        self.assertEqual(info.exception.code, "plan_scope_not_granted")

    def test_unverified_id_token_is_rejected_for_signature_and_issuer(self):
        wrong, other_keys = signed_fixture(ISSUED, self.pending.nonce)
        with self.assertRaises(OAuthError):
            verify_id_token(self.identity, client_id=ISSUED, nonce=self.pending.nonce,
                            jwks=other_keys)
        fake_issuer, keys = signed_fixture(
            ISSUED, self.pending.nonce, issuer="https://impostor.invalid"
        )
        with self.assertRaises(OAuthError):
            verify_id_token(fake_issuer, client_id=ISSUED, nonce=self.pending.nonce,
                            jwks=keys)
        with self.assertRaises(OAuthError):
            verify_id_token(self.identity, client_id=ISSUED_2, nonce=self.pending.nonce,
                            jwks=self.jwks)
        with self.assertRaises(OAuthError) as wrong_nonce:
            verify_id_token(self.identity, client_id=ISSUED, nonce="wrong",
                            jwks=self.jwks)
        self.assertEqual(wrong_nonce.exception.code, "nonce_mismatch")

    def test_expiration_and_none_alg_are_rejected(self):
        expired, jwks = signed_fixture(
            ISSUED, self.pending.nonce, expiry=-100
        )
        with self.assertRaises(OAuthError):
            verify_id_token(expired, client_id=ISSUED, nonce=self.pending.nonce,
                            jwks=jwks)
        none_alg = jwt.encode({"sub": "fake"}, key=None, algorithm="none")
        with self.assertRaises(OAuthError):
            verify_id_token(none_alg, client_id=ISSUED, nonce=self.pending.nonce,
                            jwks=jwks)

    def test_reauth_different_signed_subject_cannot_replace_account(self):
        pending, _ = begin_login(
            33445, self.host_id, issued_client_id=ISSUED,
            expected_subject="subject-1",
        )
        changed, keys = signed_fixture(
            ISSUED, pending.nonce, subject="different-user"
        )
        callback = callback_result(pending, CALLBACK_PATH + "?" + parse.urlencode({
            "code": "code", "state": pending.state,
        }))
        tokens = OAuthTokens(
            access_token="synthetic", refresh_token="synthetic-refresh",
            id_token=changed, scopes=SCOPES, expires_in=3600,
        )
        with self.assertRaises(OAuthError) as caught:
            verified_connection(pending, callback, tokens, jwks=keys)
        self.assertEqual(caught.exception.code, "reauthorized_account_mismatch")

    def test_jwks_endpoint_is_pinned_and_json_is_bounded(self):
        http = CaptureHttp(self.jwks)
        response = fetch_jwks(urlopen=http)
        self.assertEqual(response, self.jwks)
        self.assertEqual(http.requests[0].full_url,
                         "https://auth.openai.com/.well-known/jwks.json")


@unittest.skipUnless(os.name == "posix", "Unix-only owner permissions")
class LocalCredentialsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = LocalAuthStore(Path(self.tmp.name) / "private")
        self.host = self.store.host_id()

    def test_host_id_stable_and_credentials_owner_only(self):
        self.assertEqual(self.host, self.store.host_id())
        self.assertEqual(stat.S_IMODE(self.store.directory.stat().st_mode), 0o700)
        self.assertEqual(
            stat.S_IMODE((self.store.directory / "host.json").stat().st_mode),
            0o600,
        )

    def test_verified_connection_save_is_separate_from_public_repo(self):
        pending, _ = begin_login(31125, self.host)
        token, keys = signed_fixture(ISSUED, pending.nonce)
        result = callback_result(pending, CALLBACK_PATH + "?" + parse.urlencode({
            "code": "code", "state": pending.state, "client_id": ISSUED,
        }))
        conn = verified_connection(
            pending, result,
            OAuthTokens("synthetic-access", "synthetic-refresh",
                        token, SCOPES, 3600),
            jwks=keys,
        )
        self.store.save(conn)
        self.assertEqual(self.store.registered_client_ids(), (ISSUED,))
        ref = self.store.read_for_reauthorization(ISSUED)
        self.assertEqual(ref["subject"], "subject-1")
        self.assertEqual(ref["client_id"], ISSUED)
        file = self.store._path(self.store._account_name(ISSUED))
        self.assertEqual(stat.S_IMODE(file.stat().st_mode), 0o600)
        self.assertIn("synthetic-refresh", file.read_text())
        self.assertNotIn("synthetic-refresh", repr(conn))
        self.assertNotIn("synthetic-refresh", repr(self.store))

    def test_symlink_and_world_readable_records_rejected(self):
        record = self.store.directory / "host.json"
        record.chmod(0o644)
        with self.assertRaises(OAuthError) as caught:
            self.store.host_id()
        self.assertEqual(caught.exception.code, "oauth_credentials_not_private")
        record.unlink()
        record.symlink_to(Path(self.tmp.name) / "exfiltration")
        with self.assertRaises(OAuthError):
            self.store.host_id()

    def test_public_repo_path_is_rejected(self):
        from engine.v2.build import ROOT
        with self.assertRaises(OAuthError):
            LocalAuthStore(ROOT / "private-creds")


if __name__ == "__main__":
    unittest.main()
