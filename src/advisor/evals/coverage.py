"""The question grid and the coverage check (§9 B2, B3). Pure: no I/O, no model.

A generated question is only kept if its *probe* (the `search_products`
arguments that express it) behaves as its scenario says against the real
catalogue. The check is deterministic; no model judges it.
"""

from __future__ import annotations

import json
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from advisor.catalogue import CATEGORIES, Product, search_products
from advisor.evals.cases import SCENARIOS

PERSONAS = (
    "a student on a tight budget",
    "a non-technical buyer",
    "an enthusiast who knows the specs",
    "someone buying a gift",
)
QUESTIONS_PER_CELL = 2
_OFF_TOPIC = "off-topic"

Cell = tuple[str, str, str]  # (feature, scenario, persona)


def cells() -> list[Cell]:
    """Every meaningful (feature, scenario, persona) cell, in a fixed order.

    The `off-topic` scenario pairs only with the `off-topic` feature, and back.
    """
    out: list[Cell] = []
    for feature in (*CATEGORIES, _OFF_TOPIC):
        for scenario in SCENARIOS:
            if (feature == _OFF_TOPIC) != (scenario == _OFF_TOPIC):
                continue
            out.extend((feature, scenario, persona) for persona in PERSONAS)
    return out


def sample_cells(count: int, seed: int) -> list[Cell]:
    """The cells to ask about for `count` questions: a seeded shuffle, two questions a cell."""
    needed = -(-count // QUESTIONS_PER_CELL)
    pool = cells()
    random.Random(seed).shuffle(pool)
    return pool[:needed]


@dataclass(frozen=True)
class Probe:
    """The `search_products` arguments a question expresses."""

    category: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    keywords: tuple[str, ...] = ()
    product_id: str | None = None  # out-of-stock questions: the product they are about

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.category is not None:
            out["category"] = self.category
        if self.min_price is not None:
            out["min_price"] = self.min_price
        if self.max_price is not None:
            out["max_price"] = self.max_price
        if self.keywords:
            out["keywords"] = list(self.keywords)
        if self.product_id is not None:
            out["product_id"] = self.product_id
        return out

    def to_note(self) -> str:
        return "probe: " + json.dumps(self.to_dict(), sort_keys=True)


def _number(v: Any) -> bool:
    return isinstance(v, int | float) and not isinstance(v, bool)


def parse_probe(raw: Any) -> Probe | None:
    """A `Probe` from model output, or None when it is not a well-formed probe."""
    if not isinstance(raw, Mapping):
        return None
    category = raw.get("category")
    if category is not None and category not in CATEGORIES:
        return None
    for key in ("min_price", "max_price"):
        if raw.get(key) is not None and not _number(raw[key]):
            return None
    keywords = raw.get("keywords") or []
    if not isinstance(keywords, list) or not all(isinstance(k, str) and k for k in keywords):
        return None
    product_id = raw.get("product_id")
    if product_id is not None and not isinstance(product_id, str):
        return None
    return Probe(
        category=category,
        min_price=raw.get("min_price"),
        max_price=raw.get("max_price"),
        keywords=tuple(keywords),
        product_id=product_id,
    )


def _count(catalogue: Sequence[Product], probe: Probe, *, with_max_price: bool = True) -> int:
    return len(
        search_products(
            catalogue,
            category=probe.category,
            min_price=probe.min_price,
            max_price=probe.max_price if with_max_price else None,
            keywords=list(probe.keywords),
            limit=10,
        )
    )


def check_coverage(
    scenario: str, probe: Probe | None, question: str, catalogue: Sequence[Product]
) -> tuple[bool, str]:
    """Whether a candidate's probe fits its scenario; the reason names the failure."""
    if scenario == _OFF_TOPIC:
        return True, "ok"
    if probe is None:
        return False, "no probe"
    if scenario == "out-of-stock":
        product = next((p for p in catalogue if p.id == probe.product_id), None)
        if product is None:
            return False, f"product '{probe.product_id}' is not in the catalogue"
        if product.in_stock:
            return False, f"product {product.id} is in stock"
        return True, "ok"
    n = _count(catalogue, probe)
    if scenario == "exact-match":
        return (True, "ok") if n >= 1 else (False, "the probe matches no product")
    if scenario == "several-matches":
        return (True, "ok") if n >= 2 else (False, f"the probe matches {n} product(s), not 2+")
    if scenario == "no-match":
        return (True, "ok") if n == 0 else (False, f"the probe matches {n} product(s)")
    if scenario == "budget-too-low":
        if n != 0:
            return False, f"the probe matches {n} product(s) within the budget"
        if _count(catalogue, probe, with_max_price=False) < 1:
            return False, "the probe matches no product even without the budget"
        return True, "ok"
    if scenario == "spelling-differs":
        if not probe.keywords:
            return False, "the probe has no keywords"
        if n < 1:
            return False, "the probe matches no product"
        lowered = question.lower()
        for word in probe.keywords:
            if word.lower() in lowered:
                return False, f"the question contains the keyword '{word}' verbatim"
        return True, "ok"
    return False, f"unknown scenario '{scenario}'"
