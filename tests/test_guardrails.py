from advisor import agent
from advisor.agent import answer_question, search_tool
from advisor.catalogue import Product
from advisor.guardrails import REFUSAL_TEXT, Verdict, check_input, check_output
from advisor.models.base import ModelTurn, ToolCall
from advisor.models.fake import ScriptedModelClient
from tests.helpers import RecordingTracer

CAT = [Product("P-001", "Alpha Phone", "Acme", "phone", 100.0, True, {}, "d")]


def _fake():
    return ScriptedModelClient(
        [
            ModelTurn(tool_calls=(ToolCall("c", "search_products", {}),)),
            ModelTurn(text="Buy P-001."),
        ]
    )


def test_defaults_allow():
    assert check_input("anything").allow
    assert check_output("anything").allow


def test_refusal_text():
    assert REFUSAL_TEXT == "I can only help with questions about our electronics catalogue."


def test_allowed_run_returns_agent_answer_and_traces_checks_around_agent():
    tracer = RecordingTracer()
    fake = _fake()
    assert answer_question("q", fake, [search_tool(CAT)], tracer) == "Buy P-001."
    assert tracer.kinds == [
        "begin",
        "check",
        "generation",
        "tool",
        "generation",
        "check",
        "finish",
    ]
    assert tracer.events[1][1:3] == ("input", True)
    assert tracer.events[5][1:3] == ("output", True)
    assert tracer.events[-1] == ("finish", "Buy P-001.")


def test_blocked_input_refuses_and_model_is_never_called(monkeypatch):
    monkeypatch.setattr(agent, "check_input", lambda q: Verdict(False, "off topic"))
    fake = _fake()
    tracer = RecordingTracer()
    assert answer_question("q", fake, [search_tool(CAT)], tracer) == REFUSAL_TEXT
    assert fake.requests == []
    assert tracer.events[1] == ("check", "input", False, "off topic")
    assert tracer.events[-1] == ("finish", REFUSAL_TEXT)
    assert "generation" not in tracer.kinds


def test_blocked_output_replaces_answer(monkeypatch):
    seen = []

    def block(a):
        seen.append(a)
        return Verdict(False, "bad")

    monkeypatch.setattr(agent, "check_output", block)
    fake = _fake()
    tracer = RecordingTracer()
    assert answer_question("q", fake, [search_tool(CAT)], tracer) == REFUSAL_TEXT
    assert seen == ["Buy P-001."]
    assert tracer.events[-1] == ("finish", REFUSAL_TEXT)
