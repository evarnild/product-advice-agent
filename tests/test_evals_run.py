import io
import json
from datetime import UTC, datetime

from advisor.evals.run import main
from advisor.models.base import (
    ModelError,
    ModelNotAvailableError,
    ModelTurn,
    ModelUnreachableError,
    ToolCall,
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


def run(tmp_path, script, *extra, cases=CASES, env=ENV):
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
        now=lambda: CLOCK_TIME,
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
