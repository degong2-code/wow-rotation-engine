"""Offline tests of one plain HTTPS GET; no external network requests."""
from io import BytesIO
from urllib.error import HTTPError, URLError
from unittest import TestCase
from unittest.mock import Mock

from engine.http_source_fetch import get_html
from engine.source_page_acquire import SourceAccessError

URL = "https://www.wowhead.com/guide/classes/shaman/enhancement/rotation-cooldowns-pve-dps"
GUIDE = ('<!doctype html><html><body>'
         '<script>WH.markup.printHtml('
         '"[tooltip name=x]Synthetic note[/tooltip]",'
         '"guide-body",false);</script></body></html>').encode()


class Response(BytesIO):
    status = 200

    def __init__(self, body=GUIDE, *, status=200, url=URL,
                 content_type="text/html", length=None):
        super().__init__(body)
        self.status = status
        self._url = url
        self.headers = {"Content-Type": content_type}
        if length is not None:
            self.headers["Content-Length"] = str(length)

    def geturl(self):
        return self._url


class SourceFetchTests(TestCase):
    def test_normal_get_recovers_inline_whml(self):
        opener = Mock()
        opener.open.return_value = Response()
        result = get_html(URL, opener=opener)
        self.assertIn("WH.markup.printHtml", result)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertFalse(request.has_header("Cookie"))
        self.assertNotIn("Mozilla", request.get_header("User-agent", ""))

    def test_403_is_hard_refusal(self):
        opener = Mock()
        opener.open.side_effect = HTTPError(URL, 403, "Forbidden", {}, None)
        with self.assertRaisesRegex(SourceAccessError, "403 Forbidden"):
            get_html(URL, opener=opener)
        self.assertEqual(opener.open.call_count, 1)

    def test_rate_limit_is_not_retried(self):
        opener = Mock()
        opener.open.side_effect = HTTPError(URL, 429, "Too Many Requests", {}, None)
        with self.assertRaisesRegex(SourceAccessError, "429"):
            get_html(URL, opener=opener)
        self.assertEqual(opener.open.call_count, 1)

    def test_200_block_page_is_rejected_by_pipeline(self):
        from engine.source_acquisition_pipeline import inspect_and_store
        from tempfile import TemporaryDirectory
        from pathlib import Path
        opener = Mock()
        opener.open.return_value = Response(
            body=b"<!doctype html><html><body>Access challenge</body></html>"
        )
        html = get_html(URL, opener=opener)
        with TemporaryDirectory() as temp:
            with self.assertRaisesRegex(SourceAccessError, "No literal guide-body"):
                inspect_and_store(dom_html=html, output=Path(temp), kind="http_direct")

    def test_non_html_or_failed_status_is_rejected(self):
        for response in (Response(content_type="application/json"),
                         Response(status=302)):
            with self.subTest(status=response.status):
                opener = Mock()
                opener.open.return_value = response
                with self.assertRaises(SourceAccessError):
                    get_html(URL, opener=opener)

    def test_cross_host_response_is_rejected(self):
        opener = Mock()
        opener.open.return_value = Response(url="https://example.net/something")
        with self.assertRaises(SourceAccessError):
            get_html(URL, opener=opener)

    def test_url_host_port_and_scheme_restricted(self):
        for url in (
            "http://www.wowhead.com/example",
            "https://127.0.0.1/secret",
            "https://example.com/other",
            "https://notwowhead.com/other",
            "https://www.wowhead.com:8443/guide",
            "https://user:pass@www.wowhead.com/guide",
        ):
            with self.subTest(url=url):
                with self.assertRaises(SourceAccessError):
                    get_html(url, opener=Mock())

    def test_network_error_is_not_retried(self):
        opener = Mock()
        opener.open.side_effect = URLError("network unavailable")
        with self.assertRaisesRegex(SourceAccessError, "no browser fallback"):
            get_html(URL, opener=opener)
        self.assertEqual(opener.open.call_count, 1)

    def test_size_limit_rejected(self):
        from engine.source_page_acquire import MAX_HTML_BYTES
        opener = Mock()
        opener.open.return_value = Response(length=MAX_HTML_BYTES + 1)
        with self.assertRaisesRegex(SourceAccessError, "length exceeds"):
            get_html(URL, opener=opener)
