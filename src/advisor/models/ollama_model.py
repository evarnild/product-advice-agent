"""Ollama adapter: translates `ModelClient` calls to Ollama's native `/api/chat`.

The only module that imports `httpx`. It is written by hand over the native
API, not the `ollama` package and not the OpenAI-compatible `/v1` endpoint:
the native API reports token counts and takes `think` and `num_ctx` directly,
and 0001 keeps the seam provider-agnostic without a third-party abstraction.

Error mapping (the user-facing surface, spec B10-B12): only two failures get
their own message. A connection that cannot be made is
`ModelUnreachableError` (start Ollama); an HTTP 404 is
`ModelNotAvailableError` (pull the model). Every other failure, including a
read timeout, a non-2xx status and a malformed body, is a plain `ModelError`,
which the CLI shows as the generic "unavailable" message.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any
from urllib.parse import urlsplit

import httpx

from advisor.models.base import (
    Message,
    ModelError,
    ModelNotAvailableError,
    ModelTurn,
    ModelUnreachableError,
    ToolCall,
    ToolSpec,
    Usage,
)

DEFAULT_BASE_URL = "http://localhost:11434"
NUM_CTX = 8192
CALL_TIMEOUT_SECONDS = 180.0
CONNECT_TIMEOUT_SECONDS = 10.0


def _display_url(base_url: str) -> str:
    """The URL without any user or password part, safe to print."""
    parts = urlsplit(base_url)
    host = parts.hostname or ""
    if ":" in host:
        host = f"[{host}]"
    if parts.port is not None:
        host = f"{host}:{parts.port}"
    return f"{parts.scheme}://{host}{parts.path.rstrip('/')}"


def _to_api_tool(t: ToolSpec) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {"name": t.name, "description": t.description, "parameters": t.parameters},
    }


def _to_api_messages(system: str, messages: Sequence[Message]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = [{"role": "system", "content": system}]
    names: dict[str, str] = {}  # call id -> tool name, for the tool-result messages
    for m in messages:
        if m.role == "assistant":
            msg: dict[str, Any] = {"role": "assistant", "content": m.text}
            if m.tool_calls:
                msg["tool_calls"] = [
                    {"function": {"name": c.name, "arguments": c.arguments}} for c in m.tool_calls
                ]
                names.update({c.id: c.name for c in m.tool_calls})
            out.append(msg)
        elif m.tool_results:
            out.extend(
                {"role": "tool", "content": r.content, "tool_name": names.get(r.call_id, "")}
                for r in m.tool_results
            )
        else:
            out.append({"role": "user", "content": m.text})
    return out


def _arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except ValueError:
            parsed = None
        if isinstance(parsed, dict):
            return parsed
    # The agent's "unknown argument(s)" check answers the model with an error.
    return {"_unparsable_arguments": raw}


class OllamaClient:
    def __init__(
        self,
        model: str,
        base_url: str = DEFAULT_BASE_URL,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._counter = 0  # one client per run, so ids are unique within the run
        self._http = httpx.Client(
            transport=transport,
            timeout=httpx.Timeout(CALL_TIMEOUT_SECONDS, connect=CONNECT_TIMEOUT_SECONDS),
        )

    def complete(
        self, system: str, messages: Sequence[Message], tools: Sequence[ToolSpec]
    ) -> ModelTurn:
        body = {
            "model": self._model,
            "messages": _to_api_messages(system, messages),
            "tools": [_to_api_tool(t) for t in tools],
            "stream": False,
            "think": False,
            "options": {"num_ctx": NUM_CTX},
        }
        try:
            response = self._http.post(f"{self._base_url}/api/chat", json=body)
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            raise ModelUnreachableError(
                f"Ollama is not reachable at {_display_url(self._base_url)}. "
                'Start Ollama (the Ollama app, or "ollama serve") and try again.'
            ) from e
        except httpx.HTTPError as e:
            raise ModelError(f"Ollama call failed: {type(e).__name__}") from e
        if response.status_code == 404:
            raise ModelNotAvailableError(
                f"Model '{self._model}' is not available in Ollama. Run: ollama pull {self._model}"
            )
        if not response.is_success:
            raise ModelError(f"Ollama returned HTTP {response.status_code}")
        try:
            data = response.json()
            message = data["message"]
            content = message.get("content")
            raw_calls = message.get("tool_calls") or []
            calls: list[ToolCall] = []
            for raw in raw_calls:
                fn = raw["function"]
                self._counter += 1
                calls.append(
                    ToolCall(
                        id=f"call_{self._counter}",
                        name=fn["name"],
                        arguments=_arguments(fn.get("arguments")),
                    )
                )
            return ModelTurn(
                text=content if isinstance(content, str) and content.strip() else None,
                tool_calls=tuple(calls),
                usage=Usage(
                    int(data.get("prompt_eval_count") or 0), int(data.get("eval_count") or 0)
                ),
                model=str(data.get("model") or self._model),
            )
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            raise ModelError(f"Ollama returned a malformed response: {type(e).__name__}") from e
