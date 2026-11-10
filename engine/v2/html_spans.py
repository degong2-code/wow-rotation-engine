"""Exact byte-offset HTML element splitter for a controlled, trusted HTML source.

Purpose: preserve the V11 authored HTML exactly on the first conversion.
Only the original trusted V11 source should be imported; untrusted page HTML is
NOT accepted here. Future source ingestion belongs to a separate sanitized stage.
"""
from dataclasses import dataclass
from html.parser import HTMLParser
from bisect import bisect_right
from typing import List

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr'}

@dataclass(frozen=True)
class Span:
    tag: str
    attrs: dict
    start: int
    inner_start: int
    inner_end: int
    end: int

    def full(self, source: str) -> str:
        return source[self.start:self.end]

    def inner(self, source: str) -> str:
        return source[self.inner_start:self.inner_end]

    def opener(self, source: str) -> str:
        return source[self.start:self.inner_start]

    def closer(self, source: str) -> str:
        return source[self.inner_end:self.end]

class SpanParser(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.offsets = [0]
        for line in source.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))
        self.stack = []
        self.spans: List[Span] = []
        self.feed(source)
        self.close()

    def where(self):
        line, col = self.getpos()
        return self.offsets[line-1] + col

    def handle_starttag(self, tag, attrs):
        if tag in VOID: return
        pos = self.where()
        op = self.get_starttag_text()
        self.stack.append((tag, dict(attrs), pos, pos + len(op)))

    def handle_startendtag(self, tag, attrs):
        return

    def handle_endtag(self, tag):
        if not self.stack: return
        # HTMLParser can normalize a few browser-autoclosed tags; source is
        # expected to be well nested around our target view/section elements.
        indices = [i for i, x in enumerate(self.stack) if x[0] == tag]
        if not indices: return
        idx = indices[-1]
        opener = self.stack[idx]
        self.stack = self.stack[:idx]
        end_start = self.where()
        end_end = self.source.find('>', end_start) + 1
        if end_end <= 0: raise ValueError('Unterminated close tag')
        self.spans.append(Span(opener[0], opener[1], opener[2], opener[3], end_start, end_end))


def find_class(spans, tag, class_name):
    return sorted([x for x in spans if x.tag == tag and class_name in x.attrs.get('class','').split()], key=lambda x: x.start)
