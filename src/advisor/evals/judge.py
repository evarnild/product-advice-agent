"""The `judge-no-fit` LLM judge (§16): scope, prompt, verdict, split, agreement. Pure.

The caller reads the files, calls the model and writes the results. One judge,
for one failure mode: "an honest answer when nothing fits" (the owner's
combination of `no_product_available` and `irrelevant_alternatives`).
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from advisor.evals.modeljson import extract_json

PROMPT_PATH = Path(__file__).parent / "prompts" / "judge-no-fit.md"
SCORE_NAME_JUDGE = "judge-no-fit"

# Interpretation (spec): in scope by the case's scenario, not by its search
# results. The scenario is fixed by the probe check (§9); a model that did not
# search still owes an honest no-fit answer.
IN_SCOPE_SCENARIOS = ("no-match", "budget-too-low")

MAX_FEW_SHOT = 8
MIN_RATE = Fraction(4, 5)  # B7: both rates at least 0.8
MIN_CONVERSATIONS = 30
MIN_FAILS = 10

# A fixed namespace so a score id depends only on the run stamp and the case (B9).
_SCORE_NAMESPACE = uuid.UUID("5d0c1f3e-0f6a-5b8e-9a53-16a1c0de0016")


def in_scope(case: Mapping[str, Any]) -> bool:
    """B1: a case whose `dimensions.scenario` is `no-match` or `budget-too-low`."""
    dims = case.get("dimensions")
    if not isinstance(dims, Mapping):
        return False
    return dims.get("scenario") in IN_SCOPE_SCENARIOS


# --- The conversation and the prompt ----------------------------------------


def conversation(question: str, tools: Sequence[Mapping[str, Any]] | None, answer: str) -> str:
    """B2: the question, each tool call with the rows it returned, and the answer.

    The judge never reads the catalogue: this is all the model saw, so a
    verdict survives a catalogue change (§13).
    """
    lines = [f"Customer question: {question}", "", "Searches the assistant ran:"]
    if not tools:
        lines.append("(none: the assistant ran no search)")
    for number, call in enumerate(tools or (), start=1):
        arguments = json.dumps(call.get("arguments", {}), ensure_ascii=False, sort_keys=True)
        lines.append(f"{number}. {call.get('name', '?')} {arguments}")
        if call.get("error"):
            lines.append("   the call failed")
        results = call.get("results") or []
        lines.append(f"   returned {len(results)} product(s)")
        for row in results:
            lines.append("   - " + json.dumps(row, ensure_ascii=False, sort_keys=True))
    lines += ["", f"Assistant answer: {answer}"]
    return "\n".join(lines)


@dataclass(frozen=True)
class Example:
    """One few-shot example: an owner-labelled conversation."""

    ref: str  # "<labels file>#<case id>"
    label: str  # "pass" | "fail"
    critique: str
    text: str  # `conversation(...)`


def examples_block(examples: Sequence[Example]) -> str:
    blocks: list[str] = []
    for number, ex in enumerate(examples, start=1):
        parts = [f"### Example {number}", ex.text, f"Owner's verdict: {ex.label.upper()}"]
        if ex.critique.strip():
            parts.append(f"Owner's critique: {ex.critique.strip()}")
        blocks.append("\n".join(parts))
    return "\n\n".join(blocks)


def build_prompt(template: str | None, text: str, examples: Sequence[Example]) -> str:
    """B3/B6: the template with exactly `examples` and the conversation to judge."""
    base = PROMPT_PATH.read_text(encoding="utf-8") if template is None else template
    # The examples go in first: a slot-like string inside a conversation is then
    # never replaced.
    return base.replace("[[examples]]", examples_block(examples)).replace("[[conversation]]", text)


# --- The verdict ------------------------------------------------------------


@dataclass(frozen=True)
class Verdict:
    passed: bool
    reason: str


@dataclass(frozen=True)
class JudgeError:
    """The model's answer is not a verdict (B4): recorded, never a pass or a fail."""

    reason: str


def parse_verdict(text: str) -> Verdict | JudgeError:
    """B4: `{"pass": true|false, "reason": "..."}`; anything else is a `JudgeError`."""
    value = extract_json(text)
    if not isinstance(value, dict):
        return JudgeError("the model answer holds no JSON object")
    passed = value.get("pass")
    if not isinstance(passed, bool):
        return JudgeError("the JSON has no boolean 'pass'")
    reason = value.get("reason")
    return Verdict(passed, reason.strip() if isinstance(reason, str) else "")


def score_id(stamp: str, case_id: str) -> str:
    """B9: the same id for the same run and case, so a rerun replaces the score."""
    return str(uuid.uuid5(_SCORE_NAMESPACE, f"{SCORE_NAME_JUDGE}:{stamp}:{case_id}"))


# --- The split --------------------------------------------------------------


class SplitError(ValueError):
    """`split.json` is not a valid split; the message says why."""


@dataclass(frozen=True)
class Split:
    few_shot: tuple[str, ...]  # "<labels file>#<case id>"
    held_out: tuple[str, ...]


def split_ref(labels_file: str, case_id: str) -> str:
    return f"{labels_file}#{case_id}"


def parse_ref(ref: str) -> tuple[str, str]:
    """`(labels file, case id)` of a split entry."""
    file, sep, case_id = ref.partition("#")
    if not sep or not file or not case_id:
        raise SplitError(f"'{ref}' is not '<labels file>#<case id>'")
    return file, case_id


def parse_split(value: Any, labels: Mapping[str, str] | None = None) -> Split:
    """B6: at most 8 few-shot, none shared with held-out, no duplicates.

    `labels` maps each ref to its current label ("pass" or "fail"); when given,
    every entry must be in it and the few-shot examples must hold both labels.
    """
    if not isinstance(value, dict):
        raise SplitError("the split must be a JSON object with 'few_shot' and 'held_out'")
    sets: dict[str, tuple[str, ...]] = {}
    for key in ("few_shot", "held_out"):
        items = value.get(key)
        if not isinstance(items, list) or not all(isinstance(i, str) for i in items):
            raise SplitError(f"'{key}' must be a list of '<labels file>#<case id>' strings")
        if len(set(items)) != len(items):
            raise SplitError(f"'{key}' names a conversation twice")
        for item in items:
            parse_ref(item)
        sets[key] = tuple(items)
    few, held = sets["few_shot"], sets["held_out"]
    if len(few) > MAX_FEW_SHOT:
        raise SplitError(f"'few_shot' has {len(few)} entries; at most {MAX_FEW_SHOT}")
    overlap = sorted(set(few) & set(held))
    if overlap:
        raise SplitError(f"in both few_shot and held_out: {', '.join(overlap)}")
    if labels is not None:
        for ref in (*few, *held):
            if ref not in labels:
                raise SplitError(f"'{ref}' has no current owner label")
        if {labels[r] for r in few} != {"pass", "fail"}:
            raise SplitError("'few_shot' must hold at least one pass and one fail")
    return Split(few, held)


# --- Agreement with the owner (B7) ------------------------------------------


@dataclass(frozen=True)
class Agreement:
    pass_pass: int  # owner pass, judge pass
    pass_fail: int  # owner pass, judge fail
    fail_pass: int  # owner fail, judge pass
    fail_fail: int  # owner fail, judge fail
    errors: int
    tpr: Fraction | None  # None when the owner has no pass with a verdict
    tnr: Fraction | None
    trusted: bool
    reasons: tuple[str, ...]  # why not trusted; empty when trusted

    @property
    def judged(self) -> int:
        return self.pass_pass + self.pass_fail + self.fail_pass + self.fail_fail

    @property
    def owner_fails(self) -> int:
        return self.fail_pass + self.fail_fail


def agreement(pairs: Sequence[tuple[bool, bool | None]]) -> Agreement:
    """B7 from `(owner passed, judge passed or None for a judge error)` pairs.

    Errors are counted and left out of the rates. Interpretation: the minimums
    (30 conversations, 10 fails) count conversations with a verdict, since only
    those enter a rate; with no owner fail the rate is undefined, so the judge
    is not trusted.
    """
    pp = pf = fp = ff = errors = 0
    for owner_pass, judge_pass in pairs:
        if judge_pass is None:
            errors += 1
        elif owner_pass and judge_pass:
            pp += 1
        elif owner_pass:
            pf += 1
        elif judge_pass:
            fp += 1
        else:
            ff += 1
    tpr = Fraction(pp, pp + pf) if pp + pf else None
    tnr = Fraction(ff, fp + ff) if fp + ff else None
    reasons: list[str] = []
    if tpr is None:
        reasons.append("no owner pass with a verdict, so the true-positive rate is undefined")
    elif tpr < MIN_RATE:
        reasons.append(f"true-positive rate {float(tpr):.2f} is below 0.80")
    if tnr is None:
        reasons.append("no owner fail with a verdict, so the true-negative rate is undefined")
    elif tnr < MIN_RATE:
        reasons.append(f"true-negative rate {float(tnr):.2f} is below 0.80")
    total = pp + pf + fp + ff
    if total < MIN_CONVERSATIONS:
        reasons.append(f"{total} judged conversations; at least {MIN_CONVERSATIONS} are needed")
    if fp + ff < MIN_FAILS:
        reasons.append(f"{fp + ff} owner fails; at least {MIN_FAILS} are needed")
    return Agreement(pp, pf, fp, ff, errors, tpr, tnr, not reasons, tuple(reasons))


@dataclass(frozen=True)
class ValidationRow:
    ref: str
    owner_pass: bool
    owner_critique: str
    judge_pass: bool | None  # None: a judge error
    judge_reason: str


def _rate(value: Fraction | None) -> str:
    return (
        "undefined"
        if value is None
        else f"{float(value):.2f} ({value.numerator}/{value.denominator})"
    )


def _word(passed: bool) -> str:
    return "pass" if passed else "fail"


def validation_markdown(
    rows: Sequence[ValidationRow],
    *,
    model: str,
    prompt_sha256: str,
    few_shot: Sequence[str],
    skipped: Sequence[str] = (),
) -> str:
    """B7: the report committed as `evals/judge/validation.md`."""
    a = agreement([(r.owner_pass, r.judge_pass) for r in rows])
    verdict = "trusted" if a.trusted else "not trusted"
    lines = [
        "# Judge validation: judge-no-fit",
        "",
        f"**Verdict: {verdict}.**" + ("" if a.trusted else " " + "; ".join(a.reasons) + "."),
        "",
        f"- Model: {model}",
        f"- Prompt sha256: {prompt_sha256}",
        f"- Few-shot examples: {len(few_shot)}",
        f"- Held-out conversations: {len(rows)} "
        f"({a.judged} with a verdict, {a.errors} judge errors)",
        f"- True-positive rate (owner pass, judge pass / owner pass): {_rate(a.tpr)}",
        f"- True-negative rate (owner fail, judge fail / owner fail): {_rate(a.tnr)}",
        "",
        "| | judge pass | judge fail |",
        "| --- | --- | --- |",
        f"| owner pass | {a.pass_pass} | {a.pass_fail} |",
        f"| owner fail | {a.fail_pass} | {a.fail_fail} |",
        "",
        "## Disagreements and judge errors",
        "",
    ]
    wrong = [r for r in rows if r.judge_pass is None or r.judge_pass != r.owner_pass]
    if not wrong:
        lines.append("None.")
    for r in wrong:
        judge = "ERROR" if r.judge_pass is None else _word(r.judge_pass)
        lines.append(f"- {r.ref}: owner {_word(r.owner_pass)}, judge {judge}")
        if r.owner_critique.strip():
            lines.append(f"  - owner: {r.owner_critique.strip()}")
        lines.append(f"  - judge: {r.judge_reason or '(no reason)'}")
    if skipped:
        lines += ["", "## Skipped", ""]
        lines += [f"- {s}" for s in skipped]
    return "\n".join(lines) + "\n"
