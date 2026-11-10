"""A scripted fake `ModelClient` for tests (and, later, evals).

It records every request it receives so tests can assert on what the agent
actually sent, not only on what came back.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from advisor.models.base import Message, ModelTurn, ToolSpec


@dataclass(frozen=True)
class Request:
    system: str
    messages: tuple[Message, ...]
    tools: tuple[ToolSpec, ...]


class ScriptedModelClient:
    """Plays back `script` in order; an `Exception` entry is raised.

    With `repeat_last=True` the final entry is replayed forever (to model a
    model that never stops calling tools). Otherwise running out of script is
    a test bug and raises `AssertionError`.
    """

    def __init__(self, script: Sequence[ModelTurn | Exception], repeat_last: bool = False) -> None:
        self._script = list(script)
        self._repeat_last = repeat_last
        self.requests: list[Request] = []

    def complete(
        self, system: str, messages: Sequence[Message], tools: Sequence[ToolSpec]
    ) -> ModelTurn:
        self.requests.append(Request(system, tuple(messages), tuple(tools)))
        index = len(self.requests) - 1
        if index >= len(self._script):
            if not (self._repeat_last and self._script):
                raise AssertionError("ScriptedModelClient: script exhausted")
            index = len(self._script) - 1
        step = self._script[index]
        if isinstance(step, Exception):
            raise step
        return step
