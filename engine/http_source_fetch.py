"""One normal, read-only HTTPS GET for Wowhead source HTML.

This is an HTTP-first source acquisition option, not a browser emulator.
No cookies, credentials, retries, proxy switching, browser fingerprints, or
challenge bypass. An HTTP 403 is a hard denial for this request, not evidence
that a real user's browser cannot visit the page.
"""
from __future__ import annotations

from http.client import HTTPException
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener
)

from .source_page_acquire import (
    MAX_HTML_BYTES, SourceAccessError, _decode_html, _validate_html,
    _validate_remote_url,
)

USER_AGENT = "RotationTextbookSourceReview/0.1"
MAX_REDIRECTS = 3


def _validate_wowhead(url: str) -> str:
    _validate_remote_url(url)
    host = urlsplit(url).hostname or ""
    if host != "wowhead.com" and not host.endswith(".wowhead.com"):
        raise SourceAccessError("HTTP-first source retrieval is restricted to Wowhead hosts")
    if urlsplit(url).port not in (None, 443):
        raise SourceAccessError("HTTP-first source retrieval requires the normal HTTPS port")
    return host.lower()


class _SameHostRedirects(HTTPRedirectHandler):
    def __init__(self, expected_host: str):
        super().__init__()
        self.expected_host = expected_host
        self.redirect_count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected_host = _validate_wowhead(newurl)
        if redirected_host != self.expected_host:
            raise SourceAccessError("Source server redirected to another host")
        self.redirect_count += 1
        if self.redirect_count > MAX_REDIRECTS:
            raise SourceAccessError("Source server exceeded safe redirect count")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def get_html(url: str, *, opener=None) -> str:
    """Return UTF-8 HTML for a single normal GET, or fail without fallback.

    An injectable opener enables fully offline unit testing. The production
    opener explicitly ignores environment proxy settings to avoid implicitly
    routing requests through third parties.
    """
    host = _validate_wowhead(url)
    if opener is None:
        opener = build_opener(
            ProxyHandler({}),
            HTTPSHandler(context=ssl.create_default_context()),
            _SameHostRedirects(host),
        )
    request = Request(
        url,
        method="GET",
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html",
            "Accept-Encoding": "identity",
        },
    )
    try:
        with opener.open(request, timeout=15) as response:
            status = getattr(response, "status", 200)
            if status != 200:
                raise SourceAccessError("HTTP source request was not accepted (status " + str(status) + ")")
            destination = response.geturl()
            if _validate_wowhead(destination) != host:
                raise SourceAccessError("HTTP source final URL differs from the authorized host")
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type:
                raise SourceAccessError("HTTP source response was not HTML")
            declared_length = response.headers.get("Content-Length")
            if declared_length and int(declared_length) > MAX_HTML_BYTES:
                raise SourceAccessError("HTTP source length exceeds limit")
            data = response.read(MAX_HTML_BYTES + 1)
    except HTTPError as exc:
        if exc.code == 403:
            raise SourceAccessError("HTTP 403 Forbidden: this direct request was refused") from exc
        if exc.code == 429:
            raise SourceAccessError("HTTP 429 Too Many Requests: stop, do not retry") from exc
        raise SourceAccessError("HTTP source request failed with status " + str(exc.code)) from exc
    except (URLError, TimeoutError, OSError, HTTPException) as exc:
        raise SourceAccessError("HTTP source request failed; no browser fallback was attempted") from exc
    html = _decode_html(data)
    _validate_html(html, ())
    return html
