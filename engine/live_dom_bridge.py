"""Convert private runtime DOM evidence into a fail-closed source_coverage draft.

This bridge records what was visibly observed, NOT what must be present in a
complete WoW guide. UI action paths are capture navigation, not gameplay
branches. The private draft can contain source text and must never be uploaded
to a public repository or CI artifact.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path

from .source_coverage import SCHEMA, assess
from .live_dom_capture import summarize

INLINE_TEXT = ("title", "data-hint-body", "data-tippy-content",
               "data-tooltip-content", "data-bs-title")


def _signature(path: list) -> str:
    return json.dumps(path, sort_keys=True, ensure_ascii=False)


def _token(action: dict) -> str:
    return "action-" + sha256(_signature([action]).encode("utf-8")).hexdigest()[:20]


def _converted_path(path: list[dict]) -> list[dict]:
    return [{"control": "observed-ui-depth-" + str(i), "option": _token(step)}
            for i, step in enumerate(path)]


def _position(trigger: dict, state_index: int) -> dict:
    position = {"observed_state": str(state_index)}
    if trigger.get("row_id"):
        position["row_id"] = str(trigger["row_id"])[:120]
    if trigger.get("near"):
        position["near"] = str(trigger["near"])[:120]
    return position


def _entries(state: dict, state_index: int) -> list[dict]:
    observed = state["observation"]
    entries = [
        {"id": "visible_state_body", "kind": "visible_body",
         "text": observed.get("body"), "position": {"observed_state": str(state_index)}}
    ]
    triggers = observed.get("tooltip_triggers", [])
    hover_by_index = {x["trigger_index"]: x for x in state.get("hover_results", [])}
    for trigger in triggers:
        ident = "trigger-" + str(trigger["index"])
        pos = _position(trigger, state_index)
        added = 0
        for name in INLINE_TEXT:
            if name not in trigger.get("attributes", {}):
                continue
            entries.append({"id": ident + "-inline-" + name, "kind": "tooltip",
                            "text": trigger["attributes"][name] or None, "position": pos})
            added += 1
        for name, refs in trigger.get("references", {}).items():
            for i, ref in enumerate(refs):
                entries.append({"id": ident + "-ref-" + name + "-" + str(i),
                                "kind": "tooltip",
                                "text": ref.get("body") or None, "position": pos})
                added += 1
        hover = hover_by_index.get(trigger["index"])
        if hover:
            for j, body in enumerate(hover.get("dynamic_tooltips", [])):
                entries.append({"id": ident + "-hover-" + str(j),
                                "kind": "tooltip", "text": body or None,
                                "position": pos})
                added += 1
            if hover.get("error_type"):
                entries.append({"id": ident + "-hover-error", "kind": "tooltip",
                                "text": None, "position": pos})
                added += 1
        else:
            entries.append({"id": ident + "-not-hovered", "kind": "tooltip",
                            "text": None, "position": pos})
            added += 1
        if not added:
            entries.append({"id": ident + "-unresolved", "kind": "tooltip",
                            "text": None, "position": pos})
    total = observed.get("tooltip_trigger_total", len(triggers))
    if total > len(triggers):
        entries.append({"id": "tooltip-trigger-list-truncated", "kind": "tooltip",
                        "text": None, "position": {"observed_state": str(state_index)}})
    return entries


def to_coverage_draft(capture: dict, specialization: str,
                      patch: str, revision: str) -> dict:
    if not isinstance(capture, dict) or capture.get("schema_version") != "live-dom-private-observation-v1":
        raise ValueError("Expected private live DOM capture, not a public audit")
    if not isinstance(capture.get("states"), list):
        raise ValueError("Capture has no states array")
    url = capture.get("source_url")
    if not isinstance(url, str) or not url:
        raise ValueError("Capture source URL absent")

    captured = {_signature(s["path"]): s for s in capture["states"]}
    if len(captured) != len(capture["states"]):
        raise ValueError("Duplicate recorded DOM state path")
    pending = capture.get("pending_paths", [])
    if not isinstance(pending, list):
        raise ValueError("Invalid pending state paths")

    child_actions = defaultdict(dict)
    for state in capture["states"]:
        path = state["path"]
        if path:
            child_actions[_signature(path[:-1])][_token(path[-1])] = path[-1]
    for path in pending:
        if path:
            child_actions[_signature(path[:-1])][_token(path[-1])] = path[-1]

    result_states = []
    observed_root = captured.get(_signature([]))
    if observed_root is None:
        # A failed navigation must not become a seemingly complete guide.
        result_states.append({"path": [], "access_id": "capture", "inventory_checked": False,
                              "choices": [], "entries": [
                                  {"id": "failed-root-capture", "kind": "visible_body", "text": None}
                              ]})
    for i, state in enumerate(capture["states"]):
        raw_path = state["path"]
        children = child_actions.get(_signature(raw_path), {})
        choices = []
        if children:
            choices = [{"control": "observed-ui-depth-" + str(len(raw_path)),
                        "role": "decision", "options": sorted(children)}]
        result_states.append({
            "path": _converted_path(raw_path),
            "access_id": "capture",
            # A DOM snapshot cannot certify all site states/tooltip bodies.
            "inventory_checked": False,
            "choices": choices,
            "entries": _entries(state, i),
        })
    # Older private captures may provide a pending count but not paths.
    # Do not invent a visited branch: retain an explicit unvisited root option.
    missing_pending = max(0, capture.get("pending_state_count", 0) - len(pending))
    if missing_pending and result_states:
        root_state = next(s for s in result_states if not s["path"])
        if not root_state["choices"]:
            root_state["choices"] = [
                {"control": "observed-ui-depth-0", "role": "decision", "options": []}
            ]
        root_state["choices"][0]["options"].append("undisclosed-pending-branch")
    # The source patch/revision is a reviewer declaration, not automatically
    # discovered from browser content.
    guide = {"specialization": specialization, "source_url": url,
             "patch": patch, "revision": revision}
    ledger = {"schema_version": SCHEMA, "guide": guide,
              "accesses": [{"id": "capture", "kind": "live_dom",
                            "source_url": url, "patch": patch, "revision": revision,
                            "html_sha256": capture.get("source_sha256")}],
              "states": result_states}
    assess(ledger)
    return ledger


def public_audit(capture: dict, ledger: dict) -> dict:
    coverage = assess(ledger)
    counts = Counter(g["type"] for g in coverage["gaps"])
    return {
        "schema_version": "live-dom-coverage-bridge-report-v1",
        "capture": summarize(capture),
        "observation_state_count": len(ledger["states"]),
        "observation_entry_count": coverage["declared_entries"],
        "observation_tip_count": coverage["declared_tooltips"],
        "declared_gap_types": dict(sorted(counts.items())),
        "declared_coverage_candidate": coverage["declared_coverage_candidate"],
        "source_text_in_report": False,
        "real_site_completeness_verified": False,
        "gameplay_meaning_verified": False,
        "automatic_publish_allowed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--specialization", required=True)
    parser.add_argument("--patch", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--private-ledger", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    args = parser.parse_args(argv)
    capture = json.loads(args.capture.read_text(encoding="utf-8"))
    ledger = to_coverage_draft(capture, args.specialization, args.patch, args.revision)
    metadata = public_audit(capture, ledger)
    args.private_ledger.parent.mkdir(parents=True, exist_ok=True)
    args.private_ledger.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n",
                                   encoding="utf-8")
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
