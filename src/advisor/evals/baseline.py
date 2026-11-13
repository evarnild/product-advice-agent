"""Which changes owe an eval run, the committed baseline, and the comparison (§17). Pure.

The caller reads the files and git; nothing here touches either. The path list is
the one in `REVIEW-POLICY.md` -> "Eval runs" (a test compares them). An entry that
ends in `/` is a prefix; any other entry is one exact file.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

EVAL_PATHS: tuple[str, ...] = (
    "src/advisor/prompts/",
    "src/advisor/agent.py",
    "src/advisor/models/",
    "src/advisor/guardrails.py",
    "src/advisor/catalogue.py",
    "src/advisor/data/",
    "src/advisor/config.py",
    "src/advisor/evals/cases.py",
    "src/advisor/evals/score.py",
    "evals/cases.jsonl",
)

HASH_FIELDS = ("cases_sha256", "prompt_sha256", "catalogue_sha256")
SOURCE_FIELDS = ("provider", "model", *HASH_FIELDS)


class BaselineError(ValueError):
    """The baseline file is not a usable baseline."""


def owes_run(paths: Iterable[str]) -> list[str]:
    """The changed paths that make an eval run owed (empty: none is owed)."""
    owed: list[str] = []
    for raw in paths:
        path = raw.strip().replace("\\", "/")
        if any(path.startswith(e) if e.endswith("/") else path == e for e in EVAL_PATHS):
            owed.append(path)
    return owed


def baseline_from(report: Mapping[str, Any], source: str) -> dict[str, Any]:
    """The baseline of a parsed report: its name, the run's identity and each case's status."""
    out: dict[str, Any] = {"source": source}
    for key in SOURCE_FIELDS:
        value = report.get(key)
        if isinstance(value, str):
            out[key] = value
    out["cases"] = {c["id"]: c["status"] for c in report["cases"]}
    return out


def check_baseline(raw: object) -> dict[str, Any]:
    """The baseline as a dict, or `BaselineError` naming what is wrong."""
    if not isinstance(raw, dict):
        raise BaselineError("not a baseline (expected an object)")
    cases = raw.get("cases")
    if not isinstance(cases, dict) or not all(
        isinstance(k, str) and v in ("PASS", "FAIL", "ERROR") for k, v in cases.items()
    ):
        raise BaselineError("not a baseline ('cases' must map case ids to PASS, FAIL or ERROR)")
    return raw


@dataclass(frozen=True)
class Comparison:
    baseline_source: str
    new_passed: int
    new_total: int
    old_passed: int
    old_total: int
    regressed: list[tuple[str, str, str]] = field(default_factory=list)  # id, old, new
    fixed: list[tuple[str, str, str]] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def compare(report: Mapping[str, Any], baseline: Mapping[str, Any]) -> Comparison:
    """The report against the baseline; it decides nothing (the owner does)."""
    new = {c["id"]: c["status"] for c in report["cases"]}
    old: Mapping[str, str] = baseline["cases"]
    regressed = [
        (i, old[i], s) for i, s in new.items() if i in old and old[i] == "PASS" and s != "PASS"
    ]
    fixed = [
        (i, old[i], s) for i, s in new.items() if i in old and old[i] != "PASS" and s == "PASS"
    ]
    warnings = []
    for key in SOURCE_FIELDS:
        a, b = baseline.get(key), report.get(key)
        if a != b:
            warnings.append(f"{key} differs: baseline {a or '(none)'}, report {b or '(none)'}")
    return Comparison(
        baseline_source=str(baseline.get("source", "(unnamed)")),
        new_passed=sum(1 for s in new.values() if s == "PASS"),
        new_total=len(new),
        old_passed=sum(1 for s in old.values() if s == "PASS"),
        old_total=len(old),
        regressed=regressed,
        fixed=fixed,
        added=[i for i in new if i not in old],
        removed=[i for i in old if i not in new],
        warnings=warnings,
    )


def format_comparison(c: Comparison) -> str:
    lines = [
        f"baseline {c.baseline_source}: {c.old_passed}/{c.old_total} passed",
        f"this run: {c.new_passed}/{c.new_total} passed",
    ]

    def block(title: str, items: Sequence[str]) -> None:
        lines.append(f"{title} ({len(items)}):" + ("" if items else " none"))
        lines.extend(f"  {item}" for item in items)

    block("regressed", [f"{i}: {a} -> {b}" for i, a, b in c.regressed])
    block("fixed", [f"{i}: {a} -> {b}" for i, a, b in c.fixed])
    block("added", c.added)
    block("removed", c.removed)
    lines.extend(f"warning: {w}" for w in c.warnings)
    return "\n".join(lines)
