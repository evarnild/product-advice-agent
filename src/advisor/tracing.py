"""Tracing of each run.

Interpretation (spec): "tracing" means Langfuse traces of each run, not
application logs. The agent and CLI record observations through the `Tracer`
protocol only; the Langfuse implementation is the only code that imports the
`langfuse` SDK.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Mapping
from typing import Any, Protocol

from langfuse import Langfuse

from advisor.models.base import Usage


class Tracer(Protocol):
    """One tracer instance records exactly one run (one trace). Never raises."""

    def begin(self, question: str) -> None: ...

    def check(self, stage: str, allowed: bool, reason: str) -> None:
        """Record a guardrail check; `stage` is 'input' or 'output'."""
        ...

    def generation(
        self, model: str, usage: Usage, text: str | None, tool_names: list[str]
    ) -> None: ...

    def tool(
        self, name: str, arguments: dict[str, object], result_count: int, error: bool
    ) -> None: ...

    def finish(self, answer: str) -> None:
        """Close the trace with the answer and flush with a bounded wait."""
        ...


class NoopTracer:
    def begin(self, question: str) -> None:
        pass

    def check(self, stage: str, allowed: bool, reason: str) -> None:
        pass

    def generation(self, model: str, usage: Usage, text: str | None, tool_names: list[str]) -> None:
        pass

    def tool(self, name: str, arguments: dict[str, object], result_count: int, error: bool) -> None:
        pass

    def finish(self, answer: str) -> None:
        pass


FLUSH_TIMEOUT_SECONDS = 5.0
REQUIRED_ENV = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST")
log = logging.getLogger("advisor.tracing")


class LangfuseTracer:
    """Records one run as one Langfuse trace: a root span with child observations."""

    def __init__(self, client: Any) -> None:
        self._client = client
        self._root: Any = None

    def begin(self, question: str) -> None:
        self._root = self._client.start_observation(
            name="advisor-run", as_type="span", input=question
        )

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

    def tool(self, name: str, arguments: dict[str, object], result_count: int, error: bool) -> None:
        self._child(
            name=name,
            as_type="tool",
            input=arguments,
            output={"result_count": result_count},
            level="ERROR" if error else "DEFAULT",
        )

    def finish(self, answer: str) -> None:
        if self._root is not None:
            self._root.update(output=answer)
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

    def tool(self, name: str, arguments: dict[str, object], result_count: int, error: bool) -> None:
        self._guard("tool", name, arguments, result_count, error)

    def finish(self, answer: str) -> None:
        self._guard("finish", answer)


def make_tracer(env: Mapping[str, str]) -> Tracer:
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
    return SafeTracer(LangfuseTracer(client))
