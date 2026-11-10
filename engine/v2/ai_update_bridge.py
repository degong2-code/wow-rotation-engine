"""Bridge provider-neutral proposals to the EXISTING private V11 UPDATE gate.

The provider receives only selected rule text and user-supplied excerpt, not
the private V11 HTML. Model output is validated using existing source quote,
row-ID, immutable HTML, and separate human approval requirements.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .ai_runtime import AIJob, AIProposal, AIProvider
from .ai_proposals import SYSTEM_PROMPT, prepare_request, review_report


@dataclass(frozen=True)
class UpdateReviewCandidate:
    """Private-memory review result, never a published HTML or approved patch."""
    prepared: dict
    proposal: dict
    review: dict
    model: str
    requires_human_approval: bool = True
    published: bool = False

    def __post_init__(self):
        if not self.requires_human_approval or self.published:
            raise ValueError("AI cannot bypass the existing V11 review gate")


def prepare_update_with_provider(
    detail: dict,
    excerpt: str,
    rule_ids: list[str],
    *,
    provider: AIProvider,
    model: str,
) -> UpdateReviewCandidate:
    """Opt-in caller-supplied provider. No network call without this invocation."""
    prepared = prepare_request(detail, excerpt, rule_ids)
    job = AIJob(
        operation="update",
        instruction=SYSTEM_PROMPT,
        source_text=json.dumps(prepared, ensure_ascii=False),
    )
    returned = provider.propose(job, model=model)
    if not isinstance(returned, AIProposal):
        raise ValueError("Provider must return an unapproved AIProposal")
    if returned.operation != "update" or returned.status != "review_required":
        raise ValueError("Provider returned wrong operation or approval state")
    # Existing review gate verifies exact source excerpt, ID identity,
    # original text-node containment, and prevents markup edits.
    reviewed = review_report(prepared, returned.candidate, detail)
    return UpdateReviewCandidate(
        prepared=prepared,
        proposal=returned.candidate,
        review=reviewed,
        model=returned.model,
    )
