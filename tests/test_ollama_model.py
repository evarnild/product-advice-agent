"""The Ollama adapter, driven only through httpx.MockTransport (no socket)."""

import json
import subprocess
import sys

import httpx
import pytest

from advisor.models.base import (
    Message,
    ModelError,
    ModelNotAvailableError,
    ModelUnreachableError,
    ToolResult,
    ToolSpec,
)
from advisor.models.ollama_model import OllamaClient

BASE = "http://localhost:11434"
TOOL = ToolSpec(
    "search_products",
    "Search the catalogue.",
    {"type": "object", "properties": {"category": {"type": "string"}}},
)


class Server:
    """A fake transport that records each request's JSON body and replays responses."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests: list[httpx.Request] = []
        self.bodies: list[dict] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        self.bodies.append(json.loads(request.content))
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def client(self, base_url=BASE, model="qwen3:8b"):
        return OllamaClient(model, base_url, transport=httpx.MockTransport(self))


def ok(message, **extra):
    body = {"model": "qwen3:8b-served", "message": {"role": "assistant", **message}, **extra}
    return httpx.Response(200, json=body)


def test_request_shape():
    server = Server(ok({"content": "hi"}))
    server.client().complete("SYSTEM PROMPT", [Message("user", "I want a phone")], [TOOL])
    assert len(server.requests) == 1
    req = server.requests[0]
    assert req.method == "POST"
    assert str(req.url) == f"{BASE}/api/chat"
    assert server.bodies[0] == {
        "model": "qwen3:8b",
        "messages": [
            {"role": "system", "content": "SYSTEM PROMPT"},
            {"role": "user", "content": "I want a phone"},
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "search_products",
                    "description": "Search the catalogue.",
                    "parameters": TOOL.parameters,
                },
            }
        ],
        "stream": False,
        "think": False,
        "options": {"num_ctx": 8192},
    }


def test_tool_calls_get_distinct_ids_and_usage_and_served_model():
    server = Server(
        ok(
            {
                "content": "",
                "tool_calls": [
                    {"function": {"name": "search_products", "arguments": {"category": "phone"}}},
                    {"function": {"name": "other_tool", "arguments": {"x": 1}}},
                ],
            },
            prompt_eval_count=123,
            eval_count=45,
        )
    )
    turn = server.client().complete("s", [Message("user", "q")], [TOOL])
    assert turn.text is None
    assert [(c.name, c.arguments) for c in turn.tool_calls] == [
        ("search_products", {"category": "phone"}),
        ("other_tool", {"x": 1}),
    ]
    assert len({c.id for c in turn.tool_calls}) == 2
    assert (turn.usage.input_tokens, turn.usage.output_tokens) == (123, 45)
    assert turn.model == "qwen3:8b-served"


def test_ids_stay_unique_across_turns():
    call = {"function": {"name": "search_products", "arguments": {}}}
    server = Server(ok({"tool_calls": [call]}), ok({"tool_calls": [call]}))
    client = server.client()
    a = client.complete("s", [Message("user", "q")], [TOOL])
    b = client.complete("s", [Message("user", "q")], [TOOL])
    assert a.tool_calls[0].id != b.tool_calls[0].id


def test_text_response_missing_counts_and_model_fall_back():
    server = Server(
        httpx.Response(200, json={"message": {"role": "assistant", "content": "Hello"}})
    )
    turn = server.client(model="cfg").complete("s", [], [])
    assert turn.text == "Hello"
    assert turn.tool_calls == ()
    assert (turn.usage.input_tokens, turn.usage.output_tokens) == (0, 0)
    assert turn.model == "cfg"


def test_blank_content_is_no_text():
    server = Server(ok({"content": "  \n"}))
    assert server.client().complete("s", [], []).text is None


def test_tool_results_go_back_with_the_calls_tool_name():
    call_turn = ok(
        {
            "tool_calls": [
                {"function": {"name": "search_products", "arguments": {"category": "phone"}}},
                {"function": {"name": "other_tool", "arguments": {}}},
            ]
        }
    )
    server = Server(call_turn, ok({"content": "done"}))
    client = server.client()
    first = client.complete("s", [Message("user", "q")], [TOOL])
    c1, c2 = first.tool_calls
    history = [
        Message("user", "q"),
        Message("assistant", "thinking", first.tool_calls),
        # Results deliberately in the opposite order to the calls.
        Message("user", tool_results=(ToolResult(c2.id, "R2", True), ToolResult(c1.id, "R1"))),
    ]
    client.complete("s", history, [TOOL])
    assert server.bodies[1]["messages"][1:] == [
        {"role": "user", "content": "q"},
        {
            "role": "assistant",
            "content": "thinking",
            "tool_calls": [
                {"function": {"name": "search_products", "arguments": {"category": "phone"}}},
                {"function": {"name": "other_tool", "arguments": {}}},
            ],
        },
        {"role": "tool", "content": "R2", "tool_name": "other_tool"},
        {"role": "tool", "content": "R1", "tool_name": "search_products"},
    ]


def test_json_string_arguments_are_parsed():
    server = Server(
        ok({"tool_calls": [{"function": {"name": "t", "arguments": '{"category":"phone"}'}}]})
    )
    turn = server.client().complete("s", [], [])
    assert turn.tool_calls[0].arguments == {"category": "phone"}


@pytest.mark.parametrize("raw", ["not json", "[1, 2]", "3", None, 7])
def test_unparsable_arguments_are_kept_under_a_marker_key(raw):
    server = Server(ok({"tool_calls": [{"function": {"name": "t", "arguments": raw}}]}))
    turn = server.client().complete("s", [], [])
    assert turn.tool_calls[0].arguments == {"_unparsable_arguments": raw}


def test_call_timeout_is_180s_with_short_connect():
    timeout = Server().client()._http.timeout
    assert timeout.read == 180.0
    assert timeout.connect == 10.0


def test_read_timeout_is_a_plain_model_error():
    server = Server(httpx.ReadTimeout("slow"))
    with pytest.raises(ModelError) as e:
        server.client().complete("s", [], [])
    assert not isinstance(e.value, ModelUnreachableError | ModelNotAvailableError)


@pytest.mark.parametrize("exc", [httpx.ConnectError("refused"), httpx.ConnectTimeout("slow")])
def test_connect_failures_say_to_start_ollama(exc):
    with pytest.raises(ModelUnreachableError) as e:
        Server(exc).client().complete("s", [], [])
    assert str(e.value) == (
        "Ollama is not reachable at http://localhost:11434. "
        'Start Ollama (the Ollama app, or "ollama serve") and try again.'
    )


def test_credentials_are_stripped_from_the_printed_url():
    with pytest.raises(ModelUnreachableError) as e:
        Server(httpx.ConnectError("x")).client("http://usr:pw@host:1").complete("s", [], [])
    text = str(e.value)
    assert "http://host:1." in text
    assert "usr" not in text and "pw" not in text


def test_ipv6_host_keeps_its_brackets_in_the_message():
    with pytest.raises(ModelUnreachableError) as e:
        Server(httpx.ConnectError("x")).client("http://[::1]:11434").complete("s", [], [])
    assert "http://[::1]:11434." in str(e.value)


def test_404_says_to_pull_the_model():
    server = Server(httpx.Response(404, json={"error": "model 'x' not found"}))
    with pytest.raises(ModelNotAvailableError) as e:
        server.client(model="x").complete("s", [], [])
    assert str(e.value) == "Model 'x' is not available in Ollama. Run: ollama pull x"


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(500, json={"error": "boom"}),
        httpx.Response(400, json={"message": {"role": "assistant", "content": "x"}}),
        httpx.Response(200, content=b"<html>not json</html>"),
        httpx.Response(200, json={"model": "m"}),
        httpx.Response(200, json=[1]),
        httpx.Response(200, json={"message": {"tool_calls": [{"nofunction": 1}]}}),
    ],
)
def test_other_failures_are_plain_model_errors(response):
    with pytest.raises(ModelError) as e:
        Server(response).client().complete("s", [], [])
    assert not isinstance(e.value, ModelUnreachableError | ModelNotAvailableError)


def test_every_request_goes_to_the_configured_host():
    server = Server(ok({"content": "a"}), ok({"content": "b"}))
    client = server.client("http://box.test:9/")
    client.complete("s", [], [])
    client.complete("s", [], [])
    assert {(r.url.host, r.url.port, r.url.path) for r in server.requests} == {
        ("box.test", 9, "/api/chat")
    }


def test_ollama_provider_does_not_import_anthropic():
    code = (
        "import sys; import advisor.cli; from advisor.models import make_client; "
        "make_client('ollama', 'm'); assert 'anthropic' not in sys.modules"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
