"""The eval case model and its validation. Pure: the caller reads the file."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from advisor.catalogue import CATEGORIES, Product

# The `search_products` argument names a case may constrain (spec B9).
SEARCH_CONSTRAINTS = ("category", "max_price", "min_price", "in_stock_only", "keywords_any")
_FIELDS = (
    "id",
    "question",
    "expect_ids",
    "forbid_ids",
    "must_decline",
    "expect_search",
    "note",
    "dimensions",
)
# The values `dimensions` may take (§9 B1).
FEATURES = (*CATEGORIES, "off-topic")
SCENARIOS = (
    "exact-match",
    "several-matches",
    "no-match",
    "budget-too-low",
    "out-of-stock",
    "off-topic",
    "spelling-differs",
)
_DIMENSION_KEYS = ("feature", "scenario", "persona")


class CaseFileError(ValueError):
    """The case file is invalid; the message names the line, the case and the field."""


@dataclass(frozen=True)
class Case:
    id: str
    question: str
    expect_ids: tuple[str, ...] = ()
    forbid_ids: tuple[str, ...] = ()
    must_decline: bool = False
    expect_search: dict[str, Any] = field(default_factory=dict)
    note: str = ""
    dimensions: dict[str, str] | None = None


_Fail = Callable[[str, str], CaseFileError]


def _is_number(v: Any) -> bool:
    return isinstance(v, int | float) and not isinstance(v, bool)


def _ids(raw: dict[str, Any], key: str, known: set[str], fail: _Fail) -> tuple[str, ...]:
    value = raw.get(key, [])
    if not isinstance(value, list) or not all(isinstance(i, str) for i in value):
        raise fail(key, "must be a list of product ids")
    for i in value:
        if i not in known:
            raise fail(key, f"names unknown product id '{i}'")
    return tuple(value)


def _search(raw: dict[str, Any], fail: _Fail) -> dict[str, Any]:
    value = raw["expect_search"]
    if not isinstance(value, dict) or not value:
        raise fail("expect_search", "must be a non-empty object")
    for name, v in value.items():
        if name not in SEARCH_CONSTRAINTS:
            raise fail(
                "expect_search",
                f"has unknown constraint '{name}' (allowed: {', '.join(SEARCH_CONSTRAINTS)})",
            )
        if name == "category" and v not in CATEGORIES:
            raise fail("expect_search", f"'category' must be one of {', '.join(CATEGORIES)}")
        if name in ("max_price", "min_price") and not _is_number(v):
            raise fail("expect_search", f"'{name}' must be a number")
        if name == "in_stock_only" and not isinstance(v, bool):
            raise fail("expect_search", "'in_stock_only' must be true or false")
        if name == "keywords_any" and (
            not isinstance(v, list) or not v or not all(isinstance(k, str) and k for k in v)
        ):
            raise fail("expect_search", "'keywords_any' must be a non-empty list of words")
    return dict(value)


def _dimensions(raw: dict[str, Any], fail: _Fail) -> dict[str, str]:
    value = raw["dimensions"]
    if not isinstance(value, dict):
        raise fail("dimensions", "must be an object")
    extra = sorted(set(value) - set(_DIMENSION_KEYS))
    if extra:
        raise fail("dimensions", f"has unknown key '{extra[0]}'")
    for key in _DIMENSION_KEYS:
        if key not in value:
            raise fail("dimensions", f"is missing '{key}'")
    if value["feature"] not in FEATURES:
        raise fail("dimensions", f"'feature' must be one of {', '.join(FEATURES)}")
    if value["scenario"] not in SCENARIOS:
        raise fail("dimensions", f"'scenario' must be one of {', '.join(SCENARIOS)}")
    persona = value["persona"]
    if not isinstance(persona, str) or not persona.strip():
        raise fail("dimensions", "'persona' must be a non-empty string")
    return {k: value[k] for k in _DIMENSION_KEYS}


def parse_cases(text: str, catalogue: Sequence[Product]) -> list[Case]:
    """Parse and validate JSON-lines `text`; raises CaseFileError."""
    known = {p.id for p in catalogue}
    cases: list[Case] = []
    seen: set[str] = set()
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as e:
            raise CaseFileError(f"line {number}: not valid JSON ({e.msg})") from e
        if not isinstance(raw, dict):
            raise CaseFileError(f"line {number}: expected a JSON object")
        label = raw["id"] if isinstance(raw.get("id"), str) and raw["id"] else f"line {number}"

        def fail(fld: str, why: str, number: int = number, label: str = label) -> CaseFileError:
            return CaseFileError(f"line {number}, case '{label}': field '{fld}' {why}")

        unknown = sorted(set(raw) - set(_FIELDS))
        if unknown:
            raise fail(unknown[0], "is not a known field")
        for required in ("id", "question"):
            if not isinstance(raw.get(required), str) or not raw[required].strip():
                raise fail(required, "must be a non-empty string")
        if raw["id"] in seen:
            raise fail("id", "is a duplicate")
        seen.add(raw["id"])
        expect_ids = _ids(raw, "expect_ids", known, fail)
        forbid_ids = _ids(raw, "forbid_ids", known, fail)
        must_decline = raw.get("must_decline", False)
        if not isinstance(must_decline, bool):
            raise fail("must_decline", "must be true or false")
        if must_decline and expect_ids:
            raise fail("expect_ids", "must be empty when must_decline is true")
        note = raw.get("note", "")
        if not isinstance(note, str):
            raise fail("note", "must be a string")
        cases.append(
            Case(
                id=raw["id"],
                question=raw["question"],
                expect_ids=expect_ids,
                forbid_ids=forbid_ids,
                must_decline=must_decline,
                expect_search=_search(raw, fail) if "expect_search" in raw else {},
                note=note,
                dimensions=_dimensions(raw, fail) if "dimensions" in raw else None,
            )
        )
    if not cases:
        raise CaseFileError("the case file has no cases")
    return cases
