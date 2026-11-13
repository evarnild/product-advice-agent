"""Failure-mode taxonomy: drafting input, parsing and validation (§9 B13, B14). Pure.

A taxonomy names the labels file it maps (`labels`), lists the failure modes,
and maps each failed case id to one or more mode ids. It is valid when mode
ids are unique and non-empty, every mapped mode exists, every mapped case is a
fail in those labels, and every failed case is mapped at least once.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from advisor.evals.labels import Label
from advisor.evals.modeljson import extract_json

PROMPT_PATH = Path(__file__).parent / "prompts" / "taxonomy.md"


@dataclass(frozen=True)
class Mode:
    id: str
    name: str
    description: str


@dataclass(frozen=True)
class Taxonomy:
    labels: str
    modes: tuple[Mode, ...]
    mapping: dict[str, tuple[str, ...]]


def failed(labels: Mapping[str, Label]) -> dict[str, Label]:
    return {cid: x for cid, x in labels.items() if x.label == "fail"}


def build_prompt(labels: Mapping[str, Label], template: str | None = None) -> str:
    """The drafting prompt: every failed conversation with its critique, question and answer."""
    text = PROMPT_PATH.read_text(encoding="utf-8") if template is None else template
    blocks = [
        f"case id: {cid}\nquestion: {x.question}\nanswer: {x.answer}\ncritique: {x.critique}"
        for cid, x in sorted(failed(labels).items())
    ]
    return text.replace("[[failures]]", "\n\n".join(blocks))


def parse_taxonomy(value: Any, labels_ref: str | None = None) -> tuple[Taxonomy | None, list[str]]:
    """A `Taxonomy` from a decoded JSON value; the errors say what is malformed.

    `labels_ref` fills `labels` when the value (a model draft) has none.
    """
    errors: list[str] = []
    if not isinstance(value, dict):
        return None, ["the taxonomy must be a JSON object"]
    labels = value.get("labels", labels_ref)
    if not isinstance(labels, str) or not labels:
        errors.append("'labels' must name the labels file")
    modes: list[Mode] = []
    raw_modes = value.get("modes")
    if not isinstance(raw_modes, list):
        errors.append("'modes' must be a list")
        raw_modes = []
    for i, raw in enumerate(raw_modes, start=1):
        if not isinstance(raw, dict) or not all(
            isinstance(raw.get(k), str) for k in ("id", "name", "description")
        ):
            errors.append(f"mode {i}: must be an object with string 'id', 'name' and 'description'")
            continue
        modes.append(Mode(raw["id"], raw["name"], raw["description"]))
    mapping: dict[str, tuple[str, ...]] = {}
    raw_mapping = value.get("mapping")
    if not isinstance(raw_mapping, dict):
        errors.append("'mapping' must be an object of case id to a list of mode ids")
        raw_mapping = {}
    for cid, ids in raw_mapping.items():
        if not isinstance(ids, list) or not all(isinstance(m, str) for m in ids):
            errors.append(f"mapping for '{cid}': must be a list of mode ids")
            continue
        mapping[cid] = tuple(ids)
    if errors:
        return None, errors
    assert isinstance(labels, str)
    return Taxonomy(labels, tuple(modes), mapping), []


def validate(taxonomy: Taxonomy, labels: Mapping[str, Label]) -> list[str]:
    """The B14 errors for `taxonomy` against `labels`; empty when valid."""
    errors: list[str] = []
    seen: set[str] = set()
    for mode in taxonomy.modes:
        if not mode.id.strip():
            errors.append("a mode has an empty id")
        elif mode.id in seen:
            errors.append(f"mode id '{mode.id}' is used more than once")
        seen.add(mode.id)
    for cid, ids in taxonomy.mapping.items():
        for mode_id in ids:
            if mode_id not in seen:
                errors.append(f"case '{cid}' is mapped to unknown mode '{mode_id}'")
        current = labels.get(cid)
        if current is None:
            errors.append(f"case '{cid}' is mapped but has no label")
        elif current.label != "fail":
            errors.append(f"case '{cid}' is mapped but is not a fail (it is {current.label})")
    for cid in sorted(failed(labels)):
        if not taxonomy.mapping.get(cid):
            errors.append(f"failed case '{cid}' is not mapped to any mode")
    return errors


def parse_draft(
    text: str, labels: Mapping[str, Label], labels_ref: str
) -> tuple[Taxonomy | None, list[str]]:
    """A model's draft answer as a valid `Taxonomy`, or the reasons it is not."""
    value = extract_json(text)
    if value is None:
        return None, ["the model answer holds no JSON object"]
    taxonomy, errors = parse_taxonomy(value, labels_ref)
    if taxonomy is None:
        return None, errors
    errors = validate(taxonomy, labels)
    return (None, errors) if errors else (taxonomy, [])


def dumps(taxonomy: Taxonomy) -> str:
    return (
        json.dumps(
            {
                "labels": taxonomy.labels,
                "modes": [
                    {"id": m.id, "name": m.name, "description": m.description}
                    for m in taxonomy.modes
                ],
                "mapping": {cid: list(ids) for cid, ids in sorted(taxonomy.mapping.items())},
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
