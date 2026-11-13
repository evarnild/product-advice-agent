"""Label lines (§9 B11). Pure: the caller reads and appends the file.

One JSON line per change; the last line per `case_id` is the current label.
Each line carries the question and the answer, so it stands alone as a future
few-shot example.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime

LABELS = ("pass", "fail")


class LabelFileError(ValueError):
    """The labels file is invalid; the message names the line."""


@dataclass(frozen=True)
class Label:
    case_id: str
    label: str
    critique: str
    labelled_at: str
    question: str
    answer: str


def check_label(label: str, critique: str) -> str | None:
    """Why this label cannot be saved, or None. A fail needs a critique (B10)."""
    if label not in LABELS:
        return f"the label must be one of {', '.join(LABELS)}"
    if label == "fail" and not critique.strip():
        return "a fail needs a critique"
    return None


def label_line(
    case_id: str,
    label: str,
    critique: str,
    labelled_at: datetime,
    question: str,
    answer: str,
) -> str:
    """One JSON line (with its newline) for a label change; raises ValueError if invalid."""
    problem = check_label(label, critique)
    if problem is not None:
        raise ValueError(problem)
    stamp = labelled_at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    record = {
        "case_id": case_id,
        "label": label,
        "critique": critique.strip(),
        "labelled_at": stamp,
        "question": question,
        "answer": answer,
    }
    return json.dumps(record, ensure_ascii=False) + "\n"


def parse_labels(text: str) -> dict[str, Label]:
    """The current label per case id: the last line for an id wins."""
    current: dict[str, Label] = {}
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as e:
            raise LabelFileError(f"line {number}: not valid JSON ({e.msg})") from e
        if not isinstance(raw, dict):
            raise LabelFileError(f"line {number}: expected a JSON object")
        for key in ("case_id", "label", "critique", "labelled_at", "question", "answer"):
            if not isinstance(raw.get(key), str):
                raise LabelFileError(f"line {number}: field '{key}' must be a string")
        if raw["label"] not in LABELS:
            raise LabelFileError(f"line {number}: field 'label' must be one of {', '.join(LABELS)}")
        current[raw["case_id"]] = Label(
            raw["case_id"],
            raw["label"],
            raw["critique"],
            raw["labelled_at"],
            raw["question"],
            raw["answer"],
        )
    return current
