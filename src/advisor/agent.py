"""The agent loop: pure orchestration over a `ModelClient` and tool functions."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from advisor.catalogue import (
    CATEGORIES,
    Product,
    failed_filters,
    keyword_set,
    keywords_matched,
    named_products,
    search_products,
)
from advisor.guardrails import REFUSAL_TEXT, check_input, check_output
from advisor.models.base import (
    Message,
    ModelClient,
    ToolCall,
    ToolResult,
    ToolSpec,
)
from advisor.tracer import Tracer

MAX_TURNS = 5
FALLBACK_ANSWER = (
    "I couldn't find a good answer to that. Try asking about a product category or a price range."
)
SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "system.md"


class ToolError(Exception):
    """A tool call was invalid; the message is sent back to the model."""


@dataclass(frozen=True)
class Tool:
    spec: ToolSpec
    # Takes the model's arguments, returns a list of JSON-able results.
    run: Callable[[dict[str, Any]], list[dict[str, Any]]]


@dataclass(frozen=True)
class AgentResult:
    answer: str
    turns: int
    fallback: bool


def load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


_SEARCH_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": list(CATEGORIES)},
        "min_price": {"type": "number", "description": "Minimum price in euros."},
        "max_price": {"type": "number", "description": "Maximum price in euros."},
        "keywords": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "Words to look for in the name, brand or description. Any one keyword "
                "can match; products matching more of the keywords come first."
            ),
        },
        "in_stock_only": {"type": "boolean"},
        "limit": {"type": "integer", "description": "Maximum results, 1 to 10 (default 10)."},
    },
    "additionalProperties": False,
}


def _number(args: dict[str, Any], key: str) -> float | None:
    v = args.get(key)
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, int | float):
        raise ToolError(f"'{key}' must be a number")
    return float(v)


def _product_json(p: Product) -> dict[str, Any]:
    return {
        "id": p.id,
        "name": p.name,
        "brand": p.brand,
        "category": p.category,
        "price_eur": p.price_eur,
        "in_stock": p.in_stock,
        "specs": p.specs,
        "description": p.description,
    }


def search_tool(catalogue: Sequence[Product]) -> Tool:
    """The `search_products` tool over `catalogue`, validating the model's arguments."""

    def run(args: dict[str, Any]) -> list[dict[str, Any]]:
        unknown = set(args) - set(_SEARCH_SCHEMA["properties"])
        if unknown:
            raise ToolError(f"unknown argument(s): {', '.join(sorted(unknown))}")
        category = args.get("category")
        if category is not None and category not in CATEGORIES:
            raise ToolError(f"'category' must be one of {', '.join(CATEGORIES)}")
        keywords = args.get("keywords")
        if keywords is not None and (
            not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords)
        ):
            raise ToolError("'keywords' must be a list of strings")
        in_stock_only = args.get("in_stock_only", False)
        if not isinstance(in_stock_only, bool):
            raise ToolError("'in_stock_only' must be true or false")
        # search_products keeps its own default of 5 for its other callers; the tool
        # defaults to 10 so a ranked list is not cut before the best match shows (§22).
        limit = args.get("limit", 10)
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise ToolError("'limit' must be an integer")
        filters: dict[str, Any] = {
            "category": category,
            "min_price": _number(args, "min_price"),
            "max_price": _number(args, "max_price"),
            "in_stock_only": in_stock_only,
            "limit": limit,
        }
        words = keyword_set(keywords)
        found = search_products(catalogue, keywords=keywords, **filters)
        if not words:
            return [_product_json(p) for p in found]
        # B11: keywords that match nothing must not empty the answer; the same search
        # without them still returns rows, each marked as matching none of the keywords.
        if not found:
            found = search_products(catalogue, keywords=None, **filters)
        rows = [{**_product_json(p), "keywords_matched": keywords_matched(p, words)} for p in found]
        # §30: a product the customer named by its whole name must not vanish because the
        # category, price or stock filter drops it. It follows the filter rows, marked with
        # the filters it fails, and does not count towards `limit`.
        # Defensive: a product that fails a filter is never in `found`; kept so a row cannot repeat.
        shown = {p.id for p in found}
        for p in named_products(catalogue, keywords):
            failed = failed_filters(
                p, category, filters["min_price"], filters["max_price"], in_stock_only
            )
            if failed and p.id not in shown:
                rows.append(
                    {**_product_json(p), "keywords_matched": keywords_matched(p, words)}
                    | {"filters_failed": failed}
                )
        return rows

    spec = ToolSpec(
        name="search_products",
        description=(
            "Search the shop's product catalogue. The category, price and stock filters must "
            "all hold. Results are ordered by keywords matched, then price, cheapest first. When "
            "keywords are given, each row has keywords_matched; if no product matches any "
            "keyword, the rows for the other filters are returned with keywords_matched 0. A row "
            "with filters_failed is a product the customer named that fails the filters listed "
            "there (category, min_price, max_price, in_stock_only); say what it is and which "
            "filters it fails, and do not offer it as a fit for them."
        ),
        parameters=_SEARCH_SCHEMA,
    )
    return Tool(spec, run)


def _execute(call: ToolCall, tools: dict[str, Tool], tracer: Tracer) -> ToolResult:
    tool = tools.get(call.name)
    if tool is None:
        tracer.tool(call.name, call.arguments, [], True)
        return ToolResult(call.id, f"error: unknown tool '{call.name}'", True)
    try:
        results = tool.run(call.arguments)
    except ToolError as e:
        tracer.tool(call.name, call.arguments, [], True)
        return ToolResult(call.id, f"error: {e}", True)
    except Exception as e:  # a tool bug must not end the run; the model gets told
        tracer.tool(call.name, call.arguments, [], True)
        return ToolResult(call.id, f"error: tool failed ({type(e).__name__})", True)
    tracer.tool(call.name, call.arguments, results, False)
    return ToolResult(call.id, json.dumps(results), False)


def run_agent(
    question: str, client: ModelClient, tools: Sequence[Tool], tracer: Tracer
) -> AgentResult:
    """Ask the model, run the tools it calls, repeat until final text or MAX_TURNS."""
    system = load_system_prompt()
    by_name = {t.spec.name: t for t in tools}
    specs = [t.spec for t in tools]
    messages: list[Message] = [Message("user", question)]
    for turn in range(1, MAX_TURNS + 1):
        reply = client.complete(system, list(messages), specs)
        tracer.generation(reply.model, reply.usage, reply.text, [c.name for c in reply.tool_calls])
        if not reply.tool_calls:
            if reply.text:
                return AgentResult(reply.text, turn, False)
            continue
        messages.append(Message("assistant", reply.text or "", reply.tool_calls))
        results = tuple(_execute(c, by_name, tracer) for c in reply.tool_calls)
        messages.append(Message("user", tool_results=results))
    return AgentResult(FALLBACK_ANSWER, MAX_TURNS, True)


def answer_question(
    question: str, client: ModelClient, tools: Sequence[Tool], tracer: Tracer
) -> str:
    """The whole pipeline: input guardrail, agent, output guardrail.

    A block at either end gives the user the fixed refusal; a blocked input
    never reaches the model, and a blocked answer is discarded.
    """
    tracer.begin(question)
    verdict = check_input(question)
    tracer.check("input", verdict.allow, verdict.reason)
    if not verdict.allow:
        tracer.finish(REFUSAL_TEXT)
        return REFUSAL_TEXT
    try:
        answer = run_agent(question, client, tools, tracer).answer
    except Exception as e:
        # A failed run still closes its trace (level ERROR), then the CLI
        # reports the failure. Only the exception class and message are
        # recorded, never configuration or environment values.
        tracer.fail(f"{type(e).__name__}: {e}")
        raise
    verdict = check_output(answer)
    tracer.check("output", verdict.allow, verdict.reason)
    if not verdict.allow:
        answer = REFUSAL_TEXT
    tracer.finish(answer)
    return answer
