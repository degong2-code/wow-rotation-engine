"""Conservative evaluation of WHML display-options selection expressions.

This evaluates source visibility, not gameplay conditions. Validated grammar:
one declared option ID or pipe-separated OR of declared option IDs. A sequence
of ancestor/element scopes is AND. Unknown syntax/unknown options => None.
"""
from __future__ import annotations

import re

_ALTERNATIVES = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*(?:\|[A-Za-z0-9][A-Za-z0-9_-]*)*")


def source_option_visible(expression: str, selected: set[str],
                          declared: set[str]) -> bool | None:
    if not isinstance(expression, str) or not _ALTERNATIVES.fullmatch(expression):
        return None
    options = expression.split("|")
    if any(option not in declared for option in options):
        return None
    return bool(set(options) & selected)


def source_scopes_visible(expressions: list[str], selected: set[str],
                          declared: set[str]) -> bool | None:
    unknown = False
    for expression in expressions:
        result = source_option_visible(expression, selected, declared)
        if result is False:
            return False
        if result is None:
            unknown = True
    return None if unknown else True
