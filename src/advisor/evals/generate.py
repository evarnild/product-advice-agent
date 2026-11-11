"""The question generator (§9 B2-B4): the prompt, the model calls, the coverage filter.

No file I/O here beyond reading the packaged prompt; the caller writes the
cases. The model proposes questions with a probe; `check_coverage` decides
which are kept, against the real catalogue.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from advisor.catalogue import CATEGORIES, Product
from advisor.evals.coverage import (
    QUESTIONS_PER_CELL,
    Cell,
    Probe,
    check_coverage,
    parse_probe,
)
from advisor.evals.modeljson import extract_json
from advisor.models.base import (
    Message,
    ModelClient,
    ModelError,
    ModelNotAvailableError,
    ModelUnreachableError,
)

PROMPT_PATH = Path(__file__).parent / "prompts" / "generate.md"

SCENARIO_HELP = {
    "exact-match": "the customer asks for something the shop has, with a clear category and budget",
    "several-matches": "the customer's wishes fit at least two products of the shop",
    "no-match": "the customer asks for something no product of the shop fits "
    "(a combination of words that no product description holds)",
    "budget-too-low": "the customer names a budget (max_price) below the price of every "
    "product of that category",
    "out-of-stock": "the customer asks about one named product from the out-of-stock list",
    "off-topic": "the customer asks for something that has nothing to do with electronics",
    "spelling-differs": "the customer describes a feature in other words or another spelling "
    "than the catalogue uses (for example 'noise cancelling' for 'noise-cancelling'), so the "
    "probe keywords must not appear verbatim in the question",
}


@dataclass(frozen=True)
class Candidate:
    cell: Cell
    question: str
    probe: Probe | None


@dataclass
class ScenarioStats:
    asked: int = 0
    kept: int = 0
    dropped: list[str] = field(default_factory=list)


@dataclass
class GenerateResult:
    kept: list[Candidate] = field(default_factory=list)
    stats: dict[str, ScenarioStats] = field(default_factory=dict)


def catalogue_summary(catalogue: Sequence[Product]) -> str:
    lines = []
    for category in CATEGORIES:
        prices = [p.price_eur for p in catalogue if p.category == category]
        if prices:
            lines.append(f"- {category}: {len(prices)} products, {min(prices)} to {max(prices)}")
    return "\n".join(lines)


def build_prompt(cell: Cell, catalogue: Sequence[Product], template: str | None = None) -> str:
    feature, scenario, persona = cell
    text = PROMPT_PATH.read_text(encoding="utf-8") if template is None else template
    out_of_stock = "\n".join(f"- {p.id}, {p.name}" for p in catalogue if not p.in_stock)
    fields = {
        "categories": catalogue_summary(catalogue),
        "out_of_stock": out_of_stock or "(none)",
        "count": str(QUESTIONS_PER_CELL),
        "feature": feature,
        "scenario": scenario,
        "scenario_help": SCENARIO_HELP[scenario],
        "persona": persona,
    }
    for key, value in fields.items():
        text = text.replace(f"[[{key}]]", value)
    return text


def parse_candidates(text: str, cell: Cell) -> list[Candidate] | None:
    """Candidates from a model answer, or None when the answer holds no JSON array."""
    value = extract_json(text)
    if isinstance(value, dict) and isinstance(value.get("questions"), list):
        value = value["questions"]
    if not isinstance(value, list):
        return None
    out: list[Candidate] = []
    for item in value:
        question = item.get("question") if isinstance(item, dict) else None
        if not isinstance(question, str) or not question.strip():
            out.append(Candidate(cell, "", None))
            continue
        out.append(Candidate(cell, question.strip(), parse_probe(item.get("probe"))))
    return out


def generate(
    cells: Sequence[Cell], client: ModelClient, catalogue: Sequence[Product]
) -> GenerateResult:
    """One model call per cell; keep what passes the coverage check.

    A first call that finds the model unreachable or missing raises (the caller exits 1);
    after that a failed call only counts as dropped.
    """
    template = PROMPT_PATH.read_text(encoding="utf-8")
    result = GenerateResult()
    seen: set[str] = set()
    for index, cell in enumerate(cells):
        scenario = cell[1]
        stats = result.stats.setdefault(scenario, ScenarioStats())
        stats.asked += QUESTIONS_PER_CELL
        prompt = build_prompt(cell, catalogue, template)
        try:
            reply = client.complete("", [Message("user", prompt)], [])
        except (ModelUnreachableError, ModelNotAvailableError) as e:
            if index == 0:
                raise
            stats.dropped.extend([f"model unavailable: {type(e).__name__}"] * QUESTIONS_PER_CELL)
            continue
        except ModelError as e:
            stats.dropped.extend([f"model error: {type(e).__name__}"] * QUESTIONS_PER_CELL)
            continue
        candidates = parse_candidates(reply.text or "", cell)
        if candidates is None:
            stats.dropped.extend(["unparsable model answer"] * QUESTIONS_PER_CELL)
            continue
        considered = candidates[:QUESTIONS_PER_CELL]
        missing = QUESTIONS_PER_CELL - len(considered)
        stats.dropped.extend(["missing from the model answer"] * missing)
        for cand in considered:
            if not cand.question:
                stats.dropped.append("no question text")
                continue
            if cand.question.lower() in seen:
                stats.dropped.append("duplicate question")
                continue
            ok, why = check_coverage(scenario, cand.probe, cand.question, catalogue)
            if not ok:
                stats.dropped.append(why)
                continue
            seen.add(cand.question.lower())
            stats.kept += 1
            result.kept.append(cand)
    return result


def case_lines(result: GenerateResult) -> list[dict[str, Any]]:
    """The kept candidates as §8 case objects, with ids `gen-<scenario>-<n>`."""
    counter: Counter[str] = Counter()
    lines: list[dict[str, Any]] = []
    for cand in result.kept:
        feature, scenario, persona = cand.cell
        counter[scenario] += 1
        line: dict[str, Any] = {
            "id": f"gen-{scenario}-{counter[scenario]}",
            "question": cand.question,
            "dimensions": {"feature": feature, "scenario": scenario, "persona": persona},
            "note": cand.probe.to_note() if cand.probe is not None else "off-topic: no probe",
        }
        if scenario == "off-topic":
            line["must_decline"] = True
        lines.append(line)
    return lines


def dumps_cases(lines: Sequence[dict[str, Any]]) -> str:
    return "".join(json.dumps(line, ensure_ascii=False) + "\n" for line in lines)


def summary(result: GenerateResult) -> list[str]:
    """One line per scenario: asked, kept, dropped (with the reasons counted)."""
    out = []
    for scenario, s in sorted(result.stats.items()):
        reasons = Counter(s.dropped)
        why = "; ".join(f"{n} x {r}" for r, n in sorted(reasons.items()))
        tail = f" ({why})" if why else ""
        out.append(f"{scenario}: asked {s.asked}, kept {s.kept}, dropped {len(s.dropped)}{tail}")
    return out
