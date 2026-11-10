"""CLI: validate, build, diff. Safe defaults: no automatic publication."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from .pipeline import build, canonical_sha, load, validate


def main() -> int:
    p = argparse.ArgumentParser(description="WoW Rotation Engine: public CI bootstrap")
    commands = p.add_subparsers(dest="command", required=True)
    check = commands.add_parser("validate")
    check.add_argument("--input", required=True)
    render = commands.add_parser("build")
    render.add_argument("--input", required=True)
    render.add_argument("--output", required=True)
    render.add_argument("--allow-demo", action="store_true")
    diff = commands.add_parser("diff")
    diff.add_argument("--before", required=True)
    diff.add_argument("--after", required=True)
    args = p.parse_args()
    if args.command == "validate":
        data = load(args.input)
        errors = validate(data)
        for error in errors:
            print("ERROR", error)
        print("VALID" if not errors else "INVALID", canonical_sha(data))
        return 1 if errors else 0
    if args.command == "build":
        data = load(args.input)
        page = build(data, allow_demo=args.allow_demo)
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8")
        print("BUILD", str(out), "catalog_sha256", canonical_sha(data))
        return 0
    before, after = load(args.before), load(args.after)
    report = {"status": "no-change" if canonical_sha(before) == canonical_sha(after) else "review-required",
              "before_sha256": canonical_sha(before), "after_sha256": canonical_sha(after),
              "automatic_publish_allowed": False,
              "notice": "Meaningful changes require source verification and editorial review."}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
