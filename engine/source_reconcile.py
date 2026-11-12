"""Reconcile offline HTML/WHML candidates with previously captured source entries.

This is a *coverage gap locator*. It does not claim source authenticity,
full-site discovery, gameplay correctness, or final-HTML publish readiness.
Only structural IDs, short placement labels and body digests are reported.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from .source_coverage import SCHEMA as OBSERVATION_SCHEMA, assess as assess_observations
from .source_structure import SCHEMA as STRUCTURE_SCHEMA

SCHEMA = "source-structure-reconciliation-v1"
DECISIONS_SCHEMA = "source-reconciliation-decisions-v1"
REVIEWABLE = {"control", "panel", "tooltip", "whml_reference"}


def _error(message: str) -> ValueError:
    return ValueError("Invalid source reconciliation: " + message)


def _sha(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _candidate(category: str, locator: str, **metadata) -> dict:
    return {"id": category + ":" + locator, "kind": category, **metadata}


def discover(structure: dict) -> tuple[list[dict], list[str]]:
    """Build deterministic locators for a particular static HTML snapshot."""
    if not isinstance(structure, dict) or structure.get("schema_version") != STRUCTURE_SCHEMA:
        raise _error("invalid structure inventory")
    if structure.get("source_text_in_report") is not False:
        raise _error("structure inventory must not contain source text")
    for name in ("control_candidates", "hidden_region_candidates", "tooltip_trigger_candidates"):
        if not isinstance(structure.get(name), list):
            raise _error("missing structure candidates: " + name)

    result = []
    notes = []
    referenced_hidden_ids = set()
    for trigger in structure["tooltip_trigger_candidates"]:
        for desc in trigger["descriptions"]:
            if desc.get("status") == "reference_body" and desc.get("reference"):
                referenced_hidden_ids.add(desc["reference"].removeprefix("#"))

    for control in structure["control_candidates"]:
        # Pure buttons can be site navigation or unrelated UI; do not silently
        # treat every decorative button as a decision branch.
        if control["type"] == "button":
            continue
        result.append(_candidate("control", str(control["element"]),
                                 subtype=control["type"], dom_id=control.get("id"),
                                 section=control.get("section"), body_digest=None))
    for region in structure["hidden_region_candidates"]:
        if region.get("id") and region["id"] in referenced_hidden_ids:
            # This hidden node supplies a named tooltip already listed below.
            # Avoid demanding a second copy of the same text.
            notes.append("Linked tooltip body panel not double-counted: element "
                         + str(region["element"]))
            continue
        result.append(_candidate("panel", str(region["element"]),
                                 subtype=region["tag"], dom_id=region.get("id"),
                                 section=region.get("section"), body_digest=region.get("body")))
    for trigger in structure["tooltip_trigger_candidates"]:
        for i, desc in enumerate(trigger["descriptions"]):
            result.append(_candidate("tooltip", str(trigger["element"]) + ":" + str(i),
                                     subtype=desc.get("attribute"), dom_id=trigger.get("id"),
                                     section=trigger.get("section"),
                                     table_row=trigger.get("table_row"),
                                     reference=desc.get("reference"),
                                     static_status=desc.get("status"),
                                     body_digest=desc.get("body")))

    embedded = structure.get("embedded_whml", {})
    if embedded.get("unsupported_nonliteral_calls", 0):
        notes.append("Embedded nonliteral script content requires separate investigation")
    for i, payload in enumerate(embedded.get("payloads", [])):
        target = payload.get("target")
        if target != "guide-body":
            notes.append("Non-guide WHML target not assumed relevant: payload " + str(i))
            continue
        for j, ref in enumerate(payload.get("tooltip_references", [])):
            result.append(_candidate("whml_reference", str(i) + ":" + str(j),
                                     subtype=ref["attribute"], section="guide-body",
                                     dom_id=None, name=ref["name"],
                                     static_status=("resolved_name" if ref["name"] in
                                         payload.get("named_tooltip_definitions", [])
                                         else "unresolved_name"),
                                     body_digest=None))
        if payload.get("unresolved_reference_names"):
            notes.append("Some guide-body WHML tooltip definitions were not found")
        if payload.get("duplicate_definition_names"):
            notes.append("Duplicate named WHML tooltip definitions require review")
    if structure.get("candidate_lists_truncated"):
        notes.append("Structure inventory hit a candidate limit; further items unseen")
    if structure.get("duplicate_ids"):
        notes.append("Duplicate DOM IDs may make tooltip/panel associations ambiguous")
    ids = [x["id"] for x in result]
    if len(ids) != len(set(ids)):
        raise _error("duplicate generated candidate IDs")
    return result, notes


def reconcile(structure: dict, observations: dict, decisions: dict | None = None) -> dict:
    if not isinstance(observations, dict) or observations.get("schema_version") != OBSERVATION_SCHEMA:
        raise _error("invalid captured observation ledger")
    coverage = assess_observations(observations)
    candidates, notes = discover(structure)
    by_id = {c["id"]: c for c in candidates}
    linked: dict[str, dict] = {}
    invalid_mappings = []
    digest_only = []

    def link(candidate_id: str, evidence: str, kind: str, body: str | None):
        candidate = by_id.get(candidate_id)
        if candidate is None:
            invalid_mappings.append({"id": candidate_id, "issue": "unknown_candidate"})
            return
        if candidate["kind"] in {"tooltip", "whml_reference"} and kind != "tooltip":
            invalid_mappings.append({"id": candidate_id, "issue": "tip_must_link_to_tooltip"})
            return
        if candidate["kind"] == "control" and kind != "choice":
            invalid_mappings.append({"id": candidate_id, "issue": "control_must_link_to_choice"})
            return
        if candidate["kind"] != "control" and (not isinstance(body, str) or not body.strip()):
            invalid_mappings.append({"id": candidate_id, "issue": "missing_recorded_body"})
            return
        if candidate_id in linked:
            invalid_mappings.append({"id": candidate_id, "issue": "duplicate_claim"})
            return
        digest = candidate.get("body_digest")
        same = (bool(digest and digest.get("characters"))
                and _sha(body or "") == digest.get("sha256"))
        linked[candidate_id] = {"evidence": evidence, "method": "explicit",
                                "exact_text_digest_match": same}

    for si, state in enumerate(observations["states"]):
        for entry in state["entries"]:
            ids = entry.get("source_candidate_ids", [])
            if not isinstance(ids, list):
                raise _error("entry source_candidate_ids must be a list")
            for cid in ids:
                if not isinstance(cid, str):
                    raise _error("entry source_candidate_ids must contain strings")
                link(cid, "state=" + str(si) + "/entry=" + entry["id"],
                     entry["kind"], entry.get("text"))
        for choice in state["choices"]:
            ids = choice.get("source_candidate_ids", [])
            if not isinstance(ids, list):
                raise _error("choice source_candidate_ids must be a list")
            for cid in ids:
                if not isinstance(cid, str):
                    raise _error("choice source_candidate_ids must contain strings")
                link(cid, "state=" + str(si) + "/control=" + choice["control"], "choice", None)

    # Safe automatic equality, not guessed adjacency: only exact body digest
    # and a unique candidate are eligible. A paraphrase or partial quote will
    # not automatically become verified source content.
    for si, state in enumerate(observations["states"]):
        for entry in state["entries"]:
            body = entry.get("text")
            if entry.get("source_candidate_ids"):
                continue
            if not isinstance(body, str) or not body.strip():
                continue
            h = _sha(body)
            possible = [c for c in candidates if c["id"] not in linked
                        and c["kind"] in {"tooltip", "panel"}
                        and c.get("body_digest") and c["body_digest"].get("sha256") == h
                        and (c["kind"] != "tooltip" or entry["kind"] == "tooltip")]
            if len(possible) == 1:
                cid = possible[0]["id"]
                linked[cid] = {"evidence": "state=" + str(si) + "/entry=" + entry["id"],
                               "method": "exact_body_digest", "exact_text_digest_match": True}
                digest_only.append(cid)

    exclusions = {}
    if decisions is not None:
        if not isinstance(decisions, dict) or decisions.get("schema_version") != DECISIONS_SCHEMA:
            raise _error("invalid reviewer decision schema")
        items = decisions.get("not_relevant")
        if not isinstance(items, list):
            raise _error("not_relevant must be an array")
        for item in items:
            if not isinstance(item, dict) or set(item) != {"candidate_id", "reason"}:
                raise _error("review item must contain candidate_id and reason")
            cid, reason = item["candidate_id"], item["reason"]
            if not isinstance(cid, str) or cid not in by_id:
                raise _error("review decision references unknown candidate")
            if not isinstance(reason, str) or len(reason.strip()) < 8:
                raise _error("review reason is missing or too short")
            if cid in exclusions or cid in linked:
                raise _error("duplicate/existing candidate review decision")
            exclusions[cid] = True

    pending = []
    static_unresolved = []
    for candidate in candidates:
        cid = candidate["id"]
        if candidate.get("static_status") in {"unresolved_name", "empty_body",
                                              "unresolved_reference", "body_not_found_in_static_html"}:
            static_unresolved.append(cid)
        if cid not in linked and cid not in exclusions:
            pending.append({"id": cid, "kind": candidate["kind"],
                            "subtype": candidate.get("subtype"),
                            "section": candidate.get("section")})
    warnings = notes + coverage["warnings"]
    if structure.get("live_ui_completeness_verified") is not False:
        warnings.append("Unexpected structure completeness claim; not trusted")
    warnings.append("Structural snapshot provenance is not independently authenticated")
    if not observations.get("states"):
        raise _error("empty observations")
    return {
        "schema_version": SCHEMA,
        "structure_candidate_count": len(candidates),
        "mapped_candidate_count": len(linked),
        "exact_digest_matched_count": sum(bool(x["exact_text_digest_match"]) for x in linked.values()),
        "auto_matched_candidate_ids": sorted(digest_only),
        "review_exclusion_count": len(exclusions),
        "unmapped_candidates": pending,
        "static_body_unresolved_ids": sorted(set(static_unresolved)),
        "invalid_mappings": invalid_mappings,
        "declared_observation_gaps": coverage["gaps"],
        "warnings": warnings,
        "candidate_comparison_complete": not pending and not invalid_mappings
            and not coverage["gaps"] and not static_unresolved and
            not structure.get("candidate_lists_truncated", False),
        "real_site_completeness_verified": False,
        "gameplay_meaning_verified": False,
        "source_text_in_report": False,
        "automatic_publish_allowed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structure", type=Path, required=True)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--decisions", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    structure = json.loads(args.structure.read_text(encoding="utf-8"))
    observations = json.loads(args.observations.read_text(encoding="utf-8"))
    decisions = json.loads(args.decisions.read_text(encoding="utf-8")) if args.decisions else None
    result = reconcile(structure, observations, decisions)
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
