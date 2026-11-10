"""Tiny public bootstrap. No scraper, no LLM calls, no gameplay claims."""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

from .conditions import evaluate


def load(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate(data: dict) -> list[str]:
    errors = []
    if not isinstance(data, dict):
        return ["Catalog must be an object"]
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    specs = data.get("specs")
    if not isinstance(specs, list) or not specs:
        return errors + ["specs must be a nonempty list"]
    seen_specs = set()
    for spec in specs:
        if not isinstance(spec, dict):
            errors.append("spec entry must be an object")
            continue
        sid = spec.get("id")
        if not isinstance(sid, str) or not sid or sid in seen_specs:
            errors.append(f"Invalid or duplicate spec id: {sid}")
        seen_specs.add(sid)
        for label in ("name_ko", "hero"):
            if not isinstance(spec.get(label), str) or not spec[label]:
                errors.append(f"{sid}: missing {label}")
        rules = spec.get("rules")
        if not isinstance(rules, list):
            errors.append(f"{sid}: rules must be a list")
            continue
        seen_rules = set()
        for rule in rules:
            if not isinstance(rule, dict):
                errors.append(f"{sid}: rule must be an object")
                continue
            rid = rule.get("id")
            if not isinstance(rid, str) or not rid or rid in seen_rules:
                errors.append(f"{sid}: invalid or duplicate rule id: {rid}")
            seen_rules.add(rid)
            if type(rule.get("priority")) is not int or rule["priority"] < 1:
                errors.append(f"{sid}/{rid}: priority must be positive integer")
            if type(rule.get("spell_id")) is not int or rule["spell_id"] <= 0:
                errors.append(f"{sid}/{rid}: positive spell_id is required")
            if not isinstance(rule.get("name_ko"), str) or not rule["name_ko"]:
                errors.append(f"{sid}/{rid}: name_ko is required")
            if not isinstance(rule.get("notes_ko"), str):
                errors.append(f"{sid}/{rid}: notes_ko is required")
            try:
                evaluate(rule.get("when"), {})
            except (TypeError, ValueError) as e:
                errors.append(f"{sid}/{rid}: invalid condition: {e}")
            evidence = rule.get("evidence")
            if not isinstance(evidence, dict) or evidence.get("state") not in {"synthetic", "unverified", "source_checked"}:
                errors.append(f"{sid}/{rid}: invalid evidence state")
            elif evidence["state"] != "synthetic":
                if not isinstance(evidence.get("source_url"), str) or not evidence["source_url"].startswith("https://"):
                    errors.append(f"{sid}/{rid}: missing HTTPS source")
                if not isinstance(evidence.get("source_sha256"), str) or len(evidence["source_sha256"]) != 64:
                    errors.append(f"{sid}/{rid}: invalid source SHA")
            review = rule.get("review")
            if review not in {"pending", "approved"}:
                errors.append(f"{sid}/{rid}: invalid review")
            if review == "approved" and evidence and evidence.get("state") != "source_checked":
                errors.append(f"{sid}/{rid}: cannot approve without checked source")
    return errors


def build(data: dict, allow_demo: bool = False) -> str:
    errors = validate(data)
    if errors:
        raise ValueError("Invalid catalog: " + "; ".join(errors))
    rules = [r for s in data["specs"] for r in s["rules"]]
    if any(r["evidence"]["state"] == "synthetic" for r in rules):
        if not allow_demo:
            raise ValueError("Synthetic fixtures must not be published as real guides")
    elif any(r["review"] != "approved" or r["evidence"]["state"] != "source_checked" for r in rules):
        raise ValueError("Unreviewed rules cannot be published")
    q = html.escape
    pieces = [
        "<!doctype html><html lang='ko'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>WoW Rotation Engine — 검증 파이프라인 데모</title>",
        "<style>body{background:#1d1f24;color:#f4f1eb;font:16px/1.8 system-ui,"
        "'Malgun Gothic',sans-serif;max-width:850px;margin:40px auto;padding:0 20px}"
        "h1,h2{color:#e8b34b}section{border-top:1px solid #49443d;margin-top:25px}"
        "li{margin:8px 0}small{color:#b4b2b5}</style></head><body>",
        "<h1>WoW Rotation Engine — 데이터 파이프라인 검증</h1>",
    ]
    if allow_demo:
        pieces.append("<p><strong>합성 데이터 데모. 실제 게임 공략이 아닙니다.</strong></p>")
    for spec in data["specs"]:
        pieces.append(f"<section><h2>{q(spec['name_ko'])} · {q(spec['hero'])}</h2><ol>")
        for rule in sorted(spec["rules"], key=lambda r: (r["priority"], r["id"])):
            pieces.append(f"<li><strong>{q(rule['name_ko'])}</strong> "
                          f"<small>(spell_id: {rule['spell_id']})</small> "
                          f"— {q(rule['notes_ko'])}</li>")
        pieces.append("</ol></section>")
    pieces.append("</body></html>\n")
    return "".join(pieces)


def canonical_sha(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False,
        sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
