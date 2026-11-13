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
from .spec_source_resolver import Specialization, resolve_specialization
from .guide_identity import inspect_identity
from .source_editorial_packet import packet_from_html
from .source_scoped_evidence import scoped_from_packet, scoped_metadata, unbound_selector_impact

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

    # Prepare private source evidence before writing any public-safe audit.
    private_packet = packet_from_html(analysis) if payloads else None
    scoped_packet = scoped_from_packet(private_packet) if private_packet is not None else None
    scope_audit = scoped_metadata(scoped_packet) if scoped_packet is not None else None
    selector_impact = (
        unbound_selector_impact(private_packet, scoped_packet)
        if scoped_packet is not None else None
    )
    if selector_impact and selector_impact["ordered_action_review_required"]:
        flags.append("unbound_selector_ordered_action_candidate")
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
        "source_selector_impact": selector_impact,
        "source_selector_references_resolved": bool(
            selector_impact and selector_impact["source_selector_references_resolved"]
        ),
        "source_selector_action_review_required": bool(
            selector_impact and selector_impact["ordered_action_review_required"]
        ),
        "static_source_obtained": True,
        "private_editorial_packet_written": private_packet is not None,
        "private_scoped_evidence_written": scoped_packet is not None,
        "source_row_candidates": scope_audit["source_row_candidates"] if scope_audit else 0,
        "source_rows_with_mixed_visibility": scope_audit["rows_with_mixed_visibility"] if scope_audit else 0,
        "source_conditions_evidence_accounted": bool(
            scope_audit and scope_audit["source_condition_expression_count"] == conditional
            and scope_audit["unassigned_conditional_expressions"] == 0
        ),
        "source_conditions_unassigned": scope_audit["unassigned_conditional_expressions"] if scope_audit else 0,
        "source_scope_structure_issue_types": scope_audit["structure_issue_types"] if scope_audit else {},
        "source_scope_requires_review": bool(
            scope_audit and (scope_audit["rows_with_mixed_visibility"]
                             or scope_audit["structure_issue_types"]
                             or scope_audit["unassigned_conditional_expressions"])
        ),
        "source_patch_verified": False,
        "real_site_completeness_verified": False,
        "gameplay_meaning_verified": False,
        "automatic_publish_allowed": False,
        "source_text_in_report": False,
    }
    write_private_snapshot(output, dom_html, audit, source_html=raw_html,
                           mhtml=mhtml)
    if private_packet is not None:
        (output / "editorial-evidence-private.json").write_text(
            json.dumps(private_packet, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if scoped_packet is not None:
        (output / "scoped-evidence-private.json").write_text(
            json.dumps(scoped_packet, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (output / "scoped-audit.json").write_text(
            json.dumps(scope_audit, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    (output / "structure-audit.json").write_text(
        json.dumps(static, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "pipeline-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report



def run_specialization(query: str, output: Path, *,
                       expected_patch: str | None = None,
                       min_updated: str | None = None,
                       expected_guide_sha256: str | None = None,
                       fetch_html=None) -> dict:
    """Resolve name to exact guide, verify identity, and audit without a browser.

    Source metadata is not evidence of the globally latest game build: patch
    release/currentness still requires independent ChatGPT editorial checking.
    """
    spec = resolve_specialization(query)
    fetch = fetch_html if fetch_html is not None else get_html
    html = fetch(spec.guide_url)
    identity = inspect_identity(
        html, spec, expected_patch=expected_patch, min_updated=min_updated,
    )
    report = inspect_and_store(
        dom_html=html, output=output, kind="specialization_http",
        expected_guide_sha256=expected_guide_sha256,
    )
    report.update(identity)
    # These are route/identity metadata, not proprietary source passages.
    report["resolved_guide_url"] = spec.guide_url
    report["source_patch_verified"] = False
    report["editorial_review_required"] = True
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
                expected_guide_sha256: str | None = None,
                specialization: Specialization | None = None,
                expected_patch: str | None = None,
                min_updated: str | None = None) -> dict:
    """Authorized browser acquisition; optionally bind identity to a spec.

    Patch identity is checked on the ACTUAL returned source before private
    source material is persisted. This never assumes that an indexed search
    result and the directly opened page serve the same guide revision.
    """
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
            identity = None
            if specialization is not None:
                # The user sees the rendered DOM. Validate it independently,
                # not just the richer raw WHML response that may be stale.
                identity = inspect_identity(
                    dom, specialization,
                    expected_patch=expected_patch, min_updated=min_updated,
                )
                if raw is not None:
                    response_identity = inspect_identity(
                        raw, specialization,
                        expected_patch=expected_patch, min_updated=min_updated,
                    )
                    if (
                        identity["visible_patch_candidates"]
                        and response_identity["visible_patch_candidates"]
                        and not (
                            set(identity["visible_patch_candidates"])
                            & set(response_identity["visible_patch_candidates"])
                        )
                    ) or (
                        identity["observed_guide_update_date"] is not None
                        and response_identity["observed_guide_update_date"] is not None
                        and identity["observed_guide_update_date"]
                        != response_identity["observed_guide_update_date"]
                    ):
                        raise SourceAccessError(
                            "Browser DOM and network response disagree on guide revision"
                        )
            report = inspect_and_store(
                dom_html=dom, raw_html=raw, mhtml=mhtml, output=output,
                kind="specialization_browser" if specialization else "browser_url",
                expected_guide_sha256=expected_guide_sha256,
            )
            if identity is not None:
                report.update(identity)
                report["resolved_guide_url"] = specialization.guide_url
                report["editorial_review_required"] = True
                # A visible patch/date is a necessary gate, never an independent
                # confirmation that all hidden guide choices are current.
                report["source_patch_verified"] = False
            if capture_ui:
                from .live_dom_capture import capture, summarize
                # Each state reloading the page must still identify the
                # requested guide revision. Do not mix a current initial WHML
                # packet with a stale dynamic option state after reload.
                def validate_captured_state(current_page):
                    if specialization is not None:
                        inspect_identity(
                            current_page.content(), specialization,
                            expected_patch=expected_patch,
                            min_updated=min_updated,
                        )
                evidence = capture(
                    page, max_states=max_states, max_depth=max_depth,
                    validate_state=validate_captured_state if specialization else None,
                )
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
                report["ui_capture_report_written"] = True
            # Keep acquisition, identity and UI coverage in ONE final report.
            (output / "pipeline-audit.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return report
        finally:
            browser.close()



def run_specialization_with_ui(query: str, output: Path, *,
                               capture_ui: bool = True,
                               capture_mhtml: bool = False,
                               max_states: int = 24, max_depth: int = 3,
                               expected_patch: str | None = None,
                               min_updated: str | None = None,
                               expected_guide_sha256: str | None = None) -> dict:
    """HTTP-first evidence, optional *revision-matched* browser enrichment.

    The guide source is obtained once via a normal HTTPS GET, before any
    browser navigation. A blocked browser must not destroy an accessible,
    version-checked source; conversely, a stale/mismatched browser may never
    supply guide conditions or UI observations to that source.
    """
    from tempfile import TemporaryDirectory
    from shutil import copyfile

    spec = resolve_specialization(query)
    report = run_specialization(
        query, output, expected_patch=expected_patch,
        min_updated=min_updated,
        expected_guide_sha256=expected_guide_sha256,
    )
    report["ui_capture_status"] = "not_observed"
    report["ui_known_capture_gaps"] = True
    report["ui_states_observed"] = 0
    report["browser_enrichment_attempted"] = bool(capture_ui or capture_mhtml)
    report["browser_enrichment_accepted"] = False
    report["real_site_completeness_verified"] = False
    report["gameplay_meaning_verified"] = False
    report["automatic_publish_allowed"] = False

    if capture_ui or capture_mhtml:
        with TemporaryDirectory(prefix="rotation-browser-") as tmp:
            try:
                browser = run_browser(
                    spec.guide_url, Path(tmp), capture_ui=capture_ui,
                    capture_mhtml=capture_mhtml, max_states=max_states,
                    max_depth=max_depth,
                    expected_guide_sha256=expected_guide_sha256,
                    specialization=spec, expected_patch=expected_patch,
                    min_updated=min_updated,
                )
            except SourceAccessError as exc:
                # Never echo site text, actual URL query strings, or source.
                reason = str(exc).lower()
                if "403" in reason or "429" in reason or "denied" in reason:
                    category = "browser_access_denied"
                elif "patch" in reason or "older" in reason or "revision" in reason:
                    category = "browser_source_version_mismatch"
                elif "heading" in reason or "page title" in reason:
                    category = "browser_guide_identity_mismatch"
                elif "unavailable" in reason:
                    category = "browser_unavailable"
                else:
                    category = "browser_source_unavailable"
                report["ui_capture_status"] = category
            else:
                # Matching title/date alone cannot prove identical ordered
                # source rules. Compare exact guide-body digests before merging
                # *any* browser UI evidence into HTTP source's private packet.
                if (
                    browser.get("guide_body_sha256s") != report["guide_body_sha256s"]
                    or browser.get("observed_guide_update_date")
                    != report.get("observed_guide_update_date")
                ):
                    report["ui_capture_status"] = "browser_source_body_mismatch"
                else:
                    report["browser_enrichment_accepted"] = True
                    if capture_mhtml and (Path(tmp) / "page.mhtml").is_file():
                        copyfile(Path(tmp) / "page.mhtml", output / "page.mhtml")
                    if capture_ui:
                        for name in ("private-ui-capture.json", "ui-audit.json"):
                            if (Path(tmp) / name).is_file():
                                copyfile(Path(tmp) / name, output / name)
                        report["ui_states_observed"] = browser.get("ui_states_observed", 0)
                        report["ui_known_capture_gaps"] = bool(
                            browser.get("ui_known_capture_gaps", True)
                        )
                        report["ui_capture_status"] = (
                            "observed_partial" if report["ui_states_observed"]
                            else "not_observed"
                        )
                    else:
                        report["ui_capture_status"] = "mhtml_only"

    (output / "pipeline-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--url")
    src.add_argument("--http-url", help="One direct HTTPS GET; no browser, cookies or retries")
    src.add_argument("--specialization", help="Korean/English spec name; resolves to canonical Wowhead URL")
    src.add_argument("--saved-html", type=Path)
    src.add_argument("--saved-zip", type=Path)
    parser.add_argument("--allow-remote", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mhtml", action="store_true")
    parser.add_argument("--capture-ui", action="store_true")
    parser.add_argument("--expected-guide-sha256", help="Optional known-good WHML body SHA-256 for update comparison")
    parser.add_argument("--expected-patch", help="Optional patch string to require in visible page metadata")
    parser.add_argument("--min-updated", help="Optional minimum observed guide update date (YYYY-MM-DD)")
    parser.add_argument("--max-states", type=int, default=24)
    parser.add_argument("--max-depth", type=int, default=3)
    args = parser.parse_args(argv)
    if (args.expected_patch or args.min_updated) and not args.specialization:
        parser.error("--expected-patch/--min-updated require --specialization")
    if args.specialization:
        if not args.allow_remote:
            parser.error("Specialization mode requires --allow-remote")
        if args.capture_ui or args.mhtml:
            result = run_specialization_with_ui(
                args.specialization, args.output,
                capture_ui=args.capture_ui, capture_mhtml=args.mhtml,
                max_states=args.max_states, max_depth=args.max_depth,
                expected_guide_sha256=args.expected_guide_sha256,
                expected_patch=args.expected_patch,
                min_updated=args.min_updated,
            )
        else:
            result = run_specialization(
                args.specialization, args.output,
                expected_patch=args.expected_patch,
                min_updated=args.min_updated,
                expected_guide_sha256=args.expected_guide_sha256,
            )
    elif args.http_url:
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
