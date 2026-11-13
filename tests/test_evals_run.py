import hashlib
import io
import json
from datetime import UTC, datetime, timedelta

import pytest

from advisor.agent import SYSTEM_PROMPT_PATH, ToolError, search_tool
from advisor.catalogue import load_catalogue
from advisor.evals.run import RecordingTracer, _recording_tool, main
from advisor.models.base import (
    ModelError,
    ModelNotAvailableError,
    ModelTurn,
    ModelUnreachableError,
    ToolCall,
    Usage,
)
from advisor.models.fake import ScriptedModelClient

ENV = {"ADVISOR_MODEL_PROVIDER": "ollama", "ADVISOR_MODEL": "test-model"}
CLOCK_TIME = datetime(2026, 11, 11, 9, 30, 5, tzinfo=UTC)

CASES = [
    {
        "id": "hp",
        "question": "headphones under 200?",
        "expect_ids": ["P-001"],
        "expect_search": {"category": "headphones", "max_price": 200},
    },
    {"id": "lap", "question": "a laptop?", "expect_ids": ["P-009"]},
    {"id": "off", "question": "weather?", "must_decline": True},
]

HP_OK = [
    ModelTurn(
        tool_calls=(
            ToolCall("c1", "search_products", {"category": "headphones", "max_price": 200}),
        )
    ),
    ModelTurn(text="Try the Auralis Calm 300 (P-001) at 189 euros."),
]
HP_BAD = [ModelTurn(text="Try the Auralis Calm 300 (P-001) at 100 euros.")]
LAP_OK = [ModelTurn(text="The Pelagic Go 13 (P-009) costs 649 euros.")]
OFF_OK = [ModelTurn(text="Sorry, I only help with electronics.")]


class Factory:
    def __init__(self, script):
        self.client = ScriptedModelClient(script)
        self.calls = []

    def __call__(self, provider, model, *, api_key=None, base_url=None):
        self.calls.append((provider, model, api_key, base_url))
        return self.client


def write_cases(tmp_path, cases=CASES):
    path = tmp_path / "cases.jsonl"
    path.write_text("\n".join(json.dumps(c) for c in cases) + "\n", encoding="utf-8")
    return path


def ticking_clock(step_seconds=1.5):
    ticks = iter(range(10_000))
    return lambda: CLOCK_TIME + timedelta(seconds=step_seconds * next(ticks))


def run(tmp_path, script, *extra, cases=CASES, env=ENV, now=lambda: CLOCK_TIME):
    out, err = io.StringIO(), io.StringIO()
    factory = Factory(script)
    code = main(
        [
            "--cases",
            str(write_cases(tmp_path, cases)),
            "--report-dir",
            str(tmp_path / "runs"),
            *extra,
        ],
        env=env,
        client_factory=factory,
        out=out,
        err=err,
        now=now,
    )
    return code, out.getvalue(), err.getvalue(), factory


def test_all_pass_exits_0_with_a_line_per_case_and_a_total(tmp_path):
    code, out, err, factory = run(tmp_path, HP_OK + LAP_OK + OFF_OK)
    assert code == 0, out + err
    lines = out.splitlines()
    assert lines[:3] == ["PASS hp", "PASS lap", "PASS off"]
    assert lines[3] == "3/3 passed (ollama, test-model)"
    assert factory.calls == [("ollama", "test-model", None, "http://localhost:11434")]


def test_a_failing_case_exits_1_and_names_the_reason(tmp_path):
    code, out, _, _ = run(tmp_path, HP_BAD + LAP_OK + OFF_OK)
    assert code == 1
    assert out.splitlines()[0].startswith("FAIL hp: ")
    assert "price of P-001 not stated" in out
    assert "2/3 passed" in out


def report_of(tmp_path):
    (path,) = list((tmp_path / "runs").iterdir())
    return json.loads(path.read_text(encoding="utf-8"))


def test_a_model_error_on_the_first_case_does_not_abort(tmp_path):
    code, out, err, factory = run(tmp_path, [ModelError("boom")] + LAP_OK + OFF_OK)
    assert code == 1
    assert out.splitlines()[:3] == ["ERROR hp: boom", "PASS lap", "PASS off"]
    assert "2/3 passed" in out
    assert len(factory.client.requests) == 3
    assert report_of(tmp_path)["cases"][0]["status"] == "ERROR"


def test_an_unexpected_exception_is_an_error_and_the_run_goes_on(tmp_path):
    code, out, err, _ = run(tmp_path, HP_OK + [RuntimeError("x")] + OFF_OK)
    assert code == 1
    assert out.splitlines()[:3] == ["PASS hp", "ERROR lap: unexpected RuntimeError", "PASS off"]
    assert "Traceback" not in err and "Traceback" not in out
    assert report_of(tmp_path)["totals"]["errors"] == 1


def test_a_failing_case_totals_and_case_file_hash_in_the_report(tmp_path):
    code, _, _, _ = run(tmp_path, HP_BAD + LAP_OK + OFF_OK)
    assert code == 1
    report = report_of(tmp_path)
    assert report["totals"] == {"total": 3, "passed": 2, "failed": 1, "errors": 0}
    expected = hashlib.sha256((tmp_path / "cases.jsonl").read_bytes()).hexdigest()
    assert report["cases_sha256"] == expected


def test_duration_is_measured_with_the_clock(tmp_path):
    run(tmp_path, HP_OK + LAP_OK + OFF_OK, now=ticking_clock(1.5))
    durations = [c["duration_s"] for c in report_of(tmp_path)["cases"]]
    assert all(d > 0 for d in durations)
    assert durations == [1.5, 1.5, 1.5]


def test_a_model_error_marks_error_counts_as_failure_and_run_continues(tmp_path):
    code, out, _, _ = run(tmp_path, HP_OK + [ModelError("boom")] + OFF_OK)
    assert code == 1
    assert out.splitlines()[:3] == ["PASS hp", "ERROR lap: boom", "PASS off"]
    assert "2/3 passed" in out
    report = json.loads(next((tmp_path / "runs").iterdir()).read_text(encoding="utf-8"))
    assert report["totals"] == {"total": 3, "passed": 2, "failed": 0, "errors": 1}


def test_first_case_unreachable_aborts_the_run(tmp_path):
    for exc in (ModelUnreachableError("server down"), ModelNotAvailableError("no model")):
        code, out, err, factory = run(tmp_path, [exc])
        assert code == 1
        assert str(exc) in err
        assert out == ""
        assert len(factory.client.requests) == 1  # later cases not run
    assert not (tmp_path / "runs").exists()  # no report for an aborted run


def test_later_unreachable_is_an_error_not_an_abort(tmp_path):
    code, out, _, _ = run(tmp_path, HP_OK + [ModelUnreachableError("down")] + OFF_OK)
    assert code == 1
    assert "ERROR lap: down" in out
    assert "PASS off" in out


def test_bad_case_file_exits_2_naming_case_and_field(tmp_path):
    bad = [{"id": "x", "question": "q", "expect_ids": ["P-099"]}]
    code, out, err, factory = run(tmp_path, [], cases=bad)
    assert code == 2
    assert "case 'x'" in err and "'expect_ids'" in err
    assert factory.calls == []


def test_missing_case_file_and_bad_arguments_exit_2(tmp_path):
    err = io.StringIO()
    assert main(["--cases", str(tmp_path / "none.jsonl")], env=ENV, out=io.StringIO(), err=err) == 2
    assert "Case file error" in err.getvalue()
    assert main(["--bogus"], env=ENV, out=io.StringIO(), err=io.StringIO()) == 2


def test_unknown_only_id_exits_2(tmp_path):
    code, _, err, _ = run(tmp_path, [], "--only", "nope")
    assert code == 2
    assert "nope" in err


def test_config_errors_exit_2(tmp_path):
    code, _, err, _ = run(tmp_path, [], env={"ADVISOR_MODEL_PROVIDER": "anthropic"})
    assert code == 2
    assert "Missing ANTHROPIC_API_KEY" in err
    code, _, err, _ = run(tmp_path, [], env={"ADVISOR_MODEL_PROVIDER": "nope"})
    assert code == 2
    assert "Unknown model provider" in err


def test_only_runs_just_the_named_cases(tmp_path):
    code, out, _, factory = run(tmp_path, LAP_OK + OFF_OK, "--only", "lap, off")
    assert code == 0
    assert out.splitlines()[:2] == ["PASS lap", "PASS off"]
    assert "2/2 passed" in out
    assert len(factory.client.requests) == 2


def test_report_file_name_and_fields(tmp_path):
    code, out, _, _ = run(tmp_path, HP_OK + LAP_OK + OFF_OK)
    assert code == 0
    (path,) = list((tmp_path / "runs").iterdir())
    assert path.name == "20261111T093005Z-ollama.json"
    assert str(path) in out
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["provider"] == "ollama"
    assert report["model"] == "test-model"
    assert len(report["cases_sha256"]) == 64
    assert report["totals"] == {"total": 3, "passed": 3, "failed": 0, "errors": 0}
    first = report["cases"][0]
    assert first["id"] == "hp"
    assert first["question"] == "headphones under 200?"
    assert first["answer"].startswith("Try the Auralis")
    assert first["searches"] == [{"category": "headphones", "max_price": 200}]
    assert {c["name"] for c in first["checks"]} >= {"grounded", "expected", "search"}
    assert all(set(c) == {"name", "ok", "reason"} for c in first["checks"])
    assert first["duration_s"] == 0


def test_expect_search_is_read_through_the_recording_tracer(tmp_path):
    # Right answer, but the model never searched: only the search check fails.
    answer_only = [ModelTurn(text="Try the Auralis Calm 300 (P-001) at 189 euros.")]
    code, out, _, _ = run(tmp_path, answer_only + LAP_OK + OFF_OK)
    assert code == 1
    assert out.splitlines()[0].startswith("FAIL hp: no search_products call matches")
    # A search above the budget fails it too.
    over = [
        ModelTurn(tool_calls=(ToolCall("c", "search_products", {"category": "headphones"}),)),
        ModelTurn(text="Try the Auralis Calm 300 (P-001) at 189 euros."),
    ]
    code, out, _, _ = run(tmp_path, over + LAP_OK + OFF_OK)
    assert code == 1
    assert out.splitlines()[0].startswith("FAIL hp: no search_products call matches")


def test_the_suite_does_not_write_outside_the_report_dir(tmp_path):
    run(tmp_path, HP_OK + LAP_OK + OFF_OK)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["cases.jsonl", "runs"]


ANTHROPIC_ENV = {
    "ADVISOR_MODEL_PROVIDER": "anthropic",
    "ADVISOR_MODEL": "claude-env-model",
    "ANTHROPIC_API_KEY": "test-key-not-real",
}


def test_provider_flag_wins_over_the_environment_and_uses_its_default_model(tmp_path):
    code, out, _, factory = run(
        tmp_path, HP_OK + LAP_OK + OFF_OK, "--provider", "ollama", env=ANTHROPIC_ENV
    )
    assert code == 0
    assert factory.calls == [("ollama", "qwen3:8b", None, "http://localhost:11434")]
    assert "3/3 passed (ollama, qwen3:8b)" in out
    assert report_of(tmp_path)["provider"] == "ollama"
    (path,) = list((tmp_path / "runs").iterdir())
    assert path.name.endswith("-ollama.json")


def test_provider_flag_uses_the_anthropic_default_model_and_key(tmp_path):
    env = {**ENV, "ANTHROPIC_API_KEY": "test-key-not-real"}
    code, out, _, factory = run(
        tmp_path, HP_OK + LAP_OK + OFF_OK, "--provider", "anthropic", env=env
    )
    assert code == 0
    assert factory.calls == [("anthropic", "claude-haiku-5-5", "test-key-not-real", None)]
    assert "(anthropic, claude-haiku-5-5)" in out
    assert "test-key-not-real" not in out


def test_provider_flag_naming_the_env_provider_still_takes_the_default_model(tmp_path):
    env = {
        **ENV,
        "ADVISOR_MODEL_PROVIDER": "anthropic",
        "ADVISOR_MODEL": "claude-other-model",
        "ANTHROPIC_API_KEY": "test-key-not-real",
    }
    code, out, _, factory = run(
        tmp_path, HP_OK + LAP_OK + OFF_OK, "--provider", "anthropic", env=env
    )
    assert code == 0
    assert factory.calls == [("anthropic", "claude-haiku-5-5", "test-key-not-real", None)]
    assert "claude-other-model" not in out


def test_provider_flag_naming_the_env_provider_ignores_env_model_for_ollama(tmp_path):
    env = {**ENV, "ADVISOR_MODEL_PROVIDER": "ollama", "ADVISOR_MODEL": "env-model"}
    code, _, _, factory = run(tmp_path, HP_OK + LAP_OK + OFF_OK, "--provider", "ollama", env=env)
    assert code == 0
    assert factory.calls == [("ollama", "qwen3:8b", None, "http://localhost:11434")]


def test_model_flag_alone_overrides_only_the_model(tmp_path):
    code, out, _, factory = run(tmp_path, HP_OK + LAP_OK + OFF_OK, "--model", "other-model")
    assert code == 0
    assert factory.calls == [("ollama", "other-model", None, "http://localhost:11434")]
    assert "(ollama, other-model)" in out


def test_provider_and_model_flags_together(tmp_path):
    code, _, _, factory = run(
        tmp_path,
        HP_OK + LAP_OK + OFF_OK,
        "--provider",
        "ollama",
        "--model",
        "m2",
        env=ANTHROPIC_ENV,
    )
    assert code == 0
    assert factory.calls == [("ollama", "m2", None, "http://localhost:11434")]


def test_without_flags_the_environment_decides(tmp_path):
    code, _, _, factory = run(tmp_path, HP_OK + LAP_OK + OFF_OK, env=ANTHROPIC_ENV)
    assert code == 0
    assert factory.calls == [("anthropic", "claude-env-model", "test-key-not-real", None)]


def test_unknown_provider_flag_exits_2_listing_the_known_ones(tmp_path, capsys):
    code, _, _, factory = run(tmp_path, [], "--provider", "nope")
    assert code == 2
    assert factory.calls == []
    assert "ollama" in capsys.readouterr().err


def test_anthropic_flag_without_a_key_exits_2(tmp_path):
    code, out, err, factory = run(tmp_path, [], "--provider", "anthropic")
    assert code == 2
    assert "Missing ANTHROPIC_API_KEY" in err
    assert factory.calls == []


# --- §9 B5, B6: the report keeps everything -------------------------------


DIMS = {"feature": "headphones", "scenario": "several-matches", "persona": "a gift buyer"}
DIM_CASES = [{**CASES[0], "dimensions": DIMS}, *CASES[1:]]


def test_the_report_keeps_turns_tools_with_results_and_guardrails(tmp_path):
    run(tmp_path, HP_OK + LAP_OK + OFF_OK, cases=DIM_CASES)
    first = report_of(tmp_path)["cases"][0]
    assert first["turns"] == [
        {"text": None, "tools": ["search_products"]},
        {"text": "Try the Auralis Calm 300 (P-001) at 189 euros.", "tools": []},
    ]
    (call,) = first["tools"]
    assert call["name"] == "search_products"
    assert call["arguments"] == {"category": "headphones", "max_price": 200}
    expected = search_tool(load_catalogue()).run({"category": "headphones", "max_price": 200})
    assert call["results"] == expected
    assert call["results"][0]["id"] == "P-006"  # the products the model saw, cheapest first
    assert call["error"] is False
    assert [g["stage"] for g in first["guardrails"]] == ["input", "output"]
    assert all(set(g) == {"stage", "allowed", "reason"} for g in first["guardrails"])
    assert first["guardrails"][0]["allowed"] is True


def test_dimensions_are_recorded_only_for_cases_that_have_them(tmp_path):
    run(tmp_path, HP_OK + LAP_OK + OFF_OK, cases=DIM_CASES)
    cases = report_of(tmp_path)["cases"]
    assert cases[0]["dimensions"] == DIMS
    assert "dimensions" not in cases[1]


def test_prompt_sha256_is_the_hash_of_the_shipped_system_prompt(tmp_path):
    run(tmp_path, HP_OK + LAP_OK + OFF_OK)
    assert (
        report_of(tmp_path)["prompt_sha256"]
        == hashlib.sha256(SYSTEM_PROMPT_PATH.read_bytes()).hexdigest()
    )


def test_a_bad_tool_call_is_recorded_as_an_error(tmp_path):
    bad_call = [
        ModelTurn(tool_calls=(ToolCall("c1", "search_products", {"colour": "red"}),)),
        ModelTurn(text="Sorry."),
    ]
    run(tmp_path, bad_call + LAP_OK + OFF_OK)
    (call,) = report_of(tmp_path)["cases"][0]["tools"]
    assert call["arguments"] == {"colour": "red"}
    assert call["results"] == []
    assert call["error"] is True


def test_a_case_that_errors_keeps_what_was_recorded_before(tmp_path):
    script = [
        ModelTurn(tool_calls=(ToolCall("c1", "search_products", {"category": "headphones"}),)),
        ModelError("boom"),
    ]
    run(tmp_path, script + LAP_OK + OFF_OK)
    first = report_of(tmp_path)["cases"][0]
    assert first["status"] == "ERROR"
    assert len(first["tools"]) == 1 and first["tools"][0]["results"]
    assert len(first["turns"]) == 1


def test_the_wrapped_tool_returns_exactly_what_the_tool_returns():
    tool = search_tool(load_catalogue())
    tracer = RecordingTracer()
    wrapped = _recording_tool(tool, tracer)
    args = {"category": "laptop", "max_price": 700}
    assert wrapped.spec is tool.spec
    assert wrapped.run(dict(args)) == tool.run(dict(args))
    tracer.tool("search_products", args, 1, False)  # the agent reports after the run
    assert tracer.tools[0]["results"] == tool.run(dict(args))


def test_the_wrapped_tool_reraises_what_the_tool_raises():
    tool = search_tool(load_catalogue())
    tracer = RecordingTracer()
    wrapped = _recording_tool(tool, tracer)
    with pytest.raises(ToolError):
        wrapped.run({"colour": "red"})
    tracer.tool("search_products", {"colour": "red"}, 0, True)
    assert tracer.tools[0]["error"] is True and tracer.tools[0]["results"] == []


def test_an_unknown_tool_call_is_recorded_in_order_with_error_true(tmp_path):
    script = [
        ModelTurn(tool_calls=(ToolCall("c1", "get_product", {"id": "P-001"}),)),
        ModelTurn(
            tool_calls=(
                ToolCall("c2", "search_products", {"category": "headphones", "max_price": 200}),
            )
        ),
        ModelTurn(text="Try the Auralis Calm 300 (P-001) at 189 euros."),
    ]
    run(tmp_path, script + LAP_OK + OFF_OK)
    first = report_of(tmp_path)["cases"][0]
    assert [t["name"] for t in first["tools"]] == ["get_product", "search_products"]
    assert first["tools"][0]["error"] is True
    assert first["tools"][0]["arguments"] == {"id": "P-001"}
    assert first["tools"][0]["results"] == []
    assert first["tools"][1]["error"] is False
    assert first["tools"][1]["results"][0]["id"] == "P-006"
    assert [t["tools"] for t in first["turns"]] == [["get_product"], ["search_products"], []]


def test_recording_tracer_keeps_searches_turns_and_guardrails():
    t = RecordingTracer()
    t.check("input", False, "why")
    t.generation("m", Usage(), "hi", ["a", "b"])
    t.tool("search_products", {"category": "laptop"}, 1, False)
    t.tool("other", {"x": 1}, 0, True)
    assert t.guardrails == [{"stage": "input", "allowed": False, "reason": "why"}]
    assert t.turns == [{"text": "hi", "tools": ["a", "b"]}]
    assert t.searches == [{"category": "laptop"}]
