"""Loopback OAuth smoke tests with a synthetic localhost browser callback only."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import os
import threading
from tempfile import TemporaryDirectory
import unittest
from urllib import parse, request as urlrequest
from unittest.mock import patch

from engine.v2.chatgpt_oauth import (
    CALLBACK_PATH, OAuthTokens, begin_login, fresh_host_id,
)
from engine.v2.chatgpt_signin import (
    connect_once, listen_for_callback,
)
from engine.v2.chatgpt_local_store import LocalAuthStore

# No outbound auth, JWKS, inference or billing requests in these tests.
ISSUED = "oaiapp_local-test-client_ABC123"


class LoopbackSmokeTests(unittest.TestCase):
    def test_local_callback_code_is_consumed_once_without_logging(self):
        with HTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler) as server:
            pending, auth_url = begin_login(server.server_port, fresh_host_id())
            callbacks = []
            def browser(url):
                params = parse.parse_qs(parse.urlsplit(url).query)
                callback_url = (
                    params["redirect_uri"][0] + "?" +
                    parse.urlencode({
                        "code": "SYNTHETIC_CALLBACK_SECRET",
                        "client_id": ISSUED,
                        "state": params["state"][0],
                    })
                )
                def send():
                    with urlrequest.urlopen(callback_url, timeout=5) as resp:
                        callbacks.append(resp.read())
                threading.Thread(target=send, daemon=True).start()
                return True
            result = listen_for_callback(pending, server, browser, auth_url)
            self.assertEqual(result.client_id, ISSUED)
            self.assertEqual(result.code, "SYNTHETIC_CALLBACK_SECRET")
            self.assertEqual(len(callbacks), 1)
            self.assertNotIn(b"SYNTHETIC_CALLBACK_SECRET", callbacks[0])

    def test_explicit_denial_stops_listener_without_token_exchange(self):
        with HTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler) as server:
            pending, auth_url = begin_login(server.server_port, fresh_host_id())
            outcomes = []
            def browser(url):
                params = parse.parse_qs(parse.urlsplit(url).query)
                callback_url = (
                    params["redirect_uri"][0] + "?" +
                    parse.urlencode({
                        "error": "access_denied",
                        "state": params["state"][0],
                    })
                )
                def send():
                    try:
                        urlrequest.urlopen(callback_url, timeout=5)
                    except Exception:
                        outcomes.append("denied")
                threading.Thread(target=send, daemon=True).start()
                return True
            from engine.v2.chatgpt_oauth import OAuthError
            with self.assertRaises(OAuthError) as caught:
                listen_for_callback(pending, server, browser, auth_url)
            self.assertEqual(caught.exception.code, "consent_declined")

    @unittest.skipUnless(os.name == "posix", "Unix local credential pilot")
    def test_user_initiated_local_flow_stops_at_sign_in_without_inference(self):
        from engine.v2.chatgpt_oauth import VerifiedConnection
        from .test_v11_chatgpt_oauth import signed_fixture
        with TemporaryDirectory() as directory:
            store = LocalAuthStore(Path(directory) / "credentials")
            signed_keys = {}
            def browser(url):
                params = parse.parse_qs(parse.urlsplit(url).query)
                cb = (
                    params["redirect_uri"][0] + "?" +
                    parse.urlencode({
                        "code": "synthetic-code",
                        "state": params["state"][0],
                        "client_id": ISSUED,
                    })
                )
                def send():
                    with urlrequest.urlopen(cb, timeout=5) as resp:
                        resp.read()
                threading.Thread(target=send, daemon=True).start()
                return True
            def exchange(pending, result):
                id_token, keys = signed_fixture(result.client_id, pending.nonce)
                signed_keys["jwks"] = keys
                return OAuthTokens(
                    access_token="synthetic-OAuth-access",
                    refresh_token="synthetic-OAuth-refresh",
                    id_token=id_token,
                    scopes=frozenset({
                        "openid", "profile", "email", "offline_access",
                        "resource.invoke", "chatgpt.tokens.use.direct",
                    }),
                    expires_in=3600,
                )
            with patch("engine.v2.chatgpt_signin.exchange_code", side_effect=exchange), \
                 patch("engine.v2.chatgpt_signin.fetch_jwks", side_effect=lambda: signed_keys["jwks"]), \
                 patch("engine.v2.chatgpt_signin.ChatGPTPlanProvider") as plan:
                summary = connect_once(store, browser_opener=browser)
                self.assertEqual(summary["status"], "SIGNED_IN")
                self.assertEqual(summary["plan_permission"], "granted")
                self.assertFalse(summary["inference_attempted"])
                self.assertEqual(summary["models"], [])
                self.assertEqual(store.registered_client_ids(), (ISSUED,))
                plan.assert_not_called()


if __name__ == "__main__":
    unittest.main()
