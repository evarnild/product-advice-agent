import json

import pytest

from advisor.agent import (
    FALLBACK_ANSWER,
    MAX_TURNS,
    Tool,
    answer_question,
    load_system_prompt,
    run_agent,
    search_tool,
)
from advisor.catalogue import Product
from advisor.models.base import ModelError, ModelTurn, ToolCall, Usage
from advisor.models.fake import ScriptedModelClient
from advisor.tracing import NoopTracer
from tests.helpers import RecordingTracer

CAT = [
    Product("P-001", "Alpha Phone", "Acme", "phone", 100.0, True, {"ram": "4 GB"}, "d"),
    Product("P-002", "Beta Phone", "Acme", "phone", 50.0, True, {}, "d"),
    Product("P-003", "Gamma Laptop", "Acme", "laptop", 500.0, True, {}, "d"),
]


def call(args, name="search_products", cid="c1"):
    return ModelTurn(tool_calls=(ToolCall(cid, name, args),), usage=Usage(5, 2), model="fake-1")


def final(text):
    return ModelTurn(text=text, usage=Usage(7, 3), model="fake-1")


def tool_results_sent(request):
    last = request.messages[-1]
    assert last.role == "user"
    return last.tool_results


def test_tool_call_then_final_text():
    fake = ScriptedModelClient([call({"category": "phone", "max_price": 80}), final("Try P-002.")])
    result = run_agent("cheap phone?", fake, [search_tool(CAT)], NoopTracer())
    assert result.answer == "Try P-002."
    assert not result.fallback
    assert len(fake.requests) == 2
    first = fake.requests[0]
    assert first.messages[0].text == "cheap phone?"
    assert [t.name for t in first.tools] == ["search_products"]
    assert first.system == load_system_prompt()
    (res,) = tool_results_sent(fake.requests[1])
    assert res.call_id == "c1"
    assert not res.is_error
    items = json.loads(res.content)
    assert [i["id"] for i in items] == ["P-002"]
    assert items[0]["name"] == "Beta Phone"
    # the assistant's tool call is in the history the model sees
    assert fake.requests[1].messages[1].tool_calls[0].arguments == {
        "category": "phone",
        "max_price": 80,
    }


def test_tool_arguments_reach_search():
    fake = ScriptedModelClient(
        [call({"category": "laptop", "keywords": ["gamma"], "limit": 1}), final("ok")]
    )
    run_agent("q", fake, [search_tool(CAT)], NoopTracer())
    items = json.loads(tool_results_sent(fake.requests[1])[0].content)
    assert [i["id"] for i in items] == ["P-003"]


def test_no_result_is_empty_list_not_error():
    fake = ScriptedModelClient([call({"category": "camera"}), final("none")])
    run_agent("q", fake, [search_tool(CAT)], NoopTracer())
    (res,) = tool_results_sent(fake.requests[1])
    assert not res.is_error
    assert json.loads(res.content) == []


def test_fallback_after_exactly_five_turns():
    assert MAX_TURNS == 5
    fake = ScriptedModelClient([call({"category": "phone"})], repeat_last=True)
    result = run_agent("q", fake, [search_tool(CAT)], NoopTracer())
    assert len(fake.requests) == 5
    assert result.answer == FALLBACK_ANSWER
    assert result.fallback
    assert FALLBACK_ANSWER == (
        "I couldn't find a good answer to that. "
        "Try asking about a product category or a price range."
    )


def test_final_text_on_fifth_turn_is_kept():
    fake = ScriptedModelClient([call({})] * 4 + [final("late")])
    result = run_agent("q", fake, [search_tool(CAT)], NoopTracer())
    assert result.answer == "late"
    assert len(fake.requests) == 5


def test_unknown_tool_gives_error_result_and_counts_as_a_turn():
    fake = ScriptedModelClient([call({}, name="launch_rocket"), final("sorry")])
    result = run_agent("q", fake, [search_tool(CAT)], NoopTracer())
    assert result.answer == "sorry"
    (res,) = tool_results_sent(fake.requests[1])
    assert res.is_error
    assert "launch_rocket" in res.content


def test_bad_arguments_give_error_result():
    bad_args = [
        {"category": "toaster"},
        {"max_price": "lots"},
        {"keywords": "notalist"},
        {"limit": "x"},
        {"bogus": 1},
        {"in_stock_only": "yes"},
    ]
    for args in bad_args:
        fake = ScriptedModelClient([call(args), final("fixed")])
        result = run_agent("q", fake, [search_tool(CAT)], NoopTracer())
        (res,) = tool_results_sent(fake.requests[1])
        assert res.is_error, args
        assert result.answer == "fixed"


def test_multiple_calls_in_one_turn_all_answered_in_order():
    turn = ModelTurn(
        tool_calls=(
            ToolCall("a", "search_products", {"category": "phone"}),
            ToolCall("b", "nope", {}),
        )
    )
    fake = ScriptedModelClient([turn, final("done")])
    run_agent("q", fake, [search_tool(CAT)], NoopTracer())
    results = tool_results_sent(fake.requests[1])
    assert [r.call_id for r in results] == ["a", "b"]
    assert [r.is_error for r in results] == [False, True]


def test_tool_that_raises_unexpectedly_becomes_error_result():
    def boom(args):
        raise ValueError("kaput")

    from advisor.models.base import ToolSpec

    tool = Tool(ToolSpec("search_products", "x", {}), boom)
    fake = ScriptedModelClient([call({}), final("ok")])
    run_agent("q", fake, [tool], NoopTracer())
    (res,) = tool_results_sent(fake.requests[1])
    assert res.is_error


def test_empty_turn_counts_and_continues():
    fake = ScriptedModelClient([ModelTurn(), final("then text")])
    result = run_agent("q", fake, [search_tool(CAT)], NoopTracer())
    assert result.answer == "then text"


def test_tracer_sees_generations_and_tools_in_order():
    tracer = RecordingTracer()
    fake = ScriptedModelClient([call({"category": "phone"}), final("ans")])
    run_agent("q", fake, [search_tool(CAT)], tracer)
    assert tracer.kinds == ["generation", "tool", "generation"]
    assert tracer.events[0][1:3] == ("fake-1", Usage(5, 2))
    assert tracer.events[0][4] == ["search_products"]
    assert tracer.events[1][1:] == ("search_products", {"category": "phone"}, 2, False)
    assert tracer.events[2][3] == "ans"


def test_system_prompt_file_content():
    p = load_system_prompt()
    assert "search_products" in p
    assert "id" in p


ARG_CAT = [
    Product("P-010", "Cheap Phone", "Acme", "phone", 50.0, True, {"ram": "2 GB"}, "basic"),
    Product("P-011", "Mid Phone", "Acme", "phone", 150.0, False, {"ram": "4 GB"}, "solid zoom"),
    Product("P-012", "Pro Phone", "Acme", "phone", 250.0, True, {"ram": "8 GB"}, "zoom lens"),
    Product("P-013", "Max Phone", "Acme", "phone", 350.0, True, {"ram": "16 GB"}, "huge"),
]


def _ids_for(args):
    fake = ScriptedModelClient([call(args), final("ok")])
    run_agent("q", fake, [search_tool(ARG_CAT)], NoopTracer())
    (res,) = tool_results_sent(fake.requests[1])
    assert not res.is_error
    return [i["id"] for i in json.loads(res.content)]


def test_each_tool_argument_alone_changes_the_results():
    assert _ids_for({}) == ["P-010", "P-011", "P-012", "P-013"]
    assert _ids_for({"min_price": 200}) == ["P-012", "P-013"]
    assert _ids_for({"max_price": 200}) == ["P-010", "P-011"]
    assert _ids_for({"keywords": ["zoom"]}) == ["P-011", "P-012"]
    assert _ids_for({"in_stock_only": True}) == ["P-010", "P-012", "P-013"]
    assert _ids_for({"limit": 2}) == ["P-010", "P-011"]
    assert _ids_for({"category": "laptop"}) == []


def test_tool_result_carries_all_fields_including_specs():
    fake = ScriptedModelClient([call({"limit": 1}), final("ok")])
    run_agent("q", fake, [search_tool(ARG_CAT)], NoopTracer())
    (item,) = json.loads(tool_results_sent(fake.requests[1])[0].content)
    assert item == {
        "id": "P-010",
        "name": "Cheap Phone",
        "brand": "Acme",
        "category": "phone",
        "price_eur": 50.0,
        "in_stock": True,
        "specs": {"ram": "2 GB"},
        "description": "basic",
    }


def test_bad_argument_errors_name_the_argument():
    cases = [
        ({"max_price": "lots"}, "max_price"),
        ({"max_price": True}, "max_price"),
        ({"min_price": "x"}, "min_price"),
        ({"min_price": False}, "min_price"),
        ({"limit": "x"}, "limit"),
        ({"limit": True}, "limit"),
        ({"limit": 2.5}, "limit"),
        ({"keywords": "notalist"}, "keywords"),
        ({"keywords": [1]}, "keywords"),
        ({"in_stock_only": "yes"}, "in_stock_only"),
        ({"category": "toaster"}, "category"),
        ({"bogus": 1}, "bogus"),
    ]
    for args, name in cases:
        fake = ScriptedModelClient([call(args), final("fixed")])
        run_agent("q", fake, [search_tool(CAT)], NoopTracer())
        (res,) = tool_results_sent(fake.requests[1])
        assert res.is_error, args
        assert f"{name}" in res.content, (args, res.content)
        assert "failed" not in res.content, (args, res.content)


def test_failed_run_closes_the_trace_then_raises():
    tracer = RecordingTracer()
    fake = ScriptedModelClient([ModelError("down")])
    with pytest.raises(ModelError):
        answer_question("q", fake, [search_tool(CAT)], tracer)
    assert tracer.kinds == ["begin", "check", "fail"]
    assert tracer.events[1][1:3] == ("input", True)
    assert tracer.events[2] == ("fail", "ModelError: down")


def test_failed_run_does_not_record_finish():
    tracer = RecordingTracer()
    with pytest.raises(RuntimeError):
        answer_question("q", ScriptedModelClient([RuntimeError("x")]), [], tracer)
    assert "finish" not in tracer.kinds


def test_unparsable_ollama_arguments_get_an_error_result_and_the_run_goes_on():
    fake = ScriptedModelClient(
        [call({"_unparsable_arguments": "not json"}), final("Sorry, try again.")]
    )
    result = run_agent("q", fake, [search_tool(CAT)], NoopTracer())
    (tool_result,) = tool_results_sent(fake.requests[1])
    assert tool_result.is_error
    assert "unknown argument(s): _unparsable_arguments" in tool_result.content
    assert result.answer == "Sorry, try again."
