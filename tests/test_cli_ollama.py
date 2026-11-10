"""CLI behaviour specific to the keyless Ollama provider (spec B3-B5, B10-B14)."""

from collections.abc import Sequence

import pytest

from advisor import cli
from advisor.cli import UNAVAILABLE, main
from advisor.models.base import (
    ModelError,
    ModelNotAvailableError,
    ModelTurn,
    ModelUnreachableError,
    ToolCall,
    Usage,
)
from advisor.models.fake import ScriptedModelClient
from advisor.tracing import NoopTracer

ANTHROPIC_ENV = {"ADVISOR_MODEL_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "placeholder-key"}


def script():
    return ScriptedModelClient(
        [
            ModelTurn(tool_calls=(ToolCall("c", "search_products", {"category": "headphones"}),)),
            ModelTurn(text="Try the Auralis Calm 300 (P-001).", usage=Usage(1, 1), model="m"),
        ]
    )


class Factory:
    def __init__(self, client):
        self.client = client
        self.calls = []
        self.base_urls = []

    def __call__(self, provider, model, *, api_key=None, base_url=None):
        self.calls.append((provider, model, api_key))
        self.base_urls.append(base_url)
        return self.client


@pytest.fixture(autouse=True)
def _no_tracing(monkeypatch):
    monkeypatch.setattr(cli, "make_tracer", lambda env, tags=(): NoopTracer())


def test_default_provider_is_ollama_without_a_key():
    factory = Factory(script())
    assert main(["q"], env={}, client_factory=factory) == 0
    assert factory.calls == [("ollama", "qwen3:8b", None)]
    assert factory.base_urls == ["http://localhost:11434"]


def test_ollama_never_receives_an_anthropic_key(capsys):
    factory = Factory(script())
    assert main(["q"], env={"ANTHROPIC_API_KEY": "sk-x"}, client_factory=factory) == 0
    assert factory.calls == [("ollama", "qwen3:8b", None)]
    out = capsys.readouterr()
    assert "sk-x" not in out.out + out.err


def test_anthropic_gets_its_key_and_no_base_url():
    factory = Factory(script())
    main(["q"], env=ANTHROPIC_ENV, client_factory=factory)
    assert factory.calls == [("anthropic", "claude-haiku-5-5", "placeholder-key")]
    assert factory.base_urls == [None]


def test_anthropic_without_key_keeps_the_missing_key_message(capsys):
    factory = Factory(script())
    env = {"ADVISOR_MODEL_PROVIDER": "anthropic"}
    assert main(["q"], env=env, client_factory=factory) == 1
    assert (
        capsys.readouterr().err.strip()
        == "Missing ANTHROPIC_API_KEY: set it in the environment or in .env."
    )
    assert factory.calls == []


@pytest.mark.parametrize("url", ["localhost:11434", "ftp://h", "http://"])
def test_bad_ollama_url_exit_1_names_variable_no_client(url, capsys):
    factory = Factory(script())
    assert main(["q"], env={"ADVISOR_OLLAMA_URL": url}, client_factory=factory) == 1
    assert "ADVISOR_OLLAMA_URL" in capsys.readouterr().err
    assert factory.calls == []


def test_custom_ollama_url_reaches_the_factory():
    factory = Factory(script())
    main(["q"], env={"ADVISOR_OLLAMA_URL": "http://box:9"}, client_factory=factory)
    assert factory.base_urls == ["http://box:9"]


@pytest.mark.parametrize(
    "error",
    [
        ModelUnreachableError("Ollama is not reachable at http://h:1. Start it."),
        ModelNotAvailableError("Model 'x' is not available in Ollama. Run: ollama pull x"),
    ],
)
def test_ollama_specific_errors_print_their_message_exit_1(error, capsys):
    fake = ScriptedModelClient([error])
    assert main(["q"], env={}, client_factory=Factory(fake)) == 1
    err = capsys.readouterr().err
    assert err.strip() == str(error)
    assert "Traceback" not in err and UNAVAILABLE not in err


def test_ollama_specific_error_shows_traceback_with_debug(capsys):
    fake = ScriptedModelClient([ModelUnreachableError("msg")])
    assert main(["--debug", "q"], env={}, client_factory=Factory(fake)) == 1
    assert "Traceback" in capsys.readouterr().err


def test_other_model_errors_stay_generic(capsys):
    fake = ScriptedModelClient([ModelError("500")])
    assert main(["q"], env={}, client_factory=Factory(fake)) == 1
    err = capsys.readouterr().err
    assert err.strip() == UNAVAILABLE


@pytest.mark.parametrize(
    ("env", "tags"),
    [
        ({}, ["provider:ollama", "model:qwen3:8b"]),
        (ANTHROPIC_ENV, ["provider:anthropic", "model:claude-haiku-5-5"]),
        ({"ADVISOR_MODEL": "other:1b"}, ["provider:ollama", "model:other:1b"]),
    ],
)
def test_tracer_gets_provider_and_model_tags(monkeypatch, env, tags):
    seen: list[Sequence[str]] = []
    monkeypatch.setattr(cli, "make_tracer", lambda e, t=(): seen.append(list(t)) or NoopTracer())
    main(["q"], env=env, client_factory=Factory(script()))
    assert seen == [tags]
