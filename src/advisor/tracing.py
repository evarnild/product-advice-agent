"""Tracing of each run.

Interpretation (spec): "tracing" means Langfuse traces of each run, not
application logs. The agent and CLI record observations through the `Tracer`
protocol only; the Langfuse implementation is the only code that imports the
`langfuse` SDK.
"""

from __future__ import annotations

from typing import Protocol

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
