"""Read-only source-visibility grammar control on unrelated real WoW specs.

This is NOT an opener/gameplay QA and does not assume every specialization
has potion branches. Run one normal HTTPS GET for each guide; print only
counts and booleans, never guide text, expressions, talent names or HTML.
"""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from engine.source_acquisition_pipeline import run_specialization
from engine.source_page_acquire import SourceAccessError
from engine.spec_source_resolver import SpecializationResolutionError
from engine.source_choice_visibility import source_option_visible


def review_source(packet: dict) -> dict:
    declared = {option["id"]
                for p in packet["payloads"]
                for option in p["option_definitions"]}
    expressions = [c["expression"]
                   for p in packet["payloads"]
                   for c in p["conditional_expressions"]]
    recognized = 0
    decisions = 0
    unknown = 0
    for expression in expressions:
        # Empty selection checks that the expression is syntactically and
        # semantically interpretable for the declared options, not whether
        # its corresponding UI choice should be visible to a real player.
        result = source_option_visible(expression, set(), declared)
        if result is None:
            unknown += 1
        else:
            recognized += 1
            decisions += 1
    return {
        "captured_real_source": True,
        "conditional_expression_count": len(expressions),
        "declared_option_count": len(declared),
        "recognized_visibility_expressions": recognized,
        "unrecognized_visibility_expressions_review": unknown,
        "grammar_decisions_consistent": recognized + unknown == len(expressions),
        "hero_and_fight_contexts_verified": False,
        "gameplay_meaning_verified": False,
        "automatic_publish_allowed": False,
    }


def main() -> None:
    for name, label in (("생존 사냥꾼", "survival"),
                        ("비전 마법사", "arcane")):
        try:
            with TemporaryDirectory() as tmp:
                root = Path(tmp)
                run_specialization(name, root)
                packet = json.loads(
                    (root / "editorial-evidence-private.json").read_text("utf8")
                )
                report = review_source(packet)
                print("cross_spec_" + label + "_status=source_expression_inspected")
                for key, value in report.items():
                    print("cross_spec_" + label + "_" + key + "=" +
                          json.dumps(value))
        except (SourceAccessError, SpecializationResolutionError,
                ValueError, KeyError, OSError) as exc:
            print("cross_spec_" + label + "_status=source_review_required")
            print("cross_spec_" + label + "_error_class=" + type(exc).__name__)


if __name__ == "__main__":
    main()
