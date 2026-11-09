"""The guardrail seam.

Interpretation (spec): "guardrails beyond a placeholder seam are out of
scope" means the seam is real and tested (every run passes the question
through `check_input` and the answer through `check_output`, and a block
changes what the user gets), but both checks always allow in this skeleton.
Real checks are a later intent.
"""

from __future__ import annotations

from dataclasses import dataclass

REFUSAL_TEXT = "I can only help with questions about our electronics catalogue."


@dataclass(frozen=True)
class Verdict:
    allow: bool
    reason: str = ""


def check_input(question: str) -> Verdict:
    return Verdict(True)


def check_output(answer: str) -> Verdict:
    return Verdict(True)
