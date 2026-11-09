import time

import pytest
from langfuse import Langfuse
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from advisor import tracing
from advisor.agent import answer_question, search_tool
from advisor.catalogue import Product
from advisor.models.base import ModelTurn, ToolCall, Usage
from advisor.models.fake import ScriptedModelClient
from advisor.tracing import LangfuseTracer, NoopTracer, SafeTracer, make_tracer
from tests.helpers import RaisingTracer, RecordingTracer

CAT = [Product("P-001", "Alpha Phone", "Acme", "phone", 100.0, True, {}, "d")]
FULL_ENV = {
    "LANGFUSE_PUBLIC_KEY": "pk-test",
    "LANGFUSE_SECRET_KEY": "sk-test",
    "LANGFUSE_HOST": "http://localhost:3000",
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
        {"public_key": "pk-test", "secret_key": "sk-test", "host": "http://localhost:3000"}
    ]


def test_client_construction_failure_falls_back_to_noop(monkeypatch):
    def boom(**kw):
        raise RuntimeError("bad keys")

    monkeypatch.setattr(tracing, "Langfuse", boom)
    assert isinstance(make_tracer(FULL_ENV), NoopTracer)


def test_raising_tracer_does_not_change_answer():
    safe = SafeTracer(RaisingTracer())
    assert answer_question("q", _fake(), [search_tool(CAT)], safe) == "Buy P-001."


def test_langfuse_tracer_with_real_sdk_and_in_memory_exporter():
    exporter = InMemorySpanExporter()
    client = Langfuse(
        public_key="pk-test",
        secret_key="sk-test",
        host="http://localhost:3000",
        span_exporter=exporter,
        flush_at=1,
    )
    tracer = LangfuseTracer(client)
    answer_question("which phone?", _fake(), [search_tool(CAT)], tracer)
    spans = exporter.get_finished_spans()
    names = [s.name for s in spans]
    assert sorted(names) == sorted(
        [
            "advisor-run",
            "input-check",
            "model-call",
            "search_products",
            "model-call",
            "output-check",
        ]
    )
    assert len({s.context.trace_id for s in spans}) == 1
    roots = [s for s in spans if s.parent is None]
    assert [s.name for s in roots] == ["advisor-run"]
    attrs = {k: str(v) for k, v in roots[0].attributes.items()}
    assert any("which phone?" in v for v in attrs.values())
    assert any("Buy P-001." in v for v in attrs.values())
    gens = [s for s in spans if s.name == "model-call"]
    joined = " ".join(str(v) for g in gens for v in g.attributes.values())
    assert "m-1" in joined and "10" in joined


def test_flush_is_bounded(monkeypatch):
    monkeypatch.setattr(tracing, "FLUSH_TIMEOUT_SECONDS", 0.2)

    class Hanging:
        def start_observation(self, **kw):
            return self

        def update(self, **kw):
            pass

        def end(self):
            pass

        def flush(self):
            time.sleep(3)

    tracer = LangfuseTracer(Hanging())
    tracer.begin("q")
    start = time.monotonic()
    tracer.finish("a")
    assert time.monotonic() - start < 2
