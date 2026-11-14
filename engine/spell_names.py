"""Fail-closed ko_KR spell-name evidence audit.

The inherited V11 spell dictionary is NEVER modified by this module.
A live Blizzard Game Data API observation is comparison evidence, not editorial
approval of a rotation, translation, or spell identity.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from .public_data import BASE, validate as validate_public

TOKEN_URL = "https://oauth.battle.net/token"
SPELL_ENDPOINT = "https://kr.api.blizzard.com/data/wow/spell/{spell_id}?namespace=static-kr&locale=ko_KR"
MEDIA_ENDPOINT = "https://kr.api.blizzard.com/data/wow/media/spell/{spell_id}?namespace=static-kr&locale=ko_KR"
OFFICIAL_MEDIA_HOSTS = frozenset({"render.worldofwarcraft.com"})
SOURCE = "blizzard-game-data-api"
LOCALE = "ko_KR"
REGION = "kr"
SNAPSHOT_VERSION = "spell-name-snapshot-v1"


def inventory(base: Path = BASE) -> dict[int, list[str]]:
    report = validate_public(base)
    if not report["ok"]:
        raise ValueError("Public dataset invalid: " + "; ".join(report["errors"]))
    doc = json.loads((base / "spells.json").read_text(encoding="utf-8"))
    labels: dict[int, set[str]] = {}
    for row in doc["spells"]:
        labels.setdefault(row["spell_id"], set()).add(row["name_ko"])
    return {sid: sorted(labels[sid]) for sid in sorted(labels)}


def _json_response(req: Request, opener=urlopen) -> dict:
    with opener(req, timeout=20) as response:
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Expected JSON object from remote API")
    return value


def oauth_token(client_id: str, client_secret: str, opener=urlopen) -> str:
    if not client_id or not client_secret:
        raise ValueError("BLIZZARD_CLIENT_ID and BLIZZARD_CLIENT_SECRET are required")
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    req = Request(
        TOKEN_URL,
        data=urlencode({"grant_type": "client_credentials"}).encode("ascii"),
        headers={
            "Authorization": "Basic " + basic,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        method="POST",
    )
    result = _json_response(req, opener=opener)
    token = result.get("access_token")
    if not isinstance(token, str) or not token:
        raise ValueError("OAuth returned no access token")
    return token


def fetch_spell(spell_id: int, token: str, opener=urlopen, sleeper=time.sleep) -> dict:
    if type(spell_id) is not int or spell_id <= 0:
        raise ValueError("Invalid spell id")
    url = SPELL_ENDPOINT.format(spell_id=spell_id)
    req = Request(url, headers={"Authorization": "Bearer " + token,
                                "Accept": "application/json"})
    for attempt in range(3):
        try:
            result = _json_response(req, opener=opener)
            if result.get("id") != spell_id:
                return {"spell_id": spell_id, "status": "invalid_response"}
            name = result.get("name")
            if isinstance(name, dict):
                name = name.get("ko_KR")
            if not isinstance(name, str) or not name.strip():
                return {"spell_id": spell_id, "status": "missing_localized_name"}
            return {"spell_id": spell_id, "status": "found",
                    "name_ko": name.strip()}
        except HTTPError as exc:
            status = exc.code
            if status == 404:
                return {"spell_id": spell_id, "status": "not_found"}
            if status in (401, 403):
                raise RuntimeError(f"Blizzard API authorization failed (HTTP {status})") from None
            if status in (429, 500, 502, 503, 504) and attempt < 2:
                sleeper(min(2**attempt, 4))
                continue
            return {"spell_id": spell_id, "status": "request_error",
                    "http_status": status}
        except (URLError, ValueError, UnicodeError, json.JSONDecodeError):
            if attempt < 2:
                sleeper(min(2**attempt, 4))
                continue
            return {"spell_id": spell_id, "status": "request_error"}
    raise AssertionError("unreachable")


def fetch_spell_media(spell_id: int, token: str, opener=urlopen,
                      sleeper=time.sleep) -> dict:
    """Retrieve official Blizzard icon asset as review evidence, not UI approval.

    The URL must be a Blizzard rendering CDN link; no third-party redirect,
    made-up filename, or guessed icon is admitted as official evidence.
    """
    if type(spell_id) is not int or spell_id <= 0:
        raise ValueError("Invalid spell id")
    req = Request(
        MEDIA_ENDPOINT.format(spell_id=spell_id),
        headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
    )
    for attempt in range(3):
        try:
            result = _json_response(req, opener=opener)
            if result.get("id") != spell_id:
                return {"status": "invalid_response"}
            assets = result.get("assets")
            if not isinstance(assets, list):
                return {"status": "missing_assets"}
            icons = [a.get("value") for a in assets
                     if isinstance(a, dict) and a.get("key") == "icon"]
            if len(icons) != 1 or not isinstance(icons[0], str):
                return {"status": "missing_icon"}
            u = urlsplit(icons[0])
            if (u.scheme != "https" or u.hostname not in OFFICIAL_MEDIA_HOSTS
                or u.username or u.password or u.query or u.fragment
                or not u.path.lower().endswith((".jpg", ".png", ".webp"))):
                return {"status": "untrusted_icon_url"}
            return {"status": "found", "icon_url": icons[0]}
        except HTTPError as exc:
            if exc.code in (401, 403):
                raise RuntimeError("Blizzard media API authorization failed") from None
            if exc.code == 404:
                return {"status": "not_found"}
            if exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                sleeper(min(2**attempt, 4))
                continue
            return {"status": "request_error"}
        except (URLError, ValueError, UnicodeError, json.JSONDecodeError):
            if attempt < 2:
                sleeper(min(2**attempt, 4))
                continue
            return {"status": "request_error"}
    raise AssertionError("unreachable")


def fetch_snapshot(ids: list[int], token: str, opener=urlopen,
                   sleeper=time.sleep, delay_seconds: float = 0.15,
                   include_media: bool = False) -> dict:
    if len(ids) != len(set(ids)) or any(type(x) is not int or x <= 0 for x in ids):
        raise ValueError("Expected unique positive spell IDs")
    observations = []
    for i, sid in enumerate(sorted(ids)):
        if i and delay_seconds:
            sleeper(delay_seconds)
        observation = fetch_spell(sid, token, opener=opener, sleeper=sleeper)
        if include_media and observation["status"] == "found":
            observation["media"] = fetch_spell_media(
                sid, token, opener=opener, sleeper=sleeper,
            )
        observations.append(observation)
    return {
        "schema_version": SNAPSHOT_VERSION,
        "source": SOURCE,
        "region": REGION,
        "locale": LOCALE,
        "namespace": "static-kr",
        "checked_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "observations": observations,
        "notice": "External observations; require review before changing approved localization.",
    }


def _validate_snapshot(snapshot: dict, known_ids: set[int]) -> dict[int, dict]:
    if not isinstance(snapshot, dict) or any(snapshot.get(k) != v for k,v in (
        ("schema_version", SNAPSHOT_VERSION), ("source", SOURCE),
        ("region", REGION), ("locale", LOCALE), ("namespace", "static-kr"))):
        raise ValueError("Invalid snapshot provenance, locale, or schema")
    timestamp = snapshot.get("checked_at_utc")
    if not isinstance(timestamp, str) or not timestamp.endswith("+00:00"):
        raise ValueError("Snapshot requires an explicit UTC timestamp")
    rows = snapshot.get("observations")
    if not isinstance(rows, list):
        raise ValueError("Missing snapshot observations")
    seen: dict[int, dict] = {}
    statuses = {"found", "not_found", "request_error",
                "invalid_response", "missing_localized_name"}
    for r in rows:
        if not isinstance(r, dict):
            raise ValueError("Malformed observation")
        sid = r.get("spell_id")
        if type(sid) is not int or sid not in known_ids or sid in seen:
            raise ValueError("Duplicate or unexpected observation spell ID")
        if r.get("status") not in statuses:
            raise ValueError("Unsupported observation status")
        if r["status"] == "found" and (
            not isinstance(r.get("name_ko"), str) or not r["name_ko"].strip()
        ):
            raise ValueError("Found observation must include name_ko")
        if r["status"] != "found" and "name_ko" in r:
            raise ValueError("Non-found observation cannot include a name")
        media = r.get("media")
        if media is not None:
            if not isinstance(media, dict) or media.get("status") not in {
                "found", "not_found", "request_error", "invalid_response",
                "missing_assets", "missing_icon", "untrusted_icon_url",
            }:
                raise ValueError("Invalid media observation")
            if media["status"] == "found":
                u = urlsplit(media.get("icon_url", ""))
                if (u.scheme != "https" or u.hostname not in OFFICIAL_MEDIA_HOSTS
                    or u.username or u.password or u.query or u.fragment
                    or not u.path.lower().endswith((".jpg", ".png", ".webp"))):
                    raise ValueError("Invalid media URL")
            elif "icon_url" in media:
                raise ValueError("Unverified media cannot supply icon URL")
        seen[sid] = r
    return seen


def audit(base: Path = BASE, snapshot: dict | None = None) -> dict:
    labels = inventory(base)
    observed = _validate_snapshot(snapshot, set(labels)) if snapshot is not None else {}
    counts = {
        "distinct_spell_ids": len(labels),
        "inherited_name_records": len(json.loads((base / "spells.json").read_text(encoding="utf-8"))["spells"]),
        "observations_found_matching": 0,
        "observations_found_mismatching": 0,
        "observations_not_found": 0,
        "observations_other_issue": 0,
        "not_checked": 0,
        "conflicting_inherited_names": 0,
        "official_names_auto_approved": 0,
    }
    records = []
    for sid, inherited in labels.items():
        observation = observed.get(sid)
        if len(inherited) > 1:
            counts["conflicting_inherited_names"] += 1
        if observation is None:
            status = "not_checked"
            counts["not_checked"] += 1
        elif observation["status"] == "found":
            status = ("name_matches_inherited" if observation["name_ko"] in inherited
                      else "name_disagrees_with_inherited")
            counts["observations_found_matching" if status == "name_matches_inherited"
                   else "observations_found_mismatching"] += 1
        elif observation["status"] == "not_found":
            status = "not_found_in_api"
            counts["observations_not_found"] += 1
        else:
            status = observation["status"]
            counts["observations_other_issue"] += 1
        rec = {"spell_id": sid, "inherited_names_ko": inherited,
               "comparison": status, "review": "pending"}
        if observation and observation["status"] == "found":
            rec["observed_name_ko"] = observation["name_ko"]
            if isinstance(observation.get("media"), dict):
                rec["official_icon_evidence"] = observation["media"]
                rec["icon_review"] = "pending"
        records.append(rec)
    return {
        "schema_version": "spell-name-audit-v1",
        "source_scope": "V11 inherited labels vs optional Blizzard ko_KR observations",
        "snapshot_supplied": snapshot is not None,
        "counts": counts,
        "publish_ready": False,
        "records": records,
        "blockers": [
            "Imported V11 names are not independently authenticated.",
            "Matching API observations remain review candidates, not automatic approvals.",
            "Name matching alone does not establish rotation or Advanced Tips correctness.",
            "API 404/unavailable does not imply a spell is invalid or renamed.",
        ],
    }


def _write(path: str, doc: dict):
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2,
                              sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="Korean WoW spell-name comparison evidence")
    sub = p.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("audit")
    verify.add_argument("--snapshot")
    verify.add_argument("--output", default="dist/spell-name-audit.json")
    verify.add_argument("--require-all-matched", action="store_true")
    fetch = sub.add_parser("fetch")
    fetch.add_argument("--output", default="dist/spell-name-snapshot.json")
    fetch.add_argument("--report", default="dist/spell-name-audit.json")
    fetch.add_argument("--max-ids", type=int, default=176)
    fetch.add_argument("--delay-ms", type=int, default=150)
    fetch.add_argument("--include-media", action="store_true",
                       help="Also query authenticated Blizzard spell icon media; review-only")
    args = p.parse_args()

    try:
        if args.command == "audit":
            snapshot = (json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
                        if args.snapshot else None)
            result = audit(snapshot=snapshot)
            _write(args.output, result)
            print("Spell audit:", result["counts"])
            if args.require_all_matched:
                c = result["counts"]
                return 0 if (c["observations_found_matching"] == c["distinct_spell_ids"]
                             and not c["observations_found_mismatching"]
                             and not c["conflicting_inherited_names"]) else 1
            return 0

        ids = list(inventory())
        if not (1 <= args.max_ids <= len(ids)) or not (0 <= args.delay_ms <= 5000):
            raise ValueError("Invalid max-ids or delay-ms")
        token = oauth_token(os.environ.get("BLIZZARD_CLIENT_ID", ""),
                            os.environ.get("BLIZZARD_CLIENT_SECRET", ""))
        snapshot = fetch_snapshot(ids[:args.max_ids], token,
                                  delay_seconds=args.delay_ms / 1000,
                                  include_media=args.include_media)
        _write(args.output, snapshot)
        result = audit(snapshot=snapshot)
        _write(args.report, result)
        print("Spell fetch results:", result["counts"])
        return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print("Spell-name audit failed:", type(exc).__name__, str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
