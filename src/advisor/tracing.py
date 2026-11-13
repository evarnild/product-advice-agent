"""Tracing of each run.

Interpretation (spec): "tracing" means Langfuse traces of each run, not
application logs. The agent and CLI record observations through the `Tracer`
protocol only; the Langfuse implementation is the only code that imports the
`langfuse` SDK.
"""

from __future__ import annotations

import json
import logging
import threading
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, TypeVar

from langfuse import Langfuse
from langfuse.api import AnnotationQueueObjectType

from advisor.evals.annotate import SCORE_NAME, AnnotationError, RunTrace, Score
from advisor.models.base import Usage
from advisor.tracer import NoopTracer, Tracer

FLUSH_TIMEOUT_SECONDS = 5.0
# Langfuse's trace-tags span attribute (LangfuseOtelSpanAttributes.TRACE_TAGS,
# a private module in SDK 5.2, so the literal is pinned here and tested).
# No cost is attached to a generation: Langfuse prices one only when its model
# name matches a price definition, and a local model's name does not.
TRACE_TAGS_ATTRIBUTE = "langfuse.trace.tags"
MAX_TRACED_RESULTS = 10
REQUIRED_ENV = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST")
log = logging.getLogger("advisor.tracing")


class LangfuseTracer:
    """Records one run as one Langfuse trace: a root span with child observations."""

    def __init__(self, client: Any, tags: Sequence[str] = ()) -> None:
        self._client = client
        self._tags = list(tags)
        self._root: Any = None

    def begin(self, question: str) -> None:
        self._root = self._client.start_observation(
            name="advisor-run", as_type="span", input=question
        )
        if self._tags:
            # Trace tags (provider:<p>, model:<m>) let runs of different
            # providers be filtered side by side in Langfuse. SDK 5.2 has no
            # update_trace, so set the trace-tags attribute on the root span.
            self._root._otel_span.set_attribute(TRACE_TAGS_ATTRIBUTE, self._tags)

    def _child(self, **kwargs: Any) -> None:
        if self._root is None:
            return
        obs = self._root.start_observation(**kwargs)
        obs.end()

    def check(self, stage: str, allowed: bool, reason: str) -> None:
        self._child(
            name=f"{stage}-check",
            as_type="guardrail",
            output={"allowed": allowed, "reason": reason},
        )

    def generation(self, model: str, usage: Usage, text: str | None, tool_names: list[str]) -> None:
        self._child(
            name="model-call",
            as_type="generation",
            model=model,
            usage_details={"input": usage.input_tokens, "output": usage.output_tokens},
            output={"text": text, "tool_calls": tool_names},
        )

    def tool(
        self, name: str, arguments: dict[str, object], results: list[dict[str, Any]], error: bool
    ) -> None:
        # The rows are what the model received, so a reviewer judges on what it
        # knew (§10 I1). The cap is the search tool's own limit; it guards a future tool.
        self._child(
            name=name,
            as_type="tool",
            input=arguments,
            output={"result_count": len(results), "results": results[:MAX_TRACED_RESULTS]},
            level="ERROR" if error else "DEFAULT",
        )

    def finish(self, answer: str) -> None:
        self._close(output=answer)

    def fail(self, error: str) -> None:
        self._close(output=error, level="ERROR")

    def _close(self, **update: Any) -> None:
        if self._root is not None:
            self._root.update(**update)
            self._root.end()
            self._root = None
        # Bounded wait: a down Langfuse must not hold the CLI for long.
        flusher = threading.Thread(target=self._client.flush, daemon=True)
        flusher.start()
        flusher.join(FLUSH_TIMEOUT_SECONDS)


class SafeTracer:
    """Wraps a tracer so no failure inside it can reach the run (spec B17)."""

    def __init__(self, inner: Tracer) -> None:
        self._inner = inner

    def _guard(self, name: str, *args: Any) -> None:
        try:
            getattr(self._inner, name)(*args)
        except Exception as e:
            log.debug("tracing %s failed: %s", name, type(e).__name__)

    def begin(self, question: str) -> None:
        self._guard("begin", question)

    def check(self, stage: str, allowed: bool, reason: str) -> None:
        self._guard("check", stage, allowed, reason)

    def generation(self, model: str, usage: Usage, text: str | None, tool_names: list[str]) -> None:
        self._guard("generation", model, usage, text, tool_names)

    def tool(
        self, name: str, arguments: dict[str, object], results: list[dict[str, Any]], error: bool
    ) -> None:
        self._guard("tool", name, arguments, results, error)

    def finish(self, answer: str) -> None:
        self._guard("finish", answer)

    def fail(self, error: str) -> None:
        self._guard("fail", error)


def make_tracer(env: Mapping[str, str], tags: Sequence[str] = ()) -> Tracer:
    """A Langfuse tracer when all three variables are set, otherwise a no-op."""
    if not all(env.get(k) for k in REQUIRED_ENV):
        log.debug("tracing off: %s not all set", ", ".join(REQUIRED_ENV))
        return NoopTracer()
    try:
        client = Langfuse(
            public_key=env["LANGFUSE_PUBLIC_KEY"],
            secret_key=env["LANGFUSE_SECRET_KEY"],
            host=env["LANGFUSE_HOST"],
        )
    except Exception as e:
        log.debug("tracing off: Langfuse client failed (%s)", type(e).__name__)
        return NoopTracer()
    return SafeTracer(LangfuseTracer(client, tags))


# --- Annotation queues (§10) -------------------------------------------------

PAGE_LIMIT = 100
OBSERVATIONS_LIMIT = 1000
CONFIG_DESCRIPTION = "pass/fail label; the critique goes in the comment"
QUEUE_DESCRIPTION = "Eval run traces to label pass/fail; imported with advisor-analysis import"
_T = TypeVar("_T")


def _utc(when: datetime) -> datetime:
    return when if when.tzinfo is not None else when.replace(tzinfo=UTC)


def _redact(text: str, secrets: Sequence[str]) -> str:
    for secret in secrets:
        if secret:
            text = text.replace(secret, "***")
    return text


class LangfuseAnnotations:
    """`Annotations` over `Langfuse(...).api` (SDK 5.2.0).

    It creates a score config, a queue and queue items, and reads queues,
    items, scores and observations. It never updates or deletes anything. Every
    SDK failure becomes an `AnnotationError` naming the step; `secrets` are
    removed from its message.
    """

    def __init__(self, api: Any, secrets: Sequence[str] = ()) -> None:
        self._api = api
        self._secrets = tuple(secrets)

    def _call(self, step: str, fn: Callable[[], _T]) -> _T:
        try:
            return fn()
        except AnnotationError:
            raise
        except Exception as e:
            raise AnnotationError(
                step, _redact(f"{type(e).__name__}: {e}", self._secrets)
            ) from None

    def _pages(self, fetch: Callable[[int], Any]) -> list[Any]:
        """Every item of a page-numbered list (page 1 up to `meta.total_pages`)."""
        found: list[Any] = []
        page = 1
        while True:
            reply = fetch(page)
            found.extend(reply.data)
            if page >= reply.meta.total_pages:
                return found
            page += 1

    def _cursor(self, fetch: Callable[[str | None], Any]) -> list[Any]:
        """Every item of a cursor-paged list."""
        found: list[Any] = []
        cursor: str | None = None
        while True:
            reply = fetch(cursor)
            found.extend(reply.data)
            cursor = reply.meta.cursor
            if not cursor:
                return found

    def ensure_score_config(self) -> str:
        def run() -> str:
            api = self._api.score_configs
            configs = self._pages(lambda page: api.get(page=page, limit=PAGE_LIMIT))
            named = [c for c in configs if c.name == SCORE_NAME]
            for found in named:
                if found.data_type == "BOOLEAN":
                    return str(found.id)
            if named:
                raise AnnotationError(
                    "config",
                    f"a score config named '{SCORE_NAME}' exists with data type "
                    f"{named[0].data_type}, not BOOLEAN; rename or archive it in Langfuse",
                )
            created = api.create(
                name=SCORE_NAME, data_type="BOOLEAN", description=CONFIG_DESCRIPTION
            )
            return str(created.id)

        return self._call("config", run)

    def _queues(self) -> list[Any]:
        api = self._api.annotation_queues
        return self._pages(lambda page: api.list_queues(page=page, limit=PAGE_LIMIT))

    def find_queue(self, name: str) -> str | None:
        def run() -> str | None:
            for found in self._queues():
                if found.name == name:
                    return str(found.id)
            return None

        return self._call("queue", run)

    def ensure_queue(self, name: str, config_id: str) -> str:
        def run() -> str:
            for found in self._queues():
                if found.name == name:
                    if config_id not in found.score_config_ids:
                        raise AnnotationError(
                            "queue",
                            f"queue '{name}' exists without the '{SCORE_NAME}' score config; "
                            "pick another name with --queue",
                        )
                    return str(found.id)
            created = self._api.annotation_queues.create_queue(
                name=name, score_config_ids=[config_id], description=QUEUE_DESCRIPTION
            )
            return str(created.id)

        return self._call("queue", run)

    def run_traces(self, stamp: str) -> list[RunTrace]:
        # The observations API is the SDK's only real-time read path (§10 I4).
        filters = json.dumps(
            [
                {
                    "type": "arrayOptions",
                    "column": "traceTags",
                    "operator": "all of",
                    "value": ["eval", f"run:{stamp}"],
                },
                {"type": "boolean", "column": "isRootObservation", "operator": "=", "value": True},
            ]
        )

        def run() -> list[RunTrace]:
            api = self._api.observations
            rows = self._cursor(
                lambda cursor: api.get_many(
                    fields="core,basic,trace_context",
                    limit=OBSERVATIONS_LIMIT,
                    cursor=cursor,
                    filter=filters,
                )
            )
            return [RunTrace(o.trace_id, tuple(o.tags or ()), _utc(o.start_time)) for o in rows]

        return self._call("traces", run)

    def queued_trace_ids(self, queue_id: str) -> set[str]:
        def run() -> set[str]:
            api = self._api.annotation_queues
            items = self._pages(
                lambda page: api.list_queue_items(queue_id=queue_id, page=page, limit=PAGE_LIMIT)
            )
            return {str(i.object_id) for i in items if i.object_type == "TRACE"}

        return self._call("items", run)

    def add_trace(self, queue_id: str, trace_id: str) -> None:
        self._call(
            "add",
            lambda: self._api.annotation_queues.create_queue_item(
                queue_id=queue_id, object_id=trace_id, object_type=AnnotationQueueObjectType.TRACE
            ),
        )

    def annotation_scores(self, queue_id: str) -> list[Score]:
        def run() -> list[Score]:
            api = self._api.scores
            rows = self._cursor(
                lambda cursor: api.get_many(
                    source="ANNOTATION",
                    queue_id=queue_id,
                    name=SCORE_NAME,
                    fields="details,subject",
                    limit=PAGE_LIMIT,
                    cursor=cursor,
                )
            )
            scores: list[Score] = []
            for row in rows:
                subject = row.subject
                if row.data_type != "BOOLEAN" or subject is None or subject.kind != "trace":
                    continue
                scores.append(
                    Score(subject.id, bool(row.value), row.comment or "", _utc(row.timestamp))
                )
            return scores

        return self._call("scores", run)


def make_annotations(env: Mapping[str, str]) -> LangfuseAnnotations:
    """The Langfuse side of `queue` and `import`; raises `AnnotationError` if not configured."""
    missing = [k for k in REQUIRED_ENV if not env.get(k)]
    if missing:
        raise AnnotationError("config", f"missing {', '.join(missing)}")
    secrets = (env["LANGFUSE_SECRET_KEY"], env["LANGFUSE_PUBLIC_KEY"])
    try:
        client = Langfuse(
            public_key=env["LANGFUSE_PUBLIC_KEY"],
            secret_key=env["LANGFUSE_SECRET_KEY"],
            host=env["LANGFUSE_HOST"],
        )
    except Exception as e:
        raise AnnotationError("config", _redact(f"{type(e).__name__}: {e}", secrets)) from None
    return LangfuseAnnotations(client.api, secrets)
