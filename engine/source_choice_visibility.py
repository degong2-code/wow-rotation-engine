"""Conservative WHML display-options visibility parser, not game logic.

Observed source grammar: option names, ! NOT, & AND, | OR, parentheses.
Unknown option IDs, malformed syntax or excessive expressions return None.
Ancestors compose by AND. Never use visibility as a gameplay decision.
"""
from __future__ import annotations

import re

TOKENS = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*|[()!&|]")
MAX_LENGTH = 500
MAX_TOKENS = 160


def source_option_visible(expression: str, selected: set[str],
                          declared: set[str]) -> bool | None:
    if not isinstance(expression, str) or not 0 < len(expression) <= MAX_LENGTH:
        return None
    compact = re.sub(r"\s+", "", expression)
    tokens = TOKENS.findall(compact)
    if not tokens or len(tokens) > MAX_TOKENS or "".join(tokens) != compact:
        return None
    index = 0

    def atom():
        nonlocal index
        if index >= len(tokens):
            raise ValueError("missing expression operand")
        token = tokens[index]
        index += 1
        if token == "!":
            return not atom()
        if token == "(":
            result = or_expr()
            if index >= len(tokens) or tokens[index] != ")":
                raise ValueError("missing right parenthesis")
            index += 1
            return result
        if token not in declared:
            raise ValueError("unknown option or unsupported token")
        return token in selected

    def and_expr():
        nonlocal index
        result = atom()
        while index < len(tokens) and tokens[index] == "&":
            index += 1
            right = atom()
            result = result and right
        return result

    def or_expr():
        nonlocal index
        result = and_expr()
        while index < len(tokens) and tokens[index] == "|":
            index += 1
            right = and_expr()
            result = result or right
        return result

    try:
        result = or_expr()
        return result if index == len(tokens) else None
    except (ValueError, RecursionError):
        return None


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
