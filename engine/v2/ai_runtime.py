"""Provider-neutral AI proposal contract for V11 CREATE / UPDATE.

The model never edits V11 or publishes HTML. Its output remains an unapproved
candidate until the deterministic schema/evidence reviewers accept it.
This module has no network access, credential handling, or model hardcoding.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


OPERATIONS = frozenset({"extract", "compare", "explain", "update"})

@dataclass(frozen=True)
class ModelOption:
    slug: str
    display_name: str


@dataclass(frozen=True)
class AIJob:
    operation: str
    instruction: str
    source_text: str

    def __post_init__(self):
        if self.operation not in OPERATIONS:
            raise ValueError("Unsupported AI job operation")
        if not isinstance(self.instruction, str) or not self.instruction.strip():
            raise ValueError("AI job requires a specific instruction")
        if not isinstance(self.source_text, str) or not self.source_text.strip():
            raise ValueError("AI job requires source material")
        if len(self.instruction) > 12000 or len(self.source_text) > 160000:
            raise ValueError("AI job too large; split into bounded source segments")


@dataclass(frozen=True)
class AIProposal:
    provider: str
    model: str
    operation: str
    candidate: dict[str, Any]
    status: str = "review_required"
    gameplay_verified: bool = False
    auto_applied: bool = False
    auto_published: bool = False

    def __post_init__(self):
        if (self.status != "review_required" or self.gameplay_verified
                or self.auto_applied or self.auto_published):
            raise ValueError("AI responses cannot bypass independent review")
        if not isinstance(self.candidate, dict):
            raise ValueError("AI proposal must contain one JSON object")


class AIProvider(Protocol):
    def list_models(self) -> tuple[ModelOption, ...]:
        """Get account-specific supported models, not guessed model slugs."""
        ...

    def propose(self, job: AIJob, *, model: str) -> AIProposal:
        """Return a review-only candidate, never an approved patch."""
        ...
