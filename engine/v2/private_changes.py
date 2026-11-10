"""Build a minimal V11 patch from *reviewed private* per-spec JSON edits.

This does not call an AI or infer gameplay. An AI/editor may prepare a proposed
private detail JSON, but only modified rule or Advanced Tip fragments become
patch updates; unchanged original spell icons are preserved.

Example:
  python -m engine.v2.private_changes /private/base/rogue.json \
    /private/proposed/rogue.json --output /private/rogue.patch.json
  python -m engine.v2.patch_v11 /private/v11.html \
    /private/rogue.patch.json --output /private/updated-v11.html
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from .build import ROOT
from .patch_v11 import _safe_fragment

EDITABLE_RULE = {"condition_html", "condition_text_ko"}
EDITABLE_TIP = {"html", "text_ko"}


def _text(markup: str) -> str:
    if not isinstance(markup, str):
        raise ValueError("Edited HTML must be a string")
    return BeautifulSoup(markup, "html.parser").get_text(" ", strip=True)


def _outer(markup: str) -> Tag:
    if not isinstance(markup, str):
        raise ValueError("Advanced Tip HTML must be a string")
    soup = BeautifulSoup(markup, "html.parser")
    elements = [x for x in soup.contents if isinstance(x, Tag)]
    if len(elements) != 1 or any(
        isinstance(x, str) and x.strip() for x in soup.contents
    ):
        raise ValueError("An Advanced Tip must retain exactly one outer HTML tag")
    return elements[0]


def _match_unchanged(original: dict, proposed: dict, editable: set[str],
                     logical_id: str) -> None:
    if set(original) != set(proposed):
        raise ValueError(f"Unexpected fields for {logical_id}")
    if any(original[k] != proposed[k] for k in original if k not in editable):
        raise ValueError(f"Non-content identity or provenance changed: {logical_id}")


def make_patch(original: dict, proposed: dict) -> dict:
    """Compare two private detail snapshots of the SAME original V11 guide."""
    if not isinstance(original, dict) or not isinstance(proposed, dict):
        raise ValueError("Private detail documents must be JSON objects")
    if set(original) != set(proposed):
        raise ValueError("Private detail schema fields changed")
    meta_fields = {
        "schema_version", "guide_id", "baseline_v11_sha256",
        "public_storage_allowed",
    }
    if any(original.get(k) != proposed.get(k) for k in meta_fields):
        raise ValueError("Cannot change detail guide identity or V11 baseline")
    if original.get("schema_version") != "v11-private-detail-v1":
        raise ValueError("Unsupported detail schema")
    if original.get("public_storage_allowed") is not False:
        raise ValueError("Private details must not be public")
    baseline = original["baseline_v11_sha256"]
    if not isinstance(baseline, str) or len(baseline) != 64 or any(
        x not in "0123456789abcdef" for x in baseline
    ):
        raise ValueError("Invalid V11 baseline hash")

    updates = []
    seen = set()

    def append_update(kind: str, old: dict, new: dict, inner: str) -> None:
        logical_id = old["id"]
        if logical_id in seen:
            raise ValueError(f"Duplicate item ID: {logical_id}")
        seen.add(logical_id)
        if kind == "rule":
            original_html = old["condition_html"]
        else:
            original_html = _outer(old["html"]).decode_contents()
        if original_html == inner:
            return
        _safe_fragment(inner, inherited_html=original_html)
        source_hash = old["source_fragment_sha256"]
        if not isinstance(source_hash, str) or len(source_hash) != 64:
            raise ValueError(f"Missing original provenance: {logical_id}")
        updates.append({
            "kind": kind,
            "id": logical_id,
            "expected_source_sha256": source_hash,
            "new_inner_html": inner,
        })

    old_groups = original["rotation_groups"]
    new_groups = proposed["rotation_groups"]
    if len(old_groups) != len(new_groups):
        raise ValueError("Rotation group count changed")
    for og, ng in zip(old_groups, new_groups):
        if og["id"] != ng["id"] or set(og) != set(ng):
            raise ValueError("Rotation group identity changed")
        old_rules, new_rules = og["rules"], ng["rules"]
        if len(old_rules) != len(new_rules):
            raise ValueError("Rotation row count changed")
        for old, new in zip(old_rules, new_rules):
            _match_unchanged(old, new, EDITABLE_RULE, old["id"])
            if old["id"] != new["id"]:
                raise ValueError("Rotation rule ID changed")
            if new["condition_text_ko"] != _text(new["condition_html"]):
                raise ValueError(f"Condition text and HTML disagree: {old['id']}")
            append_update("rule", old, new, new["condition_html"])

    old_tips, new_tips = original["advanced_guidance"], proposed["advanced_guidance"]
    if len(old_tips) != len(new_tips):
        raise ValueError("Advanced Tip count changed")
    for old, new in zip(old_tips, new_tips):
        _match_unchanged(old, new, EDITABLE_TIP, old["id"])
        if old["id"] != new["id"]:
            raise ValueError("Advanced Tip ID changed")
        prior_node, next_node = _outer(old["html"]), _outer(new["html"])
        if (prior_node.name, prior_node.attrs) != (next_node.name, next_node.attrs):
            raise ValueError(f"Advanced Tip outer tag changed: {old['id']}")
        if new["text_ko"] != next_node.get_text(" ", strip=True):
            raise ValueError(f"Advanced Tip text and HTML disagree: {old['id']}")
        append_update("tip", old, new, next_node.decode_contents())
    if len(updates) > 256:
        raise ValueError("Too many V11 changes in one patch")
    return {
        "schema_version": "v11-private-patch-v1",
        "baseline_v11_sha256": baseline,
        "updates": updates,
    }


def create_private_patch(baseline_file: Path, proposed_file: Path, output_file: Path) -> dict:
    """Keep source, candidate, and generated patch outside the public repository."""
    repo_root = ROOT.resolve()
    for path in (baseline_file, proposed_file, output_file):
        resolved = Path(path).resolve()
        if resolved == repo_root or resolved.is_relative_to(repo_root):
            raise ValueError("Private V11 details and patches cannot be stored in GitHub")
    target = Path(output_file)
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite private patch: {target}")
    baseline = json.loads(Path(baseline_file).read_text(encoding="utf-8"))
    proposed = json.loads(Path(proposed_file).read_text(encoding="utf-8"))
    patch = make_patch(baseline, proposed)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(patch, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    return {
        "status": "PASS",
        "updated_count": len(patch["updates"]),
        "updated_ids": [entry["id"] for entry in patch["updates"]],
        "patch_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "private_output_only": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Draft minimal private V11 HTML patch")
    parser.add_argument("baseline_detail", type=Path)
    parser.add_argument("proposed_detail", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = create_private_patch(
        args.baseline_detail, args.proposed_detail, args.output
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
