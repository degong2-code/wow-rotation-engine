"""Source-text observation and change detection, without storing source text.

User-supplied/authorized excerpts stay in local input files. The portable
output contains only hashes, source URL, time, and baseline rule locators.
These observations are NOT independently authenticated Wowhead content.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from .condition_worklist import original_rows
from .public_data import BASE, load as load_public

INPUT_SCHEMA = "manual-source-input-v1"
SNAPSHOT_SCHEMA = "source-hash-snapshot-v1"
DIFF_SCHEMA = "source-hash-diff-v1"
HASH_METHOD = "nfc-whitespace-collapse-sha256-v1"
HEX = re.compile(r"^[0-9a-f]{64}$")


def _error(msg: str) -> ValueError:
    return ValueError("Invalid source evidence: " + msg)


def _time(value: str) -> datetime:
    if not isinstance(value, str):
        raise _error("captured_at must be a timezone-aware string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise _error("invalid captured_at") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise _error("captured_at requires timezone offset")
    return parsed


def _catalog(base: Path):
    _, _, guides = load_public(base)
    return {g["guide_id"]: g["source_url"] for g in guides}, original_rows(base)


def normalized_digest(text: str) -> str:
    if not isinstance(text, str):
        raise _error("passage text must be a string")
    # Ignore formatting-only diffs; do not alter case or punctuation.
    normalized = re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()
    if len(normalized) < 5 or len(normalized) > 20000:
        raise _error("passage length must be 5..20000 normalized characters")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def capture(document: dict, base: Path = BASE) -> dict:
    if not isinstance(document, dict) or set(document) != {
        "schema_version", "guide_id", "source_url", "captured_at", "passages"
    }:
        raise _error("unexpected input fields/schema")
    if document["schema_version"] != INPUT_SCHEMA:
        raise _error("wrong input schema")
    urls, rules = _catalog(base)
    guide = document["guide_id"]
    if not isinstance(guide, str) or guide not in urls:
        raise _error("unknown guide_id")
    if document["source_url"] != urls[guide]:
        raise _error("source URL does not match registered guide")
    _time(document["captured_at"])
    passages = document["passages"]
    if not isinstance(passages, list) or not passages or len(passages) > 177:
        raise _error("passages must be a nonempty bounded list")
    seen = set()
    observations = []
    for index, item in enumerate(passages):
        if not isinstance(item, dict) or set(item) != {"rule_id", "text"}:
            raise _error(f"passage {index} must have rule_id and text only")
        rid = item["rule_id"]
        if not isinstance(rid, str) or rid not in rules or rules[rid]["guide_id"] != guide:
            raise _error(f"unknown or cross-guide rule_id: {rid}")
        if rid in seen:
            raise _error(f"duplicate rule_id: {rid}")
        seen.add(rid)
        observations.append({
            "rule_id": rid,
            "observed_text_sha256": normalized_digest(item["text"]),
            "v11_fragment_sha256": rules[rid]["fragment_sha256"],
        })
    observations.sort(key=lambda x: x["rule_id"])
    return {
        "schema_version": SNAPSHOT_SCHEMA,
        "hash_method": HASH_METHOD,
        "capture_kind": "user_supplied_unverified",
        "guide_id": guide,
        "source_url": document["source_url"],
        "captured_at": document["captured_at"],
        "external_source_verified": False,
        "source_text_in_snapshot": False,
        "automatic_publish_allowed": False,
        "observations": observations,
        "warning": "Observed hashes cannot establish independent source authenticity or rule meaning.",
    }


def validate_snapshot(snapshot: dict, base: Path = BASE) -> None:
    if not isinstance(snapshot, dict):
        raise _error("snapshot must be an object")
    required = {
        "schema_version", "hash_method", "capture_kind", "guide_id", "source_url",
        "captured_at", "external_source_verified", "source_text_in_snapshot",
        "automatic_publish_allowed", "observations", "warning"
    }
    if set(snapshot) != required:
        raise _error("unknown or missing snapshot properties")
    if snapshot["schema_version"] != SNAPSHOT_SCHEMA or snapshot["hash_method"] != HASH_METHOD:
        raise _error("wrong snapshot schema/hash method")
    if (snapshot["capture_kind"] != "user_supplied_unverified" or
            snapshot["external_source_verified"] is not False or
            snapshot["source_text_in_snapshot"] is not False or
            snapshot["automatic_publish_allowed"] is not False):
        raise _error("unverified source cannot become verified or publishable")
    if not isinstance(snapshot["warning"], str):
        raise _error("missing source disclaimer")
    _time(snapshot["captured_at"])
    urls, rules = _catalog(base)
    guide = snapshot["guide_id"]
    if not isinstance(guide, str) or guide not in urls or snapshot["source_url"] != urls[guide]:
        raise _error("source registration mismatch")
    items = snapshot["observations"]
    if not isinstance(items, list) or not items or len(items) > 177:
        raise _error("invalid observation count")
    seen = set()
    for item in items:
        if not isinstance(item, dict) or set(item) != {
            "rule_id", "observed_text_sha256", "v11_fragment_sha256"
        }:
            raise _error("unknown observation properties")
        rid = item["rule_id"]
        if not isinstance(rid, str) or rid in seen or rid not in rules or rules[rid]["guide_id"] != guide:
            raise _error("duplicate/foreign observation rule")
        seen.add(rid)
        if not isinstance(item["observed_text_sha256"], str) or not HEX.fullmatch(item["observed_text_sha256"]):
            raise _error("invalid observed text hash")
        if item["v11_fragment_sha256"] != rules[rid]["fragment_sha256"]:
            raise _error("V11 locator changed or forged")


def compare(previous: dict, current: dict, base: Path = BASE) -> dict:
    validate_snapshot(previous, base)
    validate_snapshot(current, base)
    if (previous["guide_id"], previous["source_url"]) != (
            current["guide_id"], current["source_url"]):
        raise _error("cannot compare unrelated guide/source")
    if _time(current["captured_at"]) <= _time(previous["captured_at"]):
        raise _error("current observation must be later than previous")
    old = {r["rule_id"]: r["observed_text_sha256"] for r in previous["observations"]}
    new = {r["rule_id"]: r["observed_text_sha256"] for r in current["observations"]}
    changed = sorted(rid for rid in old.keys() & new.keys() if old[rid] != new[rid])
    added = sorted(new.keys() - old.keys())
    missing = sorted(old.keys() - new.keys())
    unchanged = sorted(rid for rid in old.keys() & new.keys() if old[rid] == new[rid])
    affected = sorted(set(changed) | set(added) | set(missing))
    return {
        "schema_version": DIFF_SCHEMA,
        "guide_id": current["guide_id"],
        "source_url": current["source_url"],
        "previous_captured_at": previous["captured_at"],
        "current_captured_at": current["captured_at"],
        "changed_observed_rules": changed,
        "newly_observed_rules": added,
        "no_longer_observed_rules": missing,
        "unchanged_observed_rules": unchanged,
        "affected_rule_ids": affected,
        "affected_count": len(affected),
        "requires_human_review": bool(affected),
        "source_meaning_verified": False,
        "automatic_publish_allowed": False,
        "warning": "Missing/added observations describe input coverage, not proven changes to the article.",
    }


def _read(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _save(path: str, document: dict) -> None:
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(document, sort_keys=True, ensure_ascii=False,
                               indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Review-only source-hash evidence workflow")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("capture")
    ingest.add_argument("--input", required=True, help="Local, user-supplied text JSON. Do not commit.")
    ingest.add_argument("--output", default="dist/source-snapshot.json")
    diff = sub.add_parser("diff")
    diff.add_argument("--previous", required=True)
    diff.add_argument("--current", required=True)
    diff.add_argument("--output", default="dist/source-diff.json")
    args = parser.parse_args()
    try:
        result = (capture(_read(args.input)) if args.command == "capture" else
                  compare(_read(args.previous), _read(args.current)))
        _save(args.output, result)
        print(json.dumps({"command":args.command, "output":args.output,
                          "observations":len(result.get("observations", [])),
                          "affected_count":result.get("affected_count", 0),
                          "automatic_publish_allowed":False}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print("Source evidence failed:", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
