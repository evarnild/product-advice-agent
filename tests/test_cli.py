import pytest

from advisor import cli
from advisor.catalogue import CatalogueError
from advisor.cli import UNAVAILABLE, USAGE, main
from advisor.models.base import ModelError, ModelTurn, ToolCall, Usage
from advisor.models.fake import ScriptedModelClient
from advisor.tracing import NoopTracer, SafeTracer
from tests.helpers import RaisingTracer

ENV = {"ADVISOR_MODEL_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "placeholder-key"}


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

    def __call__(self, provider, model, *, api_key=None, base_url=None):
        self.calls.append((provider, model, api_key))
        return self.client


@pytest.fixture(autouse=True)
def _no_tracing(monkeypatch):
    monkeypatch.setattr(cli, "make_tracer", lambda env, tags=(): NoopTracer())


def test_happy_path_prints_answer_exit_0(capsys):
    fake = script()
    factory = Factory(fake)
    assert main(["I want", "headphones"], env=ENV, client_factory=factory) == 0
    out = capsys.readouterr()
    assert out.out.strip() == "Try the Auralis Calm 300 (P-001)."
    assert out.err == ""
    assert factory.calls == [("anthropic", "claude-haiku-5-5", "placeholder-key")]
    assert fake.requests[0].messages[0].text == "I want headphones"
    tool_result = fake.requests[1].messages[-1].tool_results[0]
    assert "P-001" in tool_result.content  # real committed catalogue was searched


def test_model_override(capsys):
    factory = Factory(script())
    main(["q"], env={**ENV, "ADVISOR_MODEL": "other-model"}, client_factory=factory)
    assert factory.calls[0][1] == "other-model"


@pytest.mark.parametrize("argv", [[], [""], ["   "], ["--debug"], ["--bogus"]])
def test_blank_or_missing_question_exits_2_with_usage(argv, capsys):
    factory = Factory(script())
    assert main(argv, env=ENV, client_factory=factory) == 2
    out = capsys.readouterr()
    assert USAGE in out.err
    assert out.out == ""
    assert factory.calls == []


def test_unknown_provider_exit_1_lists_known_no_client(capsys):
    factory = Factory(script())
    env = {**ENV, "ADVISOR_MODEL_PROVIDER": "mystery"}
    assert main(["q"], env=env, client_factory=factory) == 1
    err = capsys.readouterr().err
    assert "mystery" in err and "anthropic" in err and "ollama" in err
    assert factory.calls == []


@pytest.mark.parametrize(
    "env",
    [
        {"ADVISOR_MODEL_PROVIDER": "anthropic"},
        {"ADVISOR_MODEL_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": ""},
    ],
)
def test_missing_key_exit_1_names_variable_no_client(env, capsys):
    factory = Factory(script())
    assert main(["q"], env=env, client_factory=factory) == 1
    assert "ANTHROPIC_API_KEY" in capsys.readouterr().err
    assert factory.calls == []


def test_key_is_never_printed(capsys):
    main(
        ["q"],
        env={"ADVISOR_MODEL_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sekrit-value"},
        client_factory=Factory(script()),
    )
    captured = capsys.readouterr()
    assert "sekrit-value" not in captured.out + captured.err


def test_model_failure_exit_1_no_traceback(capsys):
    fake = ScriptedModelClient([ModelError("down")])
    assert main(["q"], env=ENV, client_factory=Factory(fake)) == 1
    err = capsys.readouterr().err
    assert UNAVAILABLE in err
    assert "Traceback" not in err


def test_debug_shows_traceback(capsys):
    fake = ScriptedModelClient([RuntimeError("kaboom")])
    assert main(["--debug", "q"], env=ENV, client_factory=Factory(fake)) == 1
    err = capsys.readouterr().err
    assert UNAVAILABLE in err
    assert "Traceback" in err and "kaboom" in err


def test_catalogue_error_exit_1(monkeypatch, capsys):
    def bad():
        raise CatalogueError("product P-009: field 'price_eur' is missing")

    monkeypatch.setattr(cli, "load_catalogue", bad)
    factory = Factory(script())
    assert main(["q"], env=ENV, client_factory=factory) == 1
    assert "P-009" in capsys.readouterr().err
    assert factory.calls == []


def test_raising_tracer_changes_neither_answer_nor_exit(monkeypatch, capsys):
    monkeypatch.setattr(cli, "make_tracer", lambda env, tags=(): SafeTracer(RaisingTracer()))
    assert main(["q"], env=ENV, client_factory=Factory(script())) == 0
    assert capsys.readouterr().out.strip() == "Try the Auralis Calm 300 (P-001)."


def test_tracer_gets_full_environment(monkeypatch):
    seen = []
    monkeypatch.setattr(
        cli, "make_tracer", lambda env, tags=(): seen.append(dict(env)) or NoopTracer()
    )
    main(["q"], env={**ENV, "LANGFUSE_HOST": "http://x"}, client_factory=Factory(script()))
    assert seen[0]["LANGFUSE_HOST"] == "http://x"


def test_debug_sets_advisor_logger_to_debug():
    import logging

    advisor_log = logging.getLogger("advisor")
    root = logging.getLogger()
    before = (advisor_log.level, list(root.handlers))
    try:
        assert main(["--debug", "q"], env=ENV, client_factory=Factory(script())) == 0
        assert advisor_log.level == logging.DEBUG
    finally:
        advisor_log.setLevel(before[0])
        for h in list(root.handlers):
            if h not in before[1]:
                root.removeHandler(h)


def test_stdout_is_reconfigured_to_utf8(monkeypatch):
    import sys

    class Stdout:
        def __init__(self):
            self.reconfigured = []
            self.written = []

        def reconfigure(self, **kwargs):
            self.reconfigured.append(kwargs)

        def write(self, text):
            self.written.append(text)

        def flush(self):
            pass

    out = Stdout()
    monkeypatch.setattr(sys, "stdout", out)
    assert main(["q"], env=ENV, client_factory=Factory(script())) == 0
    assert out.reconfigured == [{"encoding": "utf-8", "errors": "replace"}]
