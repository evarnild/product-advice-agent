"""The provider-agnostic model interface.

Interpretation (spec, "Interpretations"): "provider-agnostic" means this
internal `ModelClient` protocol with one shipped adapter (Anthropic) plus a
scripted fake, not a third-party abstraction such as LiteLLM and not two
adapters in the first skeleton. The fake proves the seam; a second adapter is
a small later intent. Nothing outside `advisor.models` imports a provider SDK.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol


class ModelError(Exception):
    """A model call failed (provider error, network failure, bad response)."""


class ModelUnreachableError(ModelError):
    """The model server cannot be reached; `str(e)` is a ready user-facing message."""


class ModelNotAvailableError(ModelError):
    """The server is up but lacks the model; `str(e)` is a ready user-facing message."""


@dataclass(frozen=True)
class ToolSpec:
    """A tool the model may call; `parameters` is a JSON Schema object."""

    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    call_id: str
    content: str
    is_error: bool = False


@dataclass(frozen=True)
class Message:
    """One conversation message.

    A user message carries `text` or `tool_results` (answers to the previous
    assistant turn's calls); an assistant message carries `text` and/or
    `tool_calls`.
    """

    role: Literal["user", "assistant"]
    text: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    tool_results: tuple[ToolResult, ...] = ()


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True)
class ModelTurn:
    """One model response: final text, or tool calls (possibly with text)."""

    text: str | None = None
    tool_calls: tuple[ToolCall, ...] = ()
    usage: Usage = field(default_factory=Usage)
    model: str = ""


class ModelClient(Protocol):
    def complete(
        self, system: str, messages: Sequence[Message], tools: Sequence[ToolSpec]
    ) -> ModelTurn:
        """Return the model's next turn for this conversation."""
        ...
