"""Langfuse annotation queues, SDK-free (§10 B19).

The `Annotations` protocol is what the `queue` and `import` subcommands need
from Langfuse; `advisor.tracing.LangfuseAnnotations` implements it with the
SDK. Everything here is pure: choosing the cases of a report, matching run
traces to cases, and turning annotation scores into §9 label lines.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from advisor.evals.labels import Label, label_line

SCORE_NAME = "pass"
CASE_TAG = "case:"
STAMP_FORMAT = "%Y%m%dT%H%M%SZ"


class AnnotationError(Exception):
    """A Langfuse step failed; `step` names it, `message` has no key in it."""

    def __init__(self, step: str, message: str) -> None:
        super().__init__(f"Langfuse {step} failed: {message}")
        self.step = step
        self.message = message


@dataclass(frozen=True)
class RunTrace:
    """A root observation of an eval trace: its trace id, the trace's tags, its start."""

    trace_id: str
    tags: tuple[str, ...]
    start_time: datetime


@dataclass(frozen=True)
class Score:
    """One annotation score named `pass`: the trace, the boolean, the comment, its time."""

    trace_id: str
    value: bool
    comment: str
    timestamp: datetime


class Annotations(Protocol):
    """What the subcommands use of Langfuse. Raises `AnnotationError`."""

    def ensure_score_config(self) -> str:
        """The id of the BOOLEAN `pass` score config; creates it when missing."""
        ...

    def ensure_queue(self, name: str, config_id: str) -> str:
        """The id of the queue `name`; creates it with `config_id` when missing."""
        ...

    def find_queue(self, name: str) -> str | None:
        """The id of the queue `name`, or None."""
        ...

    def run_traces(self, stamp: str) -> list[RunTrace]:
        """Root observations of the traces tagged `eval` and `run:<stamp>`."""
        ...

    def queued_trace_ids(self, queue_id: str) -> set[str]: ...

    def add_trace(self, queue_id: str, trace_id: str) -> None: ...

    def annotation_scores(self, queue_id: str) -> list[Score]:
        """Every annotation score named `pass` made in the queue."""
        ...


def report_stamp(report: Mapping[str, Any]) -> str:
    """The run stamp `run.py` put in the `run:` tag, from the report's `started`."""
    started = report.get("started")
    if not isinstance(started, str):
        raise ValueError("the report has no 'started' time, so its traces cannot be found")
    try:
        when = datetime.fromisoformat(started)
    except ValueError as e:
        raise ValueError(f"the report's 'started' is not a time: {started!r}") from e
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    return when.astimezone(UTC).strftime(STAMP_FORMAT)


def default_queue_name(stamp: str) -> str:
    return f"advisor-eval {stamp}"


def select_cases(
    report: Mapping[str, Any],
    *,
    feature: str | None = None,
    scenario: str | None = None,
    persona: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """The report's cases that match every given filter (AND); none given selects all."""
    wanted = {"feature": feature, "scenario": scenario, "persona": persona}
    chosen: list[dict[str, Any]] = []
    for case in report["cases"]:
        if status is not None and case["status"] != status:
            continue
        dims = case.get("dimensions") or {}
        if any(v is not None and dims.get(k) != v for k, v in wanted.items()):
            continue
        chosen.append(case)
    return chosen


def case_traces(traces: Sequence[RunTrace]) -> tuple[dict[str, str], int]:
    """Case id -> trace id from the `case:<id>` tags; the latest start wins a repeat.

    Returns the map and the number of traces that lost to a later one.
    """
    best: dict[str, RunTrace] = {}
    duplicates = 0
    for trace in traces:
        ids = [t[len(CASE_TAG) :] for t in trace.tags if t.startswith(CASE_TAG)]
        if not ids:
            continue
        case_id = ids[0]
        seen = best.get(case_id)
        if seen is None:
            best[case_id] = trace
            continue
        duplicates += 1
        if trace.start_time > seen.start_time:
            best[case_id] = trace
    return {c: t.trace_id for c, t in best.items()}, duplicates


@dataclass(frozen=True)
class QueuePlan:
    to_add: list[tuple[str, str]]  # (case id, trace id), in report order
    already_queued: int
    no_trace: int


def plan_additions(
    selected: Sequence[Mapping[str, Any]],
    traces_by_case: Mapping[str, str],
    queued: set[str],
) -> QueuePlan:
    to_add: list[tuple[str, str]] = []
    already = 0
    missing = 0
    for case in selected:
        trace_id = traces_by_case.get(case["id"])
        if trace_id is None:
            missing += 1
        elif trace_id in queued:
            already += 1
        else:
            to_add.append((case["id"], trace_id))
    return QueuePlan(to_add, already, missing)


@dataclass(frozen=True)
class ImportResult:
    lines: list[str]  # label lines to append, in report order
    unchanged: int
    fail_without_critique: list[str]  # case ids
    outside_run: int  # scores on traces that are not this run's


def labels_from_scores(
    report: Mapping[str, Any],
    scores: Sequence[Score],
    traces_by_case: Mapping[str, str],
    current: Mapping[str, Label],
) -> ImportResult:
    """Label lines for the cases whose latest score differs from the current label."""
    case_of = {trace_id: case_id for case_id, trace_id in traces_by_case.items()}
    in_report = {c["id"]: c for c in report["cases"]}
    latest: dict[str, Score] = {}  # case id -> its trace's latest score
    outside = 0
    for score in scores:
        case_id = case_of.get(score.trace_id)
        if case_id is None or case_id not in in_report:
            outside += 1
            continue
        seen = latest.get(case_id)
        if seen is None or score.timestamp >= seen.timestamp:
            latest[case_id] = score
    lines: list[str] = []
    unchanged = 0
    no_critique: list[str] = []
    for case in report["cases"]:
        chosen = latest.get(case["id"])
        if chosen is None:
            continue
        label = "pass" if chosen.value else "fail"
        critique = chosen.comment.strip()
        if label == "fail" and not critique:
            no_critique.append(case["id"])
            continue
        existing = current.get(case["id"])
        if existing is not None and existing.label == label and existing.critique == critique:
            unchanged += 1
            continue
        lines.append(
            label_line(
                case["id"], label, critique, chosen.timestamp, case["question"], case["answer"]
            )
        )
    return ImportResult(lines, unchanged, no_critique, outside)
