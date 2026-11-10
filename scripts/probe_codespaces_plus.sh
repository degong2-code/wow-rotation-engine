#!/usr/bin/env bash
# User-triggered ChatGPT subscription feasibility check IN GitHub Codespaces.
# --preflight sends no AI requests; --probe requires explicit confirmation.
set -euo pipefail
umask 077

MODE="${1:---preflight}"
CONFIRM="${2:-}"
if [[ "${CODESPACES:-}" != "true" ]]; then
  echo "BLOCKED: run inside your own GitHub Codespace, not a GitHub Actions runner."
  exit 3
fi
if [[ -n "${OPENAI_API_KEY:-}" || -n "${CODEX_API_KEY:-}" ]]; then
  echo "BLOCKED: API key detected. Do not use a paid API key for this test."
  exit 4
fi
if ! command -v codex >/dev/null 2>&1; then
  echo "BLOCKED: Codex CLI not installed. In your Codespace: npm install -g @openai/codex"
  exit 5
fi

case "$MODE" in
  --preflight)
    codex --version
    if codex login status >/dev/null 2>&1; then
      echo "Codex has some active login; verify it says ChatGPT (not API key)."
    else
      echo "No active Codex login. Enable device login in ChatGPT Security, then run:"
      echo "  codex login --device-auth"
      echo "Use the URL and one-time code only in your own browser."
    fi
    echo "No AI request made."
    ;;
  --probe)
    if [[ "$CONFIRM" != "--confirm-plus-usage" ]]; then
      echo "BLOCKED: explicit --confirm-plus-usage needed for one AI request."
      exit 6
    fi
    # A paid API-key account is never accepted as the expected ChatGPT session.
    AUTH_STATUS="$(codex login status 2>&1)" || {
      echo "BLOCKED: sign into ChatGPT in this Codespace first."
      exit 7
    }
    if ! grep -qi "chatgpt" <<< "$AUTH_STATUS"; then
      echo "BLOCKED: Codex login status did not confirm ChatGPT auth."
      exit 8
    fi
    TMP="$(mktemp -d "${TMPDIR:-/tmp}/rotation-plus-probe.XXXXXXXX")"
    trap 'rm -rf "$TMP"' EXIT
    cat > "$TMP/schema.json" <<'EOF'
{
  "type": "object",
  "properties": {
    "status": { "type": "string", "enum": ["ROTATION_PLUS_OK"] },
    "source_count": { "type": "integer" }
  },
  "required": ["status", "source_count"],
  "additionalProperties": false
}
EOF
    # Synthetic data only; private V11 HTML is never submitted here.
    codex exec --ephemeral --sandbox read-only \
      --output-schema "$TMP/schema.json" \
      -o "$TMP/result.json" \
      'Return a JSON object only. status must equal ROTATION_PLUS_OK and source_count must equal 0. This is a synthetic authentication/connectivity test, not a WoW gameplay request.' \
      >/dev/null
    python - "$TMP/result.json" <<'PY'
import json
import sys
from pathlib import Path
p = Path(sys.argv[1])
r = json.loads(p.read_text(encoding="utf-8"))
if set(r) != {"status", "source_count"} or r["status"] != "ROTATION_PLUS_OK" or r["source_count"] != 0:
    raise SystemExit("BLOCKED: response did not meet the synthetic schema/values")
print("PASS: one ChatGPT-authenticated Codex CLI JSON inference completed in GitHub Codespaces.")
print("This confirms Codex CLI use only, NOT direct SIWC Responses auth or GitHub Actions automation.")
PY
    ;;
  *)
    echo "Usage: bash scripts/probe_codespaces_plus.sh --preflight"
    echo "       bash scripts/probe_codespaces_plus.sh --probe --confirm-plus-usage"
    exit 2
    ;;
esac
