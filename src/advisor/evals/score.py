"""Deterministic scorers for an advisor answer. Pure: no files, no model."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from advisor.catalogue import Product, _norm
from advisor.evals.cases import Case
from advisor.guardrails import REFUSAL_TEXT

# `P-` plus three digits, not inside a longer token (`P-0011`, `XP-001`).
_ID_RE = re.compile(r"(?<![A-Za-z0-9])P-\d{3}(?!\d)")


# Between thousands groups: comma, dot, space, no-break space, narrow no-break space.
_GROUP_SEP = "[,. \u00a0\u202f]"


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    reason: str


def cited_ids(answer: str) -> list[str]:
    """Product ids cited in `answer`, once each, in order of first appearance."""
    return list(dict.fromkeys(_ID_RE.findall(answer)))


def price_mentioned(answer: str, price: float) -> bool:
    """The price appears as a number: a whole price as "189", "189.00" or "189,00";
    a price with cents only with its two decimals. A price of 1000 or more also
    counts with a thousands separator ("1,799", "1.799", "1 799"), then with its
    two decimals if any ("1,799.00", "1.799,00"). Never inside a longer number."""
    whole, frac = divmod(round(price * 100), 100)
    digits = str(whole)
    number = digits
    if whole >= 1000:
        groups: list[str] = []
        while digits:
            groups.insert(0, digits[-3:])
            digits = digits[:-3]
        # Plain, or grouped by a comma, dot or (non-breaking) space.
        number = "(?:" + str(whole) + "|" + _GROUP_SEP.join(groups) + ")"
    body = rf"{number}(?:[.,]00)?" if frac == 0 else rf"{number}[.,]{frac:02d}"
    pattern = rf"(?<!\d)(?<!\d[.,]){body}(?!\d)(?![.,]\d)"
    return re.search(pattern, answer) is not None


def _is_number(v: Any) -> bool:
    return isinstance(v, int | float) and not isinstance(v, bool)


def _call_satisfies(call: Mapping[str, Any], want: Mapping[str, Any]) -> bool:
    for name, value in want.items():
        got = call.get("keywords" if name == "keywords_any" else name)
        if name == "category":
            if got != value:
                return False
        elif name == "max_price":
            if not _is_number(got) or got > value:
                return False
        elif name == "min_price":
            if not _is_number(got) or got < value:
                return False
        elif name == "in_stock_only":
            if bool(got) != value:
                return False
        elif name == "keywords_any":
            words = [_norm(k) for k in got if isinstance(k, str)] if isinstance(got, list) else []
            wanted = [_norm(w) for w in value]
            if not any(w in word for word in words for w in wanted):
                return False
    return True


def score(
    case: Case,
    answer: str,
    searches: Sequence[Mapping[str, Any]],
    catalogue: Sequence[Product],
) -> list[Check]:
    """Run the checks that apply to `case`; the case passes when all are `ok`."""
    by_id = {p.id: p for p in catalogue}
    cited = cited_ids(answer)
    checks: list[Check] = []

    unknown = [i for i in cited if i not in by_id]
    checks.append(
        Check(
            "grounded",
            not unknown,
            f"cites unknown id {', '.join(unknown)}" if unknown else "every cited id exists",
        )
    )

    # "the stated price" is read as: the catalogue price appears as a number
    # in the answer; which product it sits next to is not parsed (spec).
    unpriced = [i for i in cited if i in by_id and not price_mentioned(answer, by_id[i].price_eur)]
    checks.append(
        Check(
            "prices",
            not unpriced,
            f"price of {', '.join(unpriced)} not stated" if unpriced else "prices stated",
        )
    )

    if case.expect_ids:
        lacking = [i for i in case.expect_ids if i not in cited]
        checks.append(
            Check(
                "expected",
                not lacking,
                f"does not cite {', '.join(lacking)}" if lacking else "cites every expected id",
            )
        )
    if case.forbid_ids:
        present = [i for i in case.forbid_ids if i in cited]
        checks.append(
            Check(
                "forbidden",
                not present,
                f"cites forbidden {', '.join(present)}" if present else "cites no forbidden id",
            )
        )
    if case.must_decline:
        # Wording is not judged (no judge model): a decline is the refusal
        # text, or an answer that cites no product.
        declined = not cited or answer.strip() == REFUSAL_TEXT
        checks.append(
            Check(
                "declines",
                declined,
                "declines" if declined else f"cites {', '.join(cited)} instead of declining",
            )
        )

    flagged = "out of stock" in answer.lower()
    unflagged = [i for i in cited if i in by_id and not by_id[i].in_stock and not flagged]
    checks.append(
        Check(
            "stock",
            not unflagged,
            f"cites {', '.join(unflagged)} without saying out of stock"
            if unflagged
            else "no unflagged out-of-stock product",
        )
    )

    if case.expect_search:
        ok = any(_call_satisfies(call, case.expect_search) for call in searches)
        checks.append(
            Check(
                "search",
                ok,
                "a search call matches"
                if ok
                else f"no search_products call matches {case.expect_search} "
                f"({len(searches)} call(s))",
            )
        )
    return checks
