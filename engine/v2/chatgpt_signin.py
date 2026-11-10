"""User-initiated local Sign in with ChatGPT pilot (Windows WSL / Linux).

Run on the USER'S local machine only. No login starts during import or CI.
No token, callback code, PKCE values or authorization URL is printed. An
OAuth login is separate from optional model-listing; no inference is run here.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import time
import webbrowser

from .chatgpt_local_store import LocalAuthStore
from .chatgpt_oauth import (
    begin_login, callback_result, exchange_code, fetch_jwks,
    verified_connection, OAuthError, CALLBACK_PATH,
)
from .chatgpt_plan import ChatGPTPlanProvider, PlanRequestError

LOGIN_WAIT_SECONDS = 240


def listen_for_callback(pending, server: HTTPServer, browser_opener, login_url: str,
                        *, monotonic=time.monotonic) -> object:
    """One state-bound login result; never echo query, code, or token in UI."""
    state = {"result": None, "error": None}
    expected_host = f"127.0.0.1:{server.server_port}"

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            # Default logging would LEAK authorization code via request target.
            pass

        def do_GET(self):
            if self.headers.get("Host") != expected_host:
                self.send_error(400, "Invalid local callback host")
                return
            if self.path.split("?", 1)[0] != CALLBACK_PATH:
                self.send_error(404, "Not found")
                return
            if state["result"] is not None:
                self.send_error(409, "Callback already consumed")
                return
            try:
                result = callback_result(pending, self.path)
            except OAuthError as exc:
                # A valid-state decline is terminal; malformed callbacks are not.
                if exc.code == "consent_declined":
                    state["error"] = exc.code
                # Don't reveal state, OAuth codes or account info in browser.
                self.send_error(400, "Invalid or declined authorization")
                return
            state["result"] = result
            body = b"<html><body>ChatGPT sign-in callback received. You may close this tab.</body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'none'")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    # Prevent accidental globally exposed bind / different host.
    if server.server_address[0] != "127.0.0.1":
        raise OAuthError("callback_not_loopback")
    previous_handler = server.RequestHandlerClass
    server.RequestHandlerClass = Handler
    try:
        if not browser_opener(login_url):
            raise OAuthError("system_browser_open_failed")
        deadline = monotonic() + LOGIN_WAIT_SECONDS
        server.timeout = 1
        while state["result"] is None and state["error"] is None and monotonic() < deadline:
            server.handle_request()
        if state["error"] is not None:
            raise OAuthError(state["error"])
        if state["result"] is None:
            raise OAuthError("callback_timeout_or_declined")
        return state["result"]
    finally:
        server.RequestHandlerClass = previous_handler


def connect_once(store: LocalAuthStore, *,
                 client_id: str | None = None,
                 new_account: bool = False,
                 browser_opener=webbrowser.open,
                 server_factory=HTTPServer,
                 model_listing: bool = False,
                 credits_disabled_confirmed: bool = False) -> dict:
    """Explicit user entrypoint. Only this function starts browser/network."""
    if model_listing and not credits_disabled_confirmed:
        raise OAuthError("confirm_app_credits_off_before_model_listing")
    existing = store.registered_client_ids()
    if new_account and client_id:
        raise OAuthError("conflicting_account_selection")
    if client_id is not None:
        if client_id not in existing:
            raise OAuthError("unknown_registered_client")
    elif not new_account:
        if len(existing) > 1:
            raise OAuthError("multiple_accounts_require_client_selection")
        client_id = existing[0] if existing else None

    hints = store.read_for_reauthorization(client_id) if client_id else None
    # Loopback listener starts before opening OpenAI authorization page.
    with server_factory(("127.0.0.1", 0), BaseHTTPRequestHandler) as server:
        pending, url = begin_login(
            server.server_port, store.host_id(),
            issued_client_id=client_id,
            expected_subject=hints["subject"] if hints else None,
            id_token_hint=hints["id_token_hint"] if hints else None,
            login_hint=hints["email"] if hints else None,
        )
        result = listen_for_callback(pending, server, browser_opener, url)
    # Browser login is NOT identity validation. Exchange and validate first.
    tokens = exchange_code(pending, result)
    connection = verified_connection(pending, result, tokens, jwks=fetch_jwks())
    store.save(connection)
    report = {
        "status": "SIGNED_IN",
        "client_id": connection.client_id,
        "plan_permission": "granted" if connection.plan_enabled else "not_granted",
        "models": [],
        "inference_attempted": False,
        "paid_fallback_allowed": False,
    }
    if model_listing:
        if not connection.plan_enabled:
            raise OAuthError("plan_scope_not_granted")
        session = connection.to_plan_session(
            credits_disabled_confirmed=credits_disabled_confirmed,
        )
        choices = ChatGPTPlanProvider(session).list_models()
        report["models"] = [
            {"slug": choice.slug, "name": choice.display_name}
            for choice in choices
        ]
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="User-initiated ChatGPT Plus OAuth login (local WSL/Linux)"
    )
    parser.add_argument("command", choices=("status", "login"))
    parser.add_argument("--account", help="Existing issued client ID for reauthorization")
    parser.add_argument("--new-account", action="store_true")
    parser.add_argument("--list-models", action="store_true",
                        help="List account models after explicit OAuth login")
    parser.add_argument("--confirm-credits-off", action="store_true",
                        help="User confirms ChatGPT Settings > Usage app credits OFF")
    args = parser.parse_args(argv)
    try:
        store = LocalAuthStore()
        if args.command == "status":
            print("Saved ChatGPT registrations:", len(store.registered_client_ids()))
            print("No model request, inference, or login was performed.")
            return 0
        print("Opening system browser for user-approved ChatGPT authorization.")
        print("The local callback listens only on 127.0.0.1.")
        print("No AI inference request will be sent.")
        summary = connect_once(
            store, client_id=args.account, new_account=args.new_account,
            model_listing=args.list_models,
            credits_disabled_confirmed=args.confirm_credits_off,
        )
        print("Authorization:", summary["status"])
        print("ChatGPT plan permission:", summary["plan_permission"])
        if args.list_models:
            print("Account model options:")
            for item in summary["models"]:
                print("-", item["name"], "("+item["slug"]+")")
        return 0
    except (OAuthError, PlanRequestError) as exc:
        # Stable local error codes only, never token response bodies.
        print("Sign-in stopped:", exc.code)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
