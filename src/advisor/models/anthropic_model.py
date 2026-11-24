"""Anthropic adapter: translates `ModelClient` calls to the Messages API.

The only module that imports the `anthropic` SDK.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import anthropic
from anthropic.types import (
    MessageParam,
    OutputConfigParam,
    TextBlock,
    TextBlockParam,
    ToolParam,
    ToolResultBlockParam,
    ToolUseBlock,
    ToolUseBlockParam,
)

from advisor.models.base import (
    Message,
    ModelError,
    ModelTurn,
    ToolCall,
    ToolSpec,
    Usage,
)

MAX_TOKENS = 1024


def _to_api_message(m: Message) -> MessageParam:
    if m.role == "assistant":
        blocks: list[TextBlockParam | ToolUseBlockParam] = []
        if m.text:
            blocks.append({"type": "text", "text": m.text})
        blocks.extend(
            {"type": "tool_use", "id": c.id, "name": c.name, "input": c.arguments}
            for c in m.tool_calls
        )
        return {"role": "assistant", "content": blocks}
    if m.tool_results:
        results: list[ToolResultBlockParam] = [
            {
                "type": "tool_result",
                "tool_use_id": r.call_id,
                "content": r.content,
                "is_error": r.is_error,
            }
            for r in m.tool_results
        ]
        return {"role": "user", "content": results}
    return {"role": "user", "content": m.text}


def _to_api_tool(t: ToolSpec) -> ToolParam:
    return {"name": t.name, "description": t.description, "input_schema": t.parameters}


class AnthropicClient:
    def __init__(
        self, api_key: str, model: str, sdk_client: anthropic.Anthropic | None = None
    ) -> None:
        self._model = model
        # The SDK's own spans would become separate Langfuse traces, because the
        # advisor's observations are not the current OTel context (§5). The explicit
        # option also overrides the ANTHROPIC_OPEN_TELEMETRY* variables.
        self._sdk: anthropic.Anthropic = (
            sdk_client
            if sdk_client is not None
            else anthropic.Anthropic(api_key=api_key, open_telemetry=False)
        )

    def complete(
        self,
        system: str,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec],
        *,
        schema: Mapping[str, Any] | None = None,
    ) -> ModelTurn:
        api_messages = [_to_api_message(m) for m in messages]
        api_tools = [_to_api_tool(t) for t in tools]
        try:
            if schema is None:
                response = self._sdk.messages.create(
                    model=self._model,
                    max_tokens=MAX_TOKENS,
                    system=system,
                    messages=api_messages,
                    tools=api_tools,
                )
            else:
                # I1: the provider's structured output (`output_config.format`), not a
                # forced tool. Two calls, not `omit`, so a call without a schema sends
                # exactly the keywords it always did.
                output_config: OutputConfigParam = {
                    "format": {"type": "json_schema", "schema": dict(schema)}
                }
                response = self._sdk.messages.create(
                    model=self._model,
                    max_tokens=MAX_TOKENS,
                    system=system,
                    messages=api_messages,
                    tools=api_tools,
                    output_config=output_config,
                )
        except anthropic.AnthropicError as e:
            raise ModelError(f"Anthropic call failed: {type(e).__name__}") from e
        texts: list[str] = []
        calls: list[ToolCall] = []
        for block in response.content:
            if isinstance(block, TextBlock) and block.type == "text":
                texts.append(block.text)
            elif isinstance(block, ToolUseBlock) and block.type == "tool_use":
                args = dict(block.input) if isinstance(block.input, dict) else {}
                calls.append(ToolCall(id=block.id, name=block.name, arguments=args))
        return ModelTurn(
            text="".join(texts) if texts else None,
            tool_calls=tuple(calls),
            usage=Usage(response.usage.input_tokens, response.usage.output_tokens),
            model=response.model,
        )
