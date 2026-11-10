"""Conservative three-valued conditions. Unknown inputs never become True/False."""
from __future__ import annotations

MISSING = object()
FIELDS = {"hero", "target_count", "combo_points", "combo_point_cap", "phase", "combat_mode"}


def _value(name: str, context: dict):
    if name in FIELDS:
        return context.get(name, MISSING)
    for prefix, key in (("buff:", "buffs"), ("talent:", "talents"), ("ready:", "ready")):
        if name.startswith(prefix):
            return context.get(key, {}).get(name[len(prefix):], MISSING)
    raise ValueError(f"Unsupported condition field: {name}")


def evaluate(expr: dict, context: dict) -> bool | None:
    """True/False/None (unknown). Reject malformed expressions."""
    if not isinstance(expr, dict):
        raise ValueError("A condition must be a JSON object")
    if "all" in expr:
        xs = expr["all"]
        if not isinstance(xs, list) or not xs:
            raise ValueError("all must contain conditions")
        vs = [evaluate(x, context) for x in xs]
        return False if False in vs else None if None in vs else True
    if "any" in expr:
        xs = expr["any"]
        if not isinstance(xs, list) or not xs:
            raise ValueError("any must contain conditions")
        vs = [evaluate(x, context) for x in xs]
        return True if True in vs else None if None in vs else False
    if "not" in expr:
        v = evaluate(expr["not"], context)
        return None if v is None else not v
    if set(expr) - {"field", "op", "value", "rhs_field"}:
        raise ValueError("Unexpected condition properties")
    field, op = expr.get("field"), expr.get("op")
    if not isinstance(field, str) or op not in {"eq", "ne", "gte", "lte"}:
        raise ValueError("Unsupported condition comparison")
    if ("value" in expr) == ("rhs_field" in expr):
        raise ValueError("Exactly one of value or rhs_field is required")
    left = _value(field, context)
    right = _value(expr["rhs_field"], context) if "rhs_field" in expr else expr["value"]
    if left is MISSING or right is MISSING or left is None or right is None:
        return None
    if op in {"gte", "lte"}:
        if type(left) not in {int, float} or type(right) not in {int, float}:
            raise ValueError("Numeric comparisons require numeric operands")
    return {"eq": lambda: left == right, "ne": lambda: left != right,
            "gte": lambda: left >= right, "lte": lambda: left <= right}[op]()
