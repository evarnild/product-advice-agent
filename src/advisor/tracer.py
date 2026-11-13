"""The `Tracer` protocol and the no-op tracer.

SDK-free on purpose: the pure modules (`agent`) import it, and importing them
must not load `langfuse` or `opentelemetry`. The Langfuse implementation, the
safety wrapper and `make_tracer` live in `advisor.tracing`.
"""

from __future__ import annotations

from typing import Any, Protocol

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
        self, name: str, arguments: dict[str, object], results: list[dict[str, Any]], error: bool
    ) -> None:
        """A tool call: the rows the tool returned (empty on an error call)."""
        ...

    def finish(self, answer: str) -> None:
        """Close the trace with the answer and flush with a bounded wait."""
        ...

    def fail(self, error: str) -> None:
        """Close the trace of a failed run (level ERROR) and flush with a bounded wait."""
        ...


class NoopTracer:
    def begin(self, question: str) -> None:
        pass

    def check(self, stage: str, allowed: bool, reason: str) -> None:
        pass

    def generation(self, model: str, usage: Usage, text: str | None, tool_names: list[str]) -> None:
        pass

    def tool(
        self, name: str, arguments: dict[str, object], results: list[dict[str, Any]], error: bool
    ) -> None:
        pass

    def finish(self, answer: str) -> None:
        pass

    def fail(self, error: str) -> None:
        pass
