"""Acquire HTML for ChatGPT-first source analysis without bypassing site restrictions.

Sources:
  * authorized normal Chromium navigation (Playwright)
  * HTML previously saved by a user
  * Chrome's "Webpage, Complete" ZIP (HTML + companion _files resources)

Only the HTML is needed for the source condition/tooltip parser. Optional MHTML
stores other resources for offline reference; it is not required for analysis.

All captured HTML, response bodies and MHTML are PRIVATE. A separate metadata-
only audit intentionally does not publish source text, original paths or URLs.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import ipaddress
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
import zipfile

from .embedded_markup import inspect_embedded_whml

MAX_HTML_BYTES = 16 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 3000
MAX_ARCHIVE_BYTES = 128 * 1024 * 1024
MAX_MHTML_BYTES = 64 * 1024 * 1024


class SourceAccessError(RuntimeError):
    """Missing, denied, unsafe, or non-guide source; never report acquisition PASS."""


def _hash(value: bytes) -> str:
    return sha256(value).hexdigest()


def _decode_html(raw: bytes) -> str:
    if not raw or len(raw) > MAX_HTML_BYTES:
        raise SourceAccessError("HTML source is empty or exceeds the size limit")
    # Chrome-saved Wowhead pages are UTF-8. Other encodings require a separate
    # declared parser rather than quietly replacing skill names with U+FFFD.
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SourceAccessError("HTML is not UTF-8; do not silently replace source text") from exc


def _validate_html(html: str, required_markers: tuple[str, ...]) -> None:
    raw = html.encode("utf-8")
    if not raw or len(raw) > MAX_HTML_BYTES:
        raise SourceAccessError("HTML source is empty or exceeds the size limit")
    if "<html" not in html.lower() and "<!doctype html" not in html.lower():
        raise SourceAccessError("Captured body does not look like a complete HTML document")
    missing = [marker for marker in required_markers if marker not in html]
    if missing:
        raise SourceAccessError(
            "Expected source marker was not present; possible stale, blocked or incomplete page"
        )


def _validate_remote_url(url: str) -> None:
    split = urlsplit(url)
    if split.scheme != "https" or not split.hostname or split.username or split.password:
        raise SourceAccessError("Remote capture requires an explicit credential-free HTTPS URL")
    if split.hostname in {"localhost"} or split.hostname.endswith(".localhost"):
        raise SourceAccessError("Remote URL cannot target the local machine")
    try:
        address = ipaddress.ip_address(split.hostname)
        if not address.is_global:
            raise SourceAccessError("Nonpublic IP addresses cannot be remote capture targets")
    except ValueError:
        pass


def _score_html(text: str) -> tuple[int, int]:
    """Prefer the page holding inline content, not a secondary asset HTML."""
    return (10 * text.count("WH.markup.printHtml") +
            5 * text.count('"guide-body"') +
            3 * text.count("data-tooltip-name") +
            int("<main" in text.lower()), len(text))


def read_saved_html(path: Path) -> tuple[str, dict]:
    """Read HTML without touching its optional sibling *_files folder."""
    raw = path.read_bytes()
    html = _decode_html(raw)
    return html, {"kind": "saved_html", "companion_folder_required": False,
                  "archive_entries": 0}


def read_saved_zip(path: Path) -> tuple[str, dict]:
    """Read only the main HTML member of a browser's complete-page ZIP.

    Does not extract any paths or download CSS/JS, avoiding zip-slip and
    unnecessary public replication of third-party resources.
    """
    if path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise SourceAccessError("Saved archive is above the size limit")
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ARCHIVE_ENTRIES:
                raise SourceAccessError("Too many archive entries")
            candidates = []
            for item in infos:
                if item.is_dir() or not item.filename.lower().endswith((".html", ".htm")):
                    continue
                if item.file_size > MAX_HTML_BYTES:
                    continue
                body = _decode_html(archive.read(item))
                if "<html" in body.lower() or "<!doctype html" in body.lower():
                    candidates.append((_score_html(body), body))
            if not candidates:
                raise SourceAccessError("Archive contains no complete HTML page")
            candidates.sort(key=lambda row: row[0], reverse=True)
            _, selected = candidates[0]
            return selected, {
                "kind": "saved_zip",
                "companion_folder_required": False,
                "archive_entries": len(infos),
                "html_candidates": len(candidates),
                "resource_entries_ignored": len(infos) - 1,
            }
    except (zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise SourceAccessError("Invalid or unsupported ZIP archive") from exc


def capture_loaded_page(page, response, *, required_markers: tuple[str, ...] = (),
                        capture_mhtml: bool = False) -> tuple[str, str | None, str | None]:
    """Capture HTML after normal browser navigation; no stealth or challenge bypass.

    Return rendered DOM HTML, optional response HTML, optional MHTML. The source
    and DOM can differ after scripts run; store both rather than silently mixing.
    """
    if response is not None and response.status >= 400:
        raise SourceAccessError(
            "Browser navigation was denied or failed (HTTP " + str(response.status) + ")"
        )
    html = page.content()
    source = None
    if response is not None:
        try:
            content_type = response.headers.get("content-type", "").lower()
            if "html" in content_type:
                raw_source = response.body()
                if raw_source and len(raw_source) <= MAX_HTML_BYTES:
                    source = _decode_html(raw_source)
        except SourceAccessError:
            raise
        except Exception:
            # Some sites discard their response body after navigation. The DOM
            # snapshot remains available but cannot attest to original bytes.
            source = None
    if required_markers and not all(m in html for m in required_markers):
        if source is not None and all(m in source for m in required_markers):
            # The source has inline WHML even if hydration removed it from DOM.
            _validate_html(source, required_markers)
        else:
            raise SourceAccessError(
                "Required guide content was not found in browser DOM or HTML response"
            )
    _validate_html(html, ())
    if source is not None:
        _validate_html(source, ())
    mhtml = None
    if capture_mhtml:
        try:
            session = page.context.new_cdp_session(page)
            try:
                mhtml = session.send("Page.captureSnapshot", {"format": "mhtml"})["data"]
            finally:
                session.detach()
        except Exception as exc:
            raise SourceAccessError("Chromium MHTML snapshot was unavailable") from exc
        if not mhtml or len(mhtml.encode("utf-8")) > MAX_MHTML_BYTES:
            raise SourceAccessError("MHTML snapshot is empty or exceeds size limit")
    return html, source, mhtml


def select_analysis_html(dom_html: str, source_html: str | None) -> tuple[str, str]:
    """Choose the richer inline source, avoiding a hydration-stripped DOM.

    Always keep both inputs privately: a server response may contain WHML that
    the in-page JavaScript removed, while the DOM may contain new rendered data.
    """
    if source_html is not None and _score_html(source_html) > _score_html(dom_html):
        return source_html, "network_response"
    return dom_html, "rendered_dom"


def acquisition_audit(html: str, *, origin: str, source_html: str | None = None,
                      mhtml: str | None = None, extras: dict | None = None) -> dict:
    """Safe aggregate metrics: never include the source text, URL or file path."""
    analysis_html, analysis_variant = select_analysis_html(html, source_html)
    inspection = inspect_embedded_whml(analysis_html)
    guide = [x for x in inspection["payloads"] if x.get("target") == "guide-body"]
    return {
        "schema_version": "source-page-acquisition-audit-v1",
        "origin_kind": origin,
        "analysis_html_variant": analysis_variant,
        "dom_html_bytes": len(html.encode("utf-8")),
        "dom_html_sha256": _hash(html.encode("utf-8")),
        "raw_response_preserved": source_html is not None,
        "raw_response_sha256": (
            _hash(source_html.encode("utf-8")) if source_html is not None else None
        ),
        "optional_mhtml_saved": mhtml is not None,
        "guide_body_payloads": len(guide),
        "guide_body_lengths": [x["characters"] for x in guide],
        "guide_named_tooltips": sum(len(x.get("named_tooltip_bodies", [])) for x in guide),
        "guide_tooltip_references": sum(len(x["tooltip_references"]) for x in guide),
        "guide_options": sum(len(x.get("display_switches", {}).get("option_definitions", []))
                             for x in guide),
        "guide_conditional_displays": sum(
            x.get("display_switches", {}).get("conditional_occurrences", 0)
            for x in guide
        ),
        "asset_entries_not_needed_for_logic": (extras or {}).get("resource_entries_ignored"),
        "source_text_in_report": False,
        "site_version_verified": False,
        "real_site_completeness_verified": False,
        "gameplay_meaning_verified": False,
        "automatic_publish_allowed": False,
    }


def write_private_snapshot(output: Path, html: str, audit: dict,
                           *, source_html: str | None = None,
                           mhtml: str | None = None) -> None:
    output.mkdir(parents=True, exist_ok=True)
    # Explicit file names: use private workspace; NEVER commit these files.
    (output / "page.html").write_text(html, encoding="utf-8")
    analysis_html, _ = select_analysis_html(html, source_html)
    (output / "analysis.html").write_text(analysis_html, encoding="utf-8")
    if source_html is not None:
        (output / "network-response.html").write_text(source_html, encoding="utf-8")
    if mhtml is not None:
        (output / "page.mhtml").write_text(mhtml, encoding="utf-8")
    (output / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="Normal HTTPS browser navigation if permitted")
    group.add_argument("--saved-html", type=Path)
    group.add_argument("--saved-zip", type=Path)
    parser.add_argument("--allow-remote", action="store_true",
                        help="Required explicit opt-in for normal remote navigation")
    parser.add_argument("--require-marker", action="append", default=[],
                        help="Expected source text marker, e.g. WH.markup.printHtml")
    parser.add_argument("--mhtml", action="store_true",
                        help="Optionally embed images/styles/scripts for offline reference")
    parser.add_argument("--output", type=Path, required=True,
                        help="Private output directory, never a public repo")
    args = parser.parse_args(argv)
    markers = tuple(args.require_marker)
    source_html = mhtml = None
    if args.saved_html:
        html, metadata = read_saved_html(args.saved_html)
    elif args.saved_zip:
        html, metadata = read_saved_zip(args.saved_zip)
    else:
        if not args.allow_remote:
            parser.error("--url requires --allow-remote")
        _validate_remote_url(args.url)
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise SystemExit("Playwright is only required for --url mode") from exc
        with sync_playwright() as driver:
            browser = driver.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                response = page.goto(args.url, wait_until="domcontentloaded", timeout=20000)
                html, source_html, mhtml = capture_loaded_page(
                    page, response, required_markers=markers, capture_mhtml=args.mhtml
                )
            finally:
                browser.close()
        metadata = {"kind": "browser_url"}
    if not args.url:
        _validate_html(html, markers)
    audit = acquisition_audit(
        html, origin=metadata["kind"], source_html=source_html,
        mhtml=mhtml, extras=metadata
    )
    write_private_snapshot(args.output, html, audit, source_html=source_html,
                           mhtml=mhtml)
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
