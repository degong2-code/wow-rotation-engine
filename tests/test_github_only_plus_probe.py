"""Offline GitHub-only AI probe safety tests. Never invoke real Codex/OpenAI."""
from pathlib import Path
import os
import subprocess
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "probe_codespaces_plus.sh"
FAKE_CODEX = """#!/usr/bin/env python3
import json, os, pathlib, sys
cmd = sys.argv[1:]
log = os.environ.get('SYNTHETIC_CODEX_CALLS')
if log:
    with open(log, 'a', encoding='utf8') as f:
        f.write(repr(cmd) + '\\n')
if cmd == ['--version']:
    print('codex 1.2.3-synthetic')
elif cmd == ['login', 'status']:
    print('Logged in using ChatGPT' if os.environ.get('TEST_AUTH_MODE') == 'chatgpt' else 'Logged in using API key')
elif cmd and cmd[0] == 'exec':
    dest = pathlib.Path(cmd[cmd.index('-o') + 1])
    if os.environ.get('TEST_BAD_MODEL_RESULT') == '1':
        dest.write_text('{"status":"BAD","source_count":0}', encoding='utf8')
    else:
        dest.write_text('{"status":"ROTATION_PLUS_OK","source_count":0}', encoding='utf8')
else:
    sys.exit(99)
"""


class GitHubOnlyProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.binary = self.path / "codex"
        self.binary.write_text(FAKE_CODEX, encoding="utf-8")
        self.binary.chmod(0o700)
        self.log = self.path / "calls.txt"
        self.env = {
            **os.environ,
            "PATH": self.tmp.name + os.pathsep + os.environ.get("PATH", ""),
            "CODESPACES": "true",
            "TEST_AUTH_MODE": "chatgpt",
            "SYNTHETIC_CODEX_CALLS": str(self.log),
        }
        self.env.pop("OPENAI_API_KEY", None)
        self.env.pop("CODEX_API_KEY", None)

    def run_probe(self, *args, **env):
        vars = {**self.env, **env}
        return subprocess.run(
            ["/bin/bash", str(SCRIPT), *args],
            cwd=ROOT, env=vars, capture_output=True,
            text=True, timeout=10,
        )

    def calls(self):
        return self.log.read_text(encoding="utf8").splitlines() if self.log.exists() else []

    def test_preflight_never_runs_ai(self):
        r = self.run_probe("--preflight")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("No AI request made", r.stdout)
        self.assertFalse(any("'exec'" in x for x in self.calls()))

    def test_no_cloud_runner_allowed(self):
        r = self.run_probe("--probe", "--confirm-plus-usage", CODESPACES="")
        self.assertEqual(r.returncode, 3)
        self.assertEqual(self.calls(), [])

    def test_paid_api_key_fails_before_any_codex_call(self):
        r = self.run_probe("--probe", "--confirm-plus-usage", OPENAI_API_KEY="synthetic-paid-key")
        self.assertEqual(r.returncode, 4)
        self.assertNotIn("synthetic-paid-key", r.stdout + r.stderr)
        self.assertEqual(self.calls(), [])

    def test_explicit_confirmation_required(self):
        r = self.run_probe("--probe")
        self.assertEqual(r.returncode, 6)
        self.assertFalse(any("'exec'" in x for x in self.calls()))

    def test_only_chatgpt_login_is_accepted(self):
        r = self.run_probe("--probe", "--confirm-plus-usage", TEST_AUTH_MODE="api")
        self.assertEqual(r.returncode, 8)
        self.assertFalse(any("'exec'" in x for x in self.calls()))

    def test_synthetic_account_probe_completes_once(self):
        r = self.run_probe("--probe", "--confirm-plus-usage")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("PASS: one ChatGPT-authenticated", r.stdout)
        self.assertEqual(sum("'exec'" in x for x in self.calls()), 1)

    def test_schema_validation_rejects_false_success(self):
        r = self.run_probe("--probe", "--confirm-plus-usage", TEST_BAD_MODEL_RESULT="1")
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn("PASS:", r.stdout)
        self.assertEqual(sum("'exec'" in x for x in self.calls()), 1)


if __name__ == "__main__":
    unittest.main()
