"""The failure-mode counts (§9 B15): three Markdown tables. Pure.

Only conversations in the report are counted. Agreement compares §8's status
with the owner's label and only reports; it never changes a check.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from advisor.evals.labels import Label
from advisor.evals.taxonomy import Taxonomy

DIMENSIONS = ("feature", "scenario", "persona")
_NONE = "(none)"


def _table(header: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    lines.extend("| " + " | ".join(str(c) for c in row) + " |" for row in rows)
    return "\n".join(lines)


def _ids(ids: Sequence[str]) -> str:
    return ", ".join(ids) if ids else "-"


def _failed(labels: Mapping[str, Label], cid: str) -> bool:
    label = labels.get(cid)
    return label is not None and label.label == "fail"


def mode_counts(
    report: Mapping[str, Any], labels: Mapping[str, Label], taxonomy: Taxonomy
) -> list[tuple[str, str, int]]:
    """(mode id, name, failed conversations) sorted by count descending, then id."""
    in_report = {c["id"] for c in report["cases"]}
    rows = []
    for mode in taxonomy.modes:
        n = sum(
            1
            for cid, ids in taxonomy.mapping.items()
            if cid in in_report and _failed(labels, cid) and mode.id in ids
        )
        rows.append((mode.id, mode.name, n))
    return sorted(rows, key=lambda r: (-r[2], r[0]))


def agreement(report: Mapping[str, Any], labels: Mapping[str, Label]) -> dict[str, list[str]]:
    """Case ids per agreement cell: §8's status against the owner's label."""
    cells: dict[str, list[str]] = {
        "both_pass": [],
        "both_fail": [],
        "misses": [],  # owner fail, status PASS: a check misses it
        "too_strict": [],  # owner pass, status FAIL: a check is too strict
        "error": [],
        "unlabelled": [],
    }
    for case in report["cases"]:
        label = labels.get(case["id"])
        status = case["status"]
        if status == "ERROR":
            cells["error"].append(case["id"])
        elif label is None:
            cells["unlabelled"].append(case["id"])
        elif status == "PASS" and label.label == "pass":
            cells["both_pass"].append(case["id"])
        elif status == "FAIL" and label.label == "fail":
            cells["both_fail"].append(case["id"])
        elif status == "PASS":
            cells["misses"].append(case["id"])
        else:
            cells["too_strict"].append(case["id"])
    return cells


def counts_markdown(
    report: Mapping[str, Any], labels: Mapping[str, Label], taxonomy: Taxonomy
) -> str:
    """The three tables, with a heading each."""
    by_id = {c["id"]: c for c in report["cases"]}
    parts = ["## Failed conversations per failure mode", ""]
    parts.append(
        _table(
            ["mode", "name", "failed"],
            [(i, n, c) for i, n, c in mode_counts(report, labels, taxonomy)],
        )
    )
    for dimension in DIMENSIONS:
        values = sorted(
            {(c.get("dimensions") or {}).get(dimension, _NONE) for c in report["cases"]}
        )
        rows = []
        for mode in taxonomy.modes:
            row: list[object] = [mode.id]
            for value in values:
                row.append(
                    sum(
                        1
                        for cid, ids in taxonomy.mapping.items()
                        if cid in by_id
                        and _failed(labels, cid)
                        and mode.id in ids
                        and (by_id[cid].get("dimensions") or {}).get(dimension, _NONE) == value
                    )
                )
            rows.append(row)
        parts += ["", f"## Failure modes by {dimension}", "", _table(["mode", *values], rows)]
    cells = agreement(report, labels)
    agree_rows = [
        ("both pass", len(cells["both_pass"]), "-"),
        ("both fail", len(cells["both_fail"]), "-"),
        (
            "owner fail, status PASS (a check misses it)",
            len(cells["misses"]),
            _ids(cells["misses"]),
        ),
        (
            "owner pass, status FAIL (a check is too strict)",
            len(cells["too_strict"]),
            _ids(cells["too_strict"]),
        ),
        ("status ERROR (any label)", len(cells["error"]), "-"),
        ("unlabelled (status not ERROR)", len(cells["unlabelled"]), "-"),
    ]
    parts += [
        "",
        "## Agreement between the automatic status and the owner's label",
        "",
        _table(["cell", "count", "cases"], agree_rows),
    ]
    return "\n".join(parts) + "\n"
