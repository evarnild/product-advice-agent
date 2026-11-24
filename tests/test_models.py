from types import SimpleNamespace

import anthropic
import httpx
import pytest
from anthropic.types import Message as SdkMessage
from anthropic.types import TextBlock, ToolUseBlock
from anthropic.types import Usage as SdkUsage

from advisor.models import KNOWN_PROVIDERS, UnknownProviderError, make_client
from advisor.models.anthropic_model import MAX_TOKENS, AnthropicClient
from advisor.models.base import (
    Message,
    ModelError,
    ModelNotAvailableError,
    ModelTurn,
    ModelUnreachableError,
    ToolCall,
    ToolResult,
    ToolSpec,
)
from advisor.models.fake import ScriptedModelClient

TOOL = ToolSpec("search_products", "Search.", {"type": "object", "properties": {}})


def test_make_client_unknown_provider_lists_known():
    with pytest.raises(UnknownProviderError) as e:
        make_client("nope", "m")
    assert "nope" in str(e.value)
    for p in KNOWN_PROVIDERS:
        assert p in str(e.value)


def test_make_client_anthropic_does_not_connect():
    client = make_client("anthropic", "some-model", api_key="placeholder-key")
    assert isinstance(client, AnthropicClient)


def test_anthropic_adapter_turns_off_sdk_tracing(monkeypatch):
    seen: dict[str, object] = {}

    def recorder(**kwargs: object) -> object:
        seen.update(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr(anthropic, "Anthropic", recorder)
    AnthropicClient(api_key="placeholder-key", model="m")
    assert seen["open_telemetry"] is False
    assert seen["api_key"] == "placeholder-key"


def test_sdk_tracing_stays_off_even_if_the_environment_enables_it(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_OPEN_TELEMETRY", "true")
    client = make_client("anthropic", "m", api_key="placeholder-key")
    # `_open_telemetry` is private to anthropic 2.6.0; a rename fails loudly here.
    assert client._sdk._open_telemetry["traces"]["enabled"] is False  # type: ignore[attr-defined]


def test_make_client_ollama_is_keyless_and_does_not_connect():
    from advisor.models.ollama_model import OllamaClient

    assert isinstance(make_client("ollama", "qwen3:8b"), OllamaClient)


def test_make_client_ollama_passes_model_and_base_url_through():
    client = make_client("ollama", "m-x", base_url="http://box:9/")
    assert client._model == "m-x"
    assert client._base_url == "http://box:9"


def test_make_client_ollama_defaults_the_base_url():
    client = make_client("ollama", "m")
    assert client._model == "m"
    assert client._base_url == "http://localhost:11434"


def test_make_client_anthropic_passes_the_key_to_the_sdk():
    client = make_client("anthropic", "m", api_key="placeholder-key")
    assert client._sdk.api_key == "placeholder-key"
    assert client._model == "m"


def test_ollama_error_types_are_model_errors():
    assert issubclass(ModelUnreachableError, ModelError)
    assert issubclass(ModelNotAvailableError, ModelError)


def test_known_providers_lists_both():
    assert set(KNOWN_PROVIDERS) == {"ollama", "anthropic"}


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


def test_fake_records_the_schema_it_was_given():
    fake = ScriptedModelClient([ModelTurn(text="a"), ModelTurn(text="b")])
    fake.complete("s", [], [], schema={"type": "object"})
    fake.complete("s", [], [])
    assert [r.schema for r in fake.requests] == [{"type": "object"}, None]


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


def _response(content, model="m-1", usage=(11, 7), stop_reason="end_turn"):
    return SdkMessage(
        id="msg_1",
        type="message",
        role="assistant",
        model=model,
        stop_reason=stop_reason,
        stop_sequence=None,
        content=content,
        usage=SdkUsage(input_tokens=usage[0], output_tokens=usage[1]),
    )


def test_adapter_maps_tool_use_and_usage():
    sdk = FakeSdk(
        _response(
            [
                TextBlock(type="text", text="Let me look."),
                ToolUseBlock(
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


SCHEMA = {"type": "object", "properties": {"a": {"type": "string"}}}


def test_adapter_sends_the_schema_as_output_config_format():
    sdk = FakeSdk(_response([TextBlock(type="text", text="{}")]))
    AnthropicClient("k", "m-1", sdk_client=sdk).complete(
        "sys", [Message("user", "q")], [TOOL], schema=SCHEMA
    )
    sent = sdk.calls[0]
    assert set(sent) == {"model", "max_tokens", "system", "messages", "tools", "output_config"}
    assert sent["output_config"] == {"format": {"type": "json_schema", "schema": SCHEMA}}
    assert sent["model"] == "m-1"
    assert sent["max_tokens"] == MAX_TOKENS
    assert sent["system"] == "sys"
    assert sent["messages"] == [{"role": "user", "content": "q"}]
    assert sent["tools"] == [
        {"name": "search_products", "description": "Search.", "input_schema": TOOL.parameters}
    ]


def test_adapter_without_a_schema_sends_exactly_todays_arguments():
    sdk = FakeSdk(_response([TextBlock(type="text", text="hi")]))
    AnthropicClient("k", "m-1", sdk_client=sdk).complete("sys", [Message("user", "q")], [TOOL])
    assert set(sdk.calls[0]) == {"model", "max_tokens", "system", "messages", "tools"}
    assert sdk.calls[0]["max_tokens"] == MAX_TOKENS


def _text_turn(stop_reason, schema):
    sdk = FakeSdk(_response([TextBlock(type="text", text="partial")], stop_reason=stop_reason))
    return AnthropicClient("k", "m", sdk_client=sdk).complete("s", [], [], schema=schema)


def test_with_a_schema_a_refusal_is_a_model_error():
    with pytest.raises(ModelError) as e:
        _text_turn("refusal", SCHEMA)
    assert "refusal" in str(e.value)


def test_with_a_schema_a_cut_off_is_a_model_error():
    with pytest.raises(ModelError) as e:
        _text_turn("max_tokens", SCHEMA)
    assert "token limit" in str(e.value)


def test_with_a_schema_end_turn_returns_the_text():
    assert _text_turn("end_turn", SCHEMA).text == "partial"


@pytest.mark.parametrize("stop_reason", ["max_tokens", "refusal"])
def test_without_a_schema_a_stop_reason_returns_its_text_as_today(stop_reason):
    assert _text_turn(stop_reason, None).text == "partial"


def test_adapter_maps_text_only_response():
    sdk = FakeSdk(_response([TextBlock(type="text", text="Hello")]))
    turn = AnthropicClient("k", "m", sdk_client=sdk).complete("s", [], [])
    assert turn.text == "Hello"
    assert turn.tool_calls == ()


def test_adapter_translates_tool_round_trip_messages():
    sdk = FakeSdk(_response([TextBlock(type="text", text="ok")]))
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
    sdk = FakeSdk(_response([TextBlock(type="text", text="ok")]))
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
    sdk = FakeSdk(_response([TextBlock(type="text", text="hi")], model="served-model-9"))
    turn = AnthropicClient("k", "configured-model", sdk_client=sdk).complete("s", [], [])
    assert sdk.calls[0]["model"] == "configured-model"
    assert turn.model == "served-model-9"


def test_adapter_non_dict_tool_input_gives_empty_arguments():
    # `model_construct` skips validation, so a block can carry an input the SDK would refuse.
    bad = ToolUseBlock.model_construct(
        type="tool_use", id="tu_1", name="search_products", input=["x"]
    )
    sdk = FakeSdk(_response([bad]))
    turn = AnthropicClient("k", "m", sdk_client=sdk).complete("s", [], [])
    assert turn.tool_calls == (ToolCall("tu_1", "search_products", {}),)


def test_adapter_ignores_text_shaped_blocks_with_an_unknown_tag():
    # The SDK falls back to TextBlock for a tag it does not know and keeps the tag.
    foreign = TextBlock.model_construct(type="futuristic", text="leak")
    sdk = FakeSdk(_response([TextBlock(type="text", text="answer"), foreign]))
    turn = AnthropicClient("k", "m", sdk_client=sdk).complete("s", [], [])
    assert turn.text == "answer"


def test_adapter_ignores_tool_shaped_blocks_with_an_unknown_tag():
    foreign = ToolUseBlock.model_construct(
        type="futuristic", id="x_1", name="search_products", input={"a": 1}
    )
    sdk = FakeSdk(_response([TextBlock(type="text", text="answer"), foreign]))
    turn = AnthropicClient("k", "m", sdk_client=sdk).complete("s", [], [])
    assert turn.text == "answer"
    assert turn.tool_calls == ()
