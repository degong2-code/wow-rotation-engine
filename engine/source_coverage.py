"""Audit declared source states for any specialization, without fetching web pages.

A report never reproduces source text and never authenticates completeness of
the real website, gameplay logic, or an actual tooltip-to-row association.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA = "source-coverage-observation-v1"
REPORT_SCHEMA = "source-coverage-report-v1"
KINDS = {"rendered_ui", "live_dom", "page_html", "search_index", "user_supplied"}


def _invalid(reason: str) -> ValueError:
    return ValueError("Invalid coverage observation: " + reason)


def _label(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 120:
        raise _invalid(name + " must be a nonempty string (max 120 characters)")
    return value


def _path(value: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, list) or len(value) > 20:
        raise _invalid("path must be a list of at most 20 selections")
    parts = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"control", "option"}:
            raise _invalid("path selection requires control and option")
        parts.append((_label(item["control"], "control"), _label(item["option"], "option")))
    if len({key for key, _ in parts}) != len(parts):
        raise _invalid("same control may not occur twice in a path")
    return tuple(parts)


def _display(path: tuple[tuple[str, str], ...]) -> str:
    return " / ".join(k + "=" + v for k, v in path) or "root"


def assess(document: dict) -> dict:
    """Review user-declared coverage, not undiscovered site content."""
    if not isinstance(document, dict) or document.get("schema_version") != SCHEMA:
        raise _invalid("unexpected schema")
    guide = document.get("guide")
    if not isinstance(guide, dict):
        raise _invalid("guide is required")
    for field in ("specialization", "source_url", "patch", "revision"):
        _label(guide.get(field), "guide." + field)

    accesses = document.get("accesses")
    if not isinstance(accesses, list) or not accesses:
        raise _invalid("accesses must be a nonempty list")
    sources = {}
    for source in accesses:
        if not isinstance(source, dict):
            raise _invalid("access must be an object")
        ident = _label(source.get("id"), "access id")
        if ident in sources:
            raise _invalid("duplicate access id")
        if source.get("kind") not in KINDS:
            raise _invalid("invalid access kind")
        for field in ("source_url", "patch", "revision"):
            _label(source.get(field), "access." + field)
        sources[ident] = source

    observed = document.get("states")
    if not isinstance(observed, list) or not observed or len(observed) > 1000:
        raise _invalid("states must be a nonempty bounded list")
    states = {}
    for state in observed:
        if not isinstance(state, dict):
            raise _invalid("state must be an object")
        path = _path(state.get("path"))
        if path in states:
            raise _invalid("duplicate state path")
        if state.get("access_id") not in sources:
            raise _invalid("unknown access id")
        if not isinstance(state.get("inventory_checked"), bool):
            raise _invalid("inventory_checked must be boolean")
        choices = state.get("choices")
        entries = state.get("entries")
        if not isinstance(choices, list) or not isinstance(entries, list):
            raise _invalid("choices and entries must be lists")
        used_controls = set()
        decision_count = 0
        for choice in choices:
            if not isinstance(choice, dict):
                raise _invalid("choice must be an object")
            control = _label(choice.get("control"), "choice.control")
            if control in used_controls or control in {k for k, _ in path}:
                raise _invalid("duplicate/already-selected control")
            used_controls.add(control)
            if choice.get("role") not in ("decision", "illustrative"):
                raise _invalid("choice role must be decision or illustrative")
            options = choice.get("options")
            if not isinstance(options, list) or not options or len(options) > 100:
                raise _invalid("choice options must be nonempty and bounded")
            named_options = [_label(v, "option") for v in options]
            if len(set(named_options)) != len(named_options):
                raise _invalid("duplicate choice option")
            decision_count += choice["role"] == "decision"
        if decision_count > 1:
            raise _invalid("one decision control per state; re-discover other controls below it")
        used_entries = set()
        for item in entries:
            if not isinstance(item, dict):
                raise _invalid("entry must be an object")
            ident = _label(item.get("id"), "entry id")
            _label(item.get("kind"), "entry kind")
            if ident in used_entries:
                raise _invalid("duplicate entry id")
            used_entries.add(ident)
            if "text" in item and item["text"] is not None and not isinstance(item["text"], str):
                raise _invalid("entry text must be string or null")
            pos = item.get("position")
            if pos is not None and (not isinstance(pos, dict) or not all(
                    isinstance(k, str) and isinstance(v, str) and v.strip()
                    for k, v in pos.items())):
                raise _invalid("position must contain nonempty text hints")
        states[path] = state
    if () not in states:
        raise _invalid("root state is required")

    gaps = []
    warnings = []
    unknown_positions = []
    total_entries = total_tips = 0
    for path, state in states.items():
        where = _display(path)
        source = sources[state["access_id"]]
        if any(source[k] != guide[k] for k in ("source_url", "patch", "revision")):
            gaps.append({"type": "source_version_conflict", "state": where})
        if not state["inventory_checked"]:
            gaps.append({"type": "inventory_not_checked", "state": where})
        decisions = [c for c in state["choices"] if c["role"] == "decision"]
        if not decisions and not state["entries"]:
            gaps.append({"type": "empty_terminal_state", "state": where})
        for c in decisions:
            for option in c["options"]:
                child = path + ((c["control"], option),)
                if child not in states:
                    gaps.append({"type": "unvisited_choice", "state": _display(child)})
        for entry in state["entries"]:
            total_entries += 1
            if not isinstance(entry.get("text"), str) or not entry["text"].strip():
                gaps.append({"type": "missing_content", "state": where, "entry_id": entry["id"]})
            if entry["kind"] == "tooltip":
                total_tips += 1
                if not entry.get("position"):
                    unknown_positions.append({"state": where, "entry_id": entry["id"]})
    for path in states:
        if not path:
            continue
        parent = states.get(path[:-1])
        if parent is None or not any(c["role"] == "decision"
            and c["control"] == path[-1][0] and path[-1][1] in c["options"]
            for c in parent["choices"]):
            gaps.append({"type": "orphan_state", "state": _display(path)})

    if unknown_positions:
        warnings.append("Tooltip location unknown: meaning can be analyzed without exact row association.")
    if any(sources[s["access_id"]]["kind"] in {"search_index", "user_supplied"}
           for s in states.values()):
        warnings.append("Indirect source: indexed text does not prove exhaustive live UI coverage.")
    if not gaps:
        warnings.append("Only declared states are covered: unknown live-site states may exist.")

    return {
        "schema_version": REPORT_SCHEMA,
        "guide": {k: guide[k] for k in ("specialization", "source_url", "patch", "revision")},
        "declared_states": len(states),
        "declared_entries": total_entries,
        "declared_tooltips": total_tips,
        "gaps": gaps,
        "tooltip_positions_unknown": unknown_positions,
        "warnings": warnings,
        "declared_coverage_candidate": not gaps,
        "real_site_completeness_verified": False,
        "gameplay_meaning_verified": False,
        "source_text_in_report": False,
        "automatic_publish_allowed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-declared-complete", action="store_true")
    args = parser.parse_args(argv)
    report = assess(json.loads(args.input.read_text(encoding="utf-8")))
    result = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    return 0 if (not args.require_declared_complete or report["declared_coverage_candidate"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
