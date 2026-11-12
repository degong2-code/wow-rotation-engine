"""One-shot authorized source acquisition → HTML/WHML/tooltip coverage inventory.

Unlike rendering the guide, this prepares PRIVATE evidence for ChatGPT's
conditions-first editorial pass. A successful source snapshot NEVER certifies
current patch, complete dynamic states, or gameplay correctness.

Sources: accessible HTTPS URL, user-saved HTML, or user-saved complete-page ZIP.
No stealth, challenge bypass, cookie import, screenshots, API key, or account use.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from .source_page_acquire import (
    SourceAccessError, _validate_remote_url, _validate_html, acquisition_audit,
    capture_loaded_page, read_saved_html, read_saved_zip,
    select_analysis_html, write_private_snapshot,
)
from .source_structure import inspect_html
from .http_source_fetch import get_html

PIPELINE_SCHEMA = "source-acquisition-pipeline-v1"


def inspect_and_store(*, dom_html: str, output: Path, kind: str,
                      raw_html: str | None = None, mhtml: str | None = None,
                      metadata: dict | None = None, require_guide_body: bool = True,
                      expected_guide_sha256: str | None = None) -> dict:
    """Fail closed before writing snapshots if the requested guide is absent."""
    analysis, variant = select_analysis_html(dom_html, raw_html)
    _validate_html(analysis, ())
    static = inspect_html(analysis)
    audit = acquisition_audit(dom_html, origin=kind, source_html=raw_html,
                              mhtml=mhtml, extras=metadata)
    if require_guide_body and audit["guide_body_payloads"] < 1:
        raise SourceAccessError(
            "No literal guide-body found in acquired HTML; dynamic/non-WHML guide needs review"
        )
    payloads = [p for p in static["embedded_whml"]["payloads"]
                if p.get("target") == "guide-body"]
    hashes = [p["sha256"] for p in payloads]
    if expected_guide_sha256 is not None:
        if not re.fullmatch(r"[0-9a-f]{64}", expected_guide_sha256):
            raise ValueError("Expected guide body SHA-256 must be 64 lowercase hexadecimal characters")
        matches_baseline = expected_guide_sha256 in hashes
    else:
        matches_baseline = None
    options = sum(len(p.get("display_switches", {}).get("option_definitions", []))
                  for p in payloads)
    conditional = sum(p.get("display_switches", {}).get("conditional_occurrences", 0)
                      for p in payloads)
    named_definitions = sum(len(p.get("named_tooltip_bodies", []))
                            for p in payloads)
    references = sum(len(p.get("tooltip_references", [])) for p in payloads)
    missing_defs = sorted({
        name for p in payloads for name in p.get("unresolved_reference_names", [])
    })
    undeclared_options = sorted({
        name for p in payloads
        for name in p.get("display_switches", {}).get("unknown_conditional_option_ids", [])
    })
    flags = []
    if missing_defs:
        flags.append("tooltip_reference_without_definition")
    if undeclared_options:
        flags.append("conditional_option_without_definition")
    if static.get("candidate_lists_truncated"):
        flags.append("static_inventory_truncated")
    if static["embedded_whml"].get("unsupported_nonliteral_calls"):
        flags.append("nonliteral_script_not_decoded")
    for p in payloads:
        if p.get("nested_structure_issues"):
            flags.append("malformed_nested_markup")

    report = {
        "schema_version": PIPELINE_SCHEMA,
        "acquisition_kind": kind,
        "analysis_variant": variant,
        "analysis_html_sha256": hashlib.sha256(analysis.encode("utf-8")).hexdigest(),
        "analysis_html_characters": len(analysis),
        "guide_body_payloads": len(payloads),
        "guide_body_sha256s": hashes,
        "matches_known_baseline": matches_baseline,
        "source_change_review_required": matches_baseline is False,
        "guide_body_character_counts": [p["characters"] for p in payloads],
        "named_tooltip_definition_count": named_definitions,
        "tooltip_reference_count": references,
        "missing_named_tooltip_definitions": len(missing_defs),
        "option_definition_count": options,
        "conditional_display_count": conditional,
        "hidden_region_candidates": len(static["hidden_region_candidates"]),
        "visible_control_candidates": len(static["control_candidates"]),
        "issue_types": sorted(set(flags)),
        "static_source_obtained": True,
        "source_patch_verified": False,
        "real_site_completeness_verified": False,
        "gameplay_meaning_verified": False,
        "automatic_publish_allowed": False,
        "source_text_in_report": False,
    }
    write_private_snapshot(output, dom_html, audit, source_html=raw_html,
                           mhtml=mhtml)
    (output / "structure-audit.json").write_text(
        json.dumps(static, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "pipeline-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def require_authorized_navigation(url: str, expected_host: str) -> None:
    """Block main-frame redirect requests to other hosts before following them."""
    _validate_remote_url(url)
    if urlsplit(url).hostname.lower() != expected_host.lower():
        raise SourceAccessError("Cross-host navigation is not authorized")


def run_browser(url: str, output: Path, *, capture_mhtml: bool = False,
                capture_ui: bool = False, max_states: int = 24,
                max_depth: int = 3,
                expected_guide_sha256: str | None = None) -> dict:
    _validate_remote_url(url)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SourceAccessError("Playwright Chromium is unavailable") from exc
    original_host = urlsplit(url).hostname
    with sync_playwright() as driver:
        browser = driver.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            def authorize_route(route):
                if route.request.is_navigation_request():
                    try:
                        require_authorized_navigation(route.request.url, original_host)
                    except SourceAccessError:
                        route.abort()
                        return
                route.continue_()
            page.route("**/*", authorize_route)
            response = page.goto(url, wait_until="domcontentloaded", timeout=20000)
            require_authorized_navigation(page.url, original_host)
            dom, raw, mhtml = capture_loaded_page(
                page, response, required_markers=("WH.markup.printHtml",),
                capture_mhtml=capture_mhtml,
            )
            report = inspect_and_store(
                dom_html=dom, raw_html=raw, mhtml=mhtml, output=output,
                kind="browser_url", expected_guide_sha256=expected_guide_sha256,
            )
            if capture_ui:
                from .live_dom_capture import capture, summarize
                evidence = capture(page, max_states=max_states, max_depth=max_depth)
                (output / "private-ui-capture.json").write_text(
                    json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                ui_report = summarize(evidence)
                (output / "ui-audit.json").write_text(
                    json.dumps(ui_report, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                report["ui_states_observed"] = ui_report["observed_state_count"]
                report["ui_known_capture_gaps"] = ui_report["known_capture_gaps"]
                (output / "pipeline-audit.json").write_text(
                    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            return report
        finally:
            browser.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--url")
    src.add_argument("--http-url", help="One direct HTTPS GET; no browser, cookies or retries")
    src.add_argument("--saved-html", type=Path)
    src.add_argument("--saved-zip", type=Path)
    parser.add_argument("--allow-remote", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mhtml", action="store_true")
    parser.add_argument("--capture-ui", action="store_true")
    parser.add_argument("--expected-guide-sha256", help="Optional known-good WHML body SHA-256 for update comparison")
    parser.add_argument("--max-states", type=int, default=24)
    parser.add_argument("--max-depth", type=int, default=3)
    args = parser.parse_args(argv)
    if args.http_url:
        if not args.allow_remote:
            parser.error("Direct HTTP mode requires --allow-remote")
        if args.mhtml or args.capture_ui:
            parser.error("--mhtml/--capture-ui require a browser; HTTP mode does not execute UI")
        html = get_html(args.http_url)
        result = inspect_and_store(dom_html=html, output=args.output,
                                   kind="http_direct",
                                   expected_guide_sha256=args.expected_guide_sha256)
    elif args.url:
        if not args.allow_remote:
            parser.error("URL mode requires --allow-remote")
        result = run_browser(args.url, args.output,
                             capture_mhtml=args.mhtml,
                             capture_ui=args.capture_ui,
                             max_states=args.max_states,
                             max_depth=args.max_depth,
                             expected_guide_sha256=args.expected_guide_sha256)
    else:
        if args.mhtml or args.capture_ui:
            parser.error("--mhtml and --capture-ui require URL browser mode")
        if args.saved_zip:
            html, metadata = read_saved_zip(args.saved_zip)
        else:
            html, metadata = read_saved_html(args.saved_html)
        result = inspect_and_store(
            dom_html=html, output=args.output,
            kind=metadata["kind"], metadata=metadata,
            expected_guide_sha256=args.expected_guide_sha256,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
