"""Which changes owe an eval run, the committed baseline, and the comparison (§17). Pure.

The caller reads the files and git; nothing here touches either. The path list is
the one in `REVIEW-POLICY.md` -> "Eval runs" (a test compares them). An entry that
ends in `/` is a prefix; any other entry is one exact file.
"""

from __future__ import annotations

import hashlib
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
HASH_FORM = "lf"


def content_sha256(data: bytes) -> str:
    """sha256 of the bytes with every CRLF read as LF (§29).

    Only the two-byte sequence is folded, so a checkout's line endings do not change the
    hash but any other whitespace edit still does (§13 B6).
    """
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


class BaselineError(ValueError):
    """The baseline file is not a usable baseline."""


def raw_sha256(data: bytes) -> str:
    """sha256 of the bytes as they are: the form of a report made before §29."""
    return hashlib.sha256(data).hexdigest()


def content_check(
    recorded: Mapping[str, Any], lf: Mapping[str, str], raw: Mapping[str, str]
) -> tuple[list[str], bool]:
    """Compare the hashes a report or baseline records with the files' (§29).

    A file with `hash_form: "lf"` is checked against the `lf` hashes; one without it
    (made before §29) against the raw-byte hashes. Returns one line per field and whether
    all three match.
    """
    is_lf = recorded.get("hash_form") == HASH_FORM
    now = lf if is_lf else raw
    lines = [] if is_lf else ["(raw bytes: recorded before §29)"]
    ok = True
    for key in HASH_FIELDS:
        got = recorded.get(key)
        if not isinstance(got, str):
            lines.append(f"{key} not recorded")
            ok = False
        elif got == now[key]:
            lines.append(f"{key} matches")
        else:
            lines.append(f"{key} differs: recorded {got}, files {now[key]}")
            ok = False
    return lines, ok


def rehash(report: Mapping[str, Any], files: Mapping[str, bytes]) -> dict[str, Any]:
    """The raw-form report with its hashes in the `lf` form, proved against the files.

    `files` maps each hash field to the bytes of the file it names. Each recorded hash must
    equal the sha256 of those bytes as they are, in LF form or in CRLF form; otherwise the
    run did not see this content and `BaselineError` names the field.
    """
    if report.get("hash_form") == HASH_FORM:
        raise BaselineError("the report is already line-ending free (hash_form lf)")
    out = dict(report)
    for key in HASH_FIELDS:
        data = files[key]
        folded = data.replace(b"\r\n", b"\n")
        accepted = {
            raw_sha256(data),
            raw_sha256(folded),
            raw_sha256(folded.replace(b"\n", b"\r\n")),
        }
        if report.get(key) not in accepted:
            raise BaselineError(f"{key}: the report was not made on these files")
        out[key] = content_sha256(data)
    out["hash_form"] = HASH_FORM
    return out


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
    if isinstance(report.get("hash_form"), str):
        out["hash_form"] = report["hash_form"]
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


def _form(source: Mapping[str, Any]) -> str:
    """The hash form a report or baseline records; none means raw bytes (before §29)."""
    form = source.get("hash_form")
    return form if isinstance(form, str) else "raw"


def _form_name(form: str) -> str:
    return "raw bytes, before §29" if form == "raw" else form


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
    form_a, form_b = _form(baseline), _form(report)
    for key in SOURCE_FIELDS:
        a, b = baseline.get(key), report.get(key)
        if a != b:
            text = f"{key} differs: baseline {a or '(none)'}, report {b or '(none)'}"
            if key in HASH_FIELDS and form_a != form_b:
                text += (
                    f"; hashed differently (baseline: {_form_name(form_a)}, "
                    f"report: {_form_name(form_b)}), so this does not show whether the "
                    "content changed"
                )
            warnings.append(text)
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
