from types import SimpleNamespace

import anthropic
import httpx
import pytest

from advisor.models import KNOWN_PROVIDERS, UnknownProviderError, make_client
from advisor.models.anthropic import AnthropicClient
from advisor.models.base import Message, ModelError, ModelTurn, ToolCall, ToolResult, ToolSpec
from advisor.models.fake import ScriptedModelClient

TOOL = ToolSpec("search_products", "Search.", {"type": "object", "properties": {}})


def test_make_client_unknown_provider_lists_known():
    with pytest.raises(UnknownProviderError) as e:
        make_client("nope", "m", "k")
    assert "nope" in str(e.value)
    for p in KNOWN_PROVIDERS:
        assert p in str(e.value)


def test_make_client_anthropic_does_not_connect():
    client = make_client("anthropic", "some-model", "placeholder-key")
    assert isinstance(client, AnthropicClient)


def test_fake_records_requests_and_plays_script():
    t1 = ModelTurn(text="a")
    t2 = ModelTurn(text="b")
    fake = ScriptedModelClient([t1, t2])
    assert fake.complete("s", [Message("user", "q")], [TOOL]) is t1
    assert fake.complete("s2", [], []) is t2
    assert [r.system for r in fake.requests] == ["s", "s2"]
    assert fake.requests[0].messages == (Message("user", "q"),)
    assert fake.requests[0].tools == (TOOL,)
    with pytest.raises(AssertionError):
        fake.complete("s", [], [])


def test_fake_raises_exceptions_and_repeats_last():
    fake = ScriptedModelClient([ModelTurn(text="x"), RuntimeError("boom")], repeat_last=True)
    fake.complete("s", [], [])
    for _ in range(2):
        with pytest.raises(RuntimeError):
            fake.complete("s", [], [])


class FakeSdk:
    def __init__(self, response=None, error=None):
        self.calls = []
        self._response = response
        self._error = error
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self._error:
            raise self._error
        return self._response


def _response(content, model="m-1", usage=(11, 7)):
    return SimpleNamespace(
        content=content,
        model=model,
        usage=SimpleNamespace(input_tokens=usage[0], output_tokens=usage[1]),
    )


def test_adapter_maps_tool_use_and_usage():
    sdk = FakeSdk(
        _response(
            [
                SimpleNamespace(type="text", text="Let me look."),
                SimpleNamespace(
                    type="tool_use", id="tu_1", name="search_products", input={"category": "phone"}
                ),
            ]
        )
    )
    turn = AnthropicClient("k", "m-1", sdk_client=sdk).complete(
        "sys", [Message("user", "q")], [TOOL]
    )
    assert turn.text == "Let me look."
    assert turn.tool_calls == (ToolCall("tu_1", "search_products", {"category": "phone"}),)
    assert (turn.usage.input_tokens, turn.usage.output_tokens) == (11, 7)
    assert turn.model == "m-1"
    sent = sdk.calls[0]
    assert sent["model"] == "m-1"
    assert sent["system"] == "sys"
    assert sent["messages"] == [{"role": "user", "content": "q"}]
    assert sent["tools"] == [
        {"name": "search_products", "description": "Search.", "input_schema": TOOL.parameters}
    ]


def test_adapter_maps_text_only_response():
    sdk = FakeSdk(_response([SimpleNamespace(type="text", text="Hello")]))
    turn = AnthropicClient("k", "m", sdk_client=sdk).complete("s", [], [])
    assert turn.text == "Hello"
    assert turn.tool_calls == ()


def test_adapter_translates_tool_round_trip_messages():
    sdk = FakeSdk(_response([SimpleNamespace(type="text", text="ok")]))
    history = [
        Message("user", "q"),
        Message("assistant", "hm", (ToolCall("tu_1", "search_products", {"a": 1}),)),
        Message("user", tool_results=(ToolResult("tu_1", "[]"), ToolResult("tu_2", "bad", True))),
    ]
    AnthropicClient("k", "m", sdk_client=sdk).complete("s", history, [])
    assert sdk.calls[0]["messages"] == [
        {"role": "user", "content": "q"},
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "hm"},
                {"type": "tool_use", "id": "tu_1", "name": "search_products", "input": {"a": 1}},
            ],
        },
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "tu_1", "content": "[]", "is_error": False},
                {"type": "tool_result", "tool_use_id": "tu_2", "content": "bad", "is_error": True},
            ],
        },
    ]


def test_adapter_wraps_sdk_errors():
    err = anthropic.APIConnectionError(request=httpx.Request("POST", "https://example.invalid"))
    with pytest.raises(ModelError):
        AnthropicClient("k", "m", sdk_client=FakeSdk(error=err)).complete("s", [], [])


def test_adapter_assistant_with_empty_text_sends_no_text_block():
    sdk = FakeSdk(_response([SimpleNamespace(type="text", text="ok")]))
    history = [
        Message("user", "q"),
        Message("assistant", "", (ToolCall("tu_1", "search_products", {}),)),
        Message("user", tool_results=(ToolResult("tu_1", "[]"),)),
    ]
    AnthropicClient("k", "m", sdk_client=sdk).complete("s", history, [])
    assert sdk.calls[0]["messages"][1] == {
        "role": "assistant",
        "content": [{"type": "tool_use", "id": "tu_1", "name": "search_products", "input": {}}],
    }


def test_adapter_reports_the_model_the_response_names():
    sdk = FakeSdk(_response([SimpleNamespace(type="text", text="hi")], model="served-model-9"))
    turn = AnthropicClient("k", "configured-model", sdk_client=sdk).complete("s", [], [])
    assert sdk.calls[0]["model"] == "configured-model"
    assert turn.model == "served-model-9"
