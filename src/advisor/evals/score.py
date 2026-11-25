"""Deterministic scorers for an advisor answer. Pure: no files, no model."""

from __future__ import annotations

import difflib
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from advisor.catalogue import Product, _norm, fold
from advisor.evals.cases import Case, fits
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


_WINDOW = 80


def misnamed(answer: str, by_id: Mapping[str, Product]) -> list[tuple[str, str, list[str]]]:
    """Cited known ids written next to another product's name.

    For each occurrence of a known id, the window is up to 80 characters on
    each side, on the same line, never past the previous or next id, nor
    past a name that sits right before the next id (it belongs to that id). The
    occurrence is a mismatch when the window names another catalogue product
    and not the cited one. Names match case-insensitively with a hyphen read
    as a space, as whole names, the longer name winning on overlap. Returns
    `(id, own name, other names)`, once per id, in order of first occurrence.
    """
    ids = [(m.start(), m.end(), m.group()) for m in _ID_RE.finditer(answer)]
    if not ids:
        return []
    # Fold case and hyphens one character at a time so positions stay put: a
    # character whose lower() is longer than one character is kept as it is.
    text = "".join(_norm(c) if len(c.lower()) == 1 else c for c in answer)
    names = sorted(
        {_norm(p.name): p.name for p in by_id.values()}.items(), key=lambda kv: -len(kv[0])
    )
    pattern = re.compile(
        r"(?<![a-z0-9])(?:" + "|".join(re.escape(n) for n, _ in names) + r")(?![a-z0-9])"
    )
    shown = dict(names)
    mentions = [(m.start(), m.end(), m.group()) for m in pattern.finditer(text)]
    out: list[tuple[str, str, list[str]]] = []
    seen: set[str] = set()
    for k, (start, end, pid) in enumerate(ids):
        if pid not in by_id or pid in seen:
            continue
        lo = max(start - _WINDOW, answer.rfind("\n", 0, start) + 1)
        nl = answer.find("\n", end)
        hi = min(end + _WINDOW, len(answer) if nl < 0 else nl)
        if k > 0:
            lo = max(lo, ids[k - 1][1])
        if k + 1 < len(ids):
            hi = min(hi, ids[k + 1][0])
            # A name right before the next id (only space and "(" between) is
            # that id's own: it does not count here.
            for a, b, _ in mentions:
                if (
                    a >= end
                    and b <= ids[k + 1][0]
                    and re.fullmatch(r"\s*\(?", text[b : ids[k + 1][0]])
                ):
                    hi = min(hi, a)
        near = [shown[n] for a, b, n in mentions if a >= lo and b <= hi]
        own = _norm(by_id[pid].name)
        if near and own not in {_norm(n) for n in near}:
            seen.add(pid)
            out.append((pid, by_id[pid].name, list(dict.fromkeys(near))))
    return out


# The name slot (§35): the capitalised words right before a cited id are the
# name the answer gives it. Names with no id beside them are not read.
_SIMILARITY = 0.85
_MAX_SLOT = 5
_SLOT_TRAIL = " \t([*\"'“”‘’"
_WORD_LEAD = "*([_\"'“‘"


def _slot_run(segment: str) -> list[str]:
    """The name words at the end of `segment` (text before an id, one line)."""
    words = segment.rstrip(_SLOT_TRAIL).split()
    taken: list[str] = []
    for raw in reversed(words):
        word = raw.rstrip("*\"'”’")
        # A word not ending in a letter or digit ("GPS.", "Price:", "](") ends the run.
        if not word or not word[-1].isalnum():
            break
        head = word.lstrip(_WORD_LEAD)
        if not head or not (head[0].isupper() or head[0].isdigit()):
            break
        taken.append(word.lstrip(_WORD_LEAD))
        if len(taken) == _MAX_SLOT:
            break
    taken.reverse()
    if len(taken) > 1 and taken[0].lower() in {"the", "a", "an"}:
        taken.pop(0)
    if len(taken) > 1 and taken[0].isdigit():
        taken.pop(0)
    return taken


def invented_names(answer: str, by_id: Mapping[str, Product]) -> list[tuple[str, str, str]]:
    """Cited known ids written under a name the catalogue does not have (§35).

    For each occurrence of a known id the name slot is the run of up to five
    words, each starting with a capital letter or a digit, directly before it
    on the same line (only spaces, `(`, bold marks and quotes between), after
    any lead-in word, list number or sentence break, and never reaching back
    past another id. A word that does not end in a letter or digit ("GPS.",
    "Price:", a name ending in `)`, `+`, `%` or `-`) ends the run.
    The occurrence is fine when the run is shorter than two words, is a whole
    catalogue name, is the cited product's own name, a tail of it in whole
    words, or ends in it in whole words (a capitalised lead-in such as
    "Recommend Auralis Home 1"), or is a near spelling of the cited name with
    the same numbers (similarity at least `_SIMILARITY`). Otherwise it is
    invented. Returns `(id, own name, run as written)`, once per id, in order
    of first occurrence. Pure: no question, no model.
    """
    names = {_norm(p.name) for p in by_id.values()}
    ids = list(_ID_RE.finditer(answer))
    out: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for k, m in enumerate(ids):
        pid = m.group()
        if pid not in by_id or pid in seen:
            continue
        lo = answer.rfind("\n", 0, m.start()) + 1
        if k > 0:
            lo = max(lo, ids[k - 1].end())
        words = _slot_run(answer[lo : m.start()])
        if len(words) < 2:
            continue
        run = " ".join(words)
        shown, own = _norm(run), _norm(by_id[pid].name)
        if shown in names or shown == own or own.endswith(" " + shown) or shown.endswith(" " + own):
            continue
        digits = re.findall(r"\d+", run) == re.findall(r"\d+", by_id[pid].name)
        if digits and difflib.SequenceMatcher(None, shown, own).ratio() >= _SIMILARITY:
            continue
        seen.add(pid)
        out.append((pid, by_id[pid].name, run))
    return out


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


def says_out_of_stock(answer: str) -> bool:
    """The answer flags stock: it contains "out of stock", any case. Shared by
    the stock check and the prices exemption so the two cannot drift apart."""
    return "out of stock" in answer.lower()


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
            words = [fold(k) for k in got if isinstance(k, str)] if isinstance(got, list) else []
            wanted = [fold(w) for w in value]
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

    wrong = misnamed(answer, by_id)
    checks.append(
        Check(
            "names",
            not wrong,
            "; ".join(f"{i} is the {own}, cited as {', '.join(got)}" for i, own, got in wrong)
            if wrong
            else "every cited id sits with its own name or none",
        )
    )

    made_up = invented_names(answer, by_id)
    checks.append(
        Check(
            "invented",
            not made_up,
            "; ".join(f"{i} is the {own}, cited as {run}" for i, own, run in made_up)
            if made_up
            else "no invented product name next to a cited id",
        )
    )

    # "the stated price" is read as: the catalogue price appears as a number
    # in the answer; which product it sits next to is not parsed (spec). A
    # cited out-of-stock product is exempt when the answer says "out of stock"
    # (the stock check's own test): such an answer need not quote its price.
    flagged = says_out_of_stock(answer)
    unpriced = [
        i
        for i in cited
        if i in by_id
        and not (flagged and not by_id[i].in_stock)
        and not price_mentioned(answer, by_id[i].price_eur)
    ]
    checks.append(
        Check(
            "prices",
            not unpriced,
            f"price of {', '.join(f'{i} ({by_id[i].name})' for i in unpriced)} not stated"
            if unpriced
            else "prices stated",
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
    # Cited ids that are not in the catalogue are left to `grounded`.
    existing = [by_id[i] for i in cited if i in by_id]
    if "cites_a_match" in case.expect_properties:
        matching = [p.id for p in existing if fits(p, case.expect_search)]
        checks.append(
            Check(
                "a-match",
                bool(matching),
                f"cites a fitting product ({', '.join(matching)})"
                if matching
                else f"none of the cited products fits ({', '.join(p.id for p in existing)})"
                if existing
                else "cites no product",
            )
        )
    if "cites_only_matches" in case.expect_properties:
        misfits = [p.id for p in existing if not fits(p, case.expect_search)]
        checks.append(
            Check(
                "only-matches",
                not misfits,
                f"cites {', '.join(misfits)} which do not fit"
                if misfits
                else "every cited product fits",
            )
        )
    return checks
