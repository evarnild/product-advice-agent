import json
import threading
import time
import uuid

import pytest
from langfuse import Langfuse
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from advisor import tracing
from advisor.agent import answer_question, search_tool
from advisor.catalogue import Product
from advisor.models.base import ModelError, ModelTurn, ToolCall, Usage
from advisor.models.fake import ScriptedModelClient
from advisor.tracing import LangfuseTracer, NoopTracer, SafeTracer, make_tracer
from tests.helpers import RaisingTracer, RecordingTracer

CAT = [Product("P-001", "Alpha Phone", "Acme", "phone", 100.0, True, {}, "d")]
FULL_ENV = {
    "LANGFUSE_PUBLIC_KEY": "pk-test",
    "LANGFUSE_SECRET_KEY": "sk-test",
    "LANGFUSE_HOST": "http://langfuse.test:3000",
}


def _fake():
    return ScriptedModelClient(
        [
            ModelTurn(
                tool_calls=(ToolCall("c", "search_products", {"category": "phone"}),),
                usage=Usage(10, 4),
                model="m-1",
            ),
            ModelTurn(text="Buy P-001.", usage=Usage(20, 6), model="m-1"),
        ]
    )


def test_one_run_records_expected_observations_in_order():
    tracer = RecordingTracer()
    answer_question("which phone?", _fake(), [search_tool(CAT)], tracer)
    assert tracer.kinds == ["begin", "check", "generation", "tool", "generation", "check", "finish"]
    assert tracer.events[0] == ("begin", "which phone?")
    assert tracer.events[2][1:3] == ("m-1", Usage(10, 4))
    assert tracer.events[3][1:] == ("search_products", {"category": "phone"}, 1, False)
    assert tracer.events[-1] == ("finish", "Buy P-001.")
    assert tracer.kinds.count("begin") == 1 and tracer.kinds.count("finish") == 1


@pytest.mark.parametrize("missing", list(FULL_ENV))
def test_any_missing_variable_gives_noop_and_no_client(monkeypatch, missing):
    created = []
    monkeypatch.setattr(tracing, "Langfuse", lambda **kw: created.append(kw))
    env = {k: v for k, v in FULL_ENV.items() if k != missing}
    assert isinstance(make_tracer(env), NoopTracer)
    assert created == []


def test_empty_value_counts_as_unset(monkeypatch):
    created = []
    monkeypatch.setattr(tracing, "Langfuse", lambda **kw: created.append(kw))
    assert isinstance(make_tracer({**FULL_ENV, "LANGFUSE_HOST": ""}), NoopTracer)
    assert make_tracer({}).__class__ is NoopTracer
    assert created == []


def test_all_set_creates_one_client_with_the_values(monkeypatch):
    created = []

    class FakeClient:
        def __init__(self, **kw):
            created.append(kw)

    monkeypatch.setattr(tracing, "Langfuse", FakeClient)
    assert isinstance(make_tracer(FULL_ENV), SafeTracer)
    assert created == [
        {"public_key": "pk-test", "secret_key": "sk-test", "host": "http://langfuse.test:3000"}
    ]


def test_client_construction_failure_falls_back_to_noop(monkeypatch):
    def boom(**kw):
        raise RuntimeError("bad keys")

    monkeypatch.setattr(tracing, "Langfuse", boom)
    assert isinstance(make_tracer(FULL_ENV), NoopTracer)


def test_raising_tracer_does_not_change_answer():
    safe = SafeTracer(RaisingTracer())
    assert answer_question("q", _fake(), [search_tool(CAT)], safe) == "Buy P-001."


def _real_tracer():
    exporter = InMemorySpanExporter()
    client = Langfuse(
        # The SDK shares one exporter per public key, so each test needs its own key.
        public_key=f"pk-{uuid.uuid4().hex}",
        secret_key="sk-test",
        host="http://langfuse.test:3000",
        span_exporter=exporter,
        flush_at=1,
    )
    return exporter, LangfuseTracer(client)


def _attr(span, name):
    return span.attributes[f"langfuse.observation.{name}"]


def _json_attr(span, name):
    return json.loads(_attr(span, name))


def test_langfuse_tracer_with_real_sdk_and_in_memory_exporter():
    exporter, tracer = _real_tracer()
    script = [
        ModelTurn(
            tool_calls=(ToolCall("c", "search_products", {"category": "phone"}),),
            usage=Usage(10, 4),
            model="m-1",
        ),
        ModelTurn(tool_calls=(ToolCall("d", "no_such_tool", {}),), usage=Usage(1, 1), model="m-1"),
        ModelTurn(text="Buy P-001.", usage=Usage(20, 6), model="m-1"),
    ]
    answer_question("which phone?", ScriptedModelClient(script), [search_tool(CAT)], tracer)
    spans = exporter.get_finished_spans()
    assert sorted(s.name for s in spans) == sorted(
        [
            "advisor-run",
            "input-check",
            "model-call",
            "search_products",
            "model-call",
            "no_such_tool",
            "model-call",
            "output-check",
        ]
    )
    assert len({s.context.trace_id for s in spans}) == 1
    roots = [s for s in spans if s.parent is None]
    assert [s.name for s in roots] == ["advisor-run"]
    assert _attr(roots[0], "input") == "which phone?"
    assert _attr(roots[0], "output") == "Buy P-001."
    assert "langfuse.observation.level" not in roots[0].attributes
    by_name = {s.name: s for s in spans}

    for name in ("input-check", "output-check"):
        assert _attr(by_name[name], "type") == "guardrail"
        assert _json_attr(by_name[name], "output")["allowed"] is True

    search = by_name["search_products"]
    assert _attr(search, "type") == "tool"
    assert _json_attr(search, "input") == {"category": "phone"}
    assert _json_attr(search, "output") == {"result_count": 1}
    assert _attr(search, "level") == "DEFAULT"
    assert _attr(by_name["no_such_tool"], "level") == "ERROR"

    gens = [s for s in spans if s.name == "model-call"]
    assert all(_attr(g, "type") == "generation" for g in gens)
    assert {_attr(g, "model.name") for g in gens} == {"m-1"}
    usages = sorted((json.loads(_attr(g, "usage_details")) for g in gens), key=lambda u: u["input"])
    assert usages == [
        {"input": 1, "output": 1},
        {"input": 10, "output": 4},
        {"input": 20, "output": 6},
    ]


def test_failed_run_exports_root_with_level_error_and_propagates():
    exporter, tracer = _real_tracer()
    fake = ScriptedModelClient([ModelError("down")])
    with pytest.raises(ModelError):
        answer_question("which phone?", fake, [search_tool(CAT)], tracer)
    spans = exporter.get_finished_spans()
    roots = [s for s in spans if s.parent is None]
    assert [s.name for s in roots] == ["advisor-run"]
    assert _attr(roots[0], "level") == "ERROR"
    assert _attr(roots[0], "input") == "which phone?"
    assert _attr(roots[0], "output") == "ModelError: down"
    assert [s.name for s in spans if s.parent is not None] == ["input-check"]


def test_safe_tracer_swallows_fail_errors():
    SafeTracer(RaisingTracer()).fail("x")


def test_flush_is_bounded(monkeypatch):
    assert tracing.FLUSH_TIMEOUT_SECONDS <= 5
    monkeypatch.setattr(tracing, "FLUSH_TIMEOUT_SECONDS", 0.2)
    flushed = threading.Event()

    class Hanging:
        def start_observation(self, **kw):
            return self

        def update(self, **kw):
            pass

        def end(self):
            pass

        def flush(self):
            flushed.set()
            time.sleep(3)

    tracer = LangfuseTracer(Hanging())
    tracer.begin("q")
    start = time.monotonic()
    tracer.finish("a")
    assert time.monotonic() - start < 2
    assert flushed.wait(1)


def test_fail_also_flushes(monkeypatch):
    flushed = threading.Event()

    class Client:
        def start_observation(self, **kw):
            return self

        def update(self, **kw):
            self.updated = kw

        def end(self):
            pass

        def flush(self):
            flushed.set()

    client = Client()
    tracer = LangfuseTracer(client)
    tracer.begin("q")
    tracer.fail("boom")
    assert flushed.wait(1)
    assert client.updated == {"output": "boom", "level": "ERROR"}


def _events_of_a_run(tracer):
    answer_question("which phone?", _fake(), [search_tool(CAT)], tracer)


def test_safe_tracer_forwards_every_call_with_its_arguments():
    direct = RecordingTracer()
    _events_of_a_run(direct)
    inner = RecordingTracer()
    _events_of_a_run(SafeTracer(inner))
    assert inner.kinds == ["begin", "check", "generation", "tool", "generation", "check", "finish"]
    assert inner.events == direct.events
    assert inner.events[0] == ("begin", "which phone?")
    assert inner.events[3][1:] == ("search_products", {"category": "phone"}, 1, False)


def test_safe_tracer_forwards_fail():
    inner = RecordingTracer()
    with pytest.raises(ModelError):
        answer_question(
            "q", ScriptedModelClient([ModelError("down")]), [search_tool(CAT)], SafeTracer(inner)
        )
    assert inner.kinds == ["begin", "check", "fail"]
    assert inner.events[-1] == ("fail", "ModelError: down")


def test_safe_tracer_forwards_a_blocked_check(monkeypatch):
    from advisor import agent
    from advisor.guardrails import REFUSAL_TEXT, Verdict

    monkeypatch.setattr(agent, "check_input", lambda q: Verdict(False, "off topic"))
    inner = RecordingTracer()
    answer = answer_question("q", ScriptedModelClient([]), [search_tool(CAT)], SafeTracer(inner))
    assert answer == REFUSAL_TEXT
    assert inner.events == [
        ("begin", "q"),
        ("check", "input", False, "off topic"),
        ("finish", REFUSAL_TEXT),
    ]
