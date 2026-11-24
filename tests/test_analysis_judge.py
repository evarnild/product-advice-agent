"""§16: `advisor-analysis judge` over a fake model and fake Langfuse (B5, B8-B11, AC4, AC6)."""

import json
from datetime import timedelta

import pytest

from advisor.evals.annotate import AnnotationError, RunTrace
from advisor.evals.judge import VERDICT_SCHEMA, score_id
from advisor.models.base import ModelError, ModelUnreachableError
from tests.fake_langfuse_api import T0
from tests.judge_world import (
    ENV,
    LABELS_FILE,
    LANGFUSE_ENV,
    STAMP,
    RoutedClient,
    question,
    run,
    verdict,
    write_world,
)

IN_SCOPE = ["f1", "p1", "h1", "h2", "h3"]  # x1 is exact-match


def judge_argv(w, *extra):
    return [
        "judge",
        str(w["report"]),
        "--split",
        str(w["split"]),
        "--labels-dir",
        str(w["labels_dir"]),
        "--runs-dir",
        str(w["runs_dir"]),
        "--judgements-dir",
        str(w["judgements"]),
        *extra,
    ]


ANSWERS = {
    "f1": verdict(False, "implies a fit"),
    "p1": verdict(True, "plainly says none"),
    "h1": verdict(True, "ok"),
    "h2": "I cannot tell",
    "h3": verdict(False, "wrong kind"),
}
WITH_LANGFUSE = {**ENV, **LANGFUSE_ENV}


class FakeAnnotations:
    def __init__(self, traces=(), fail_at=None):
        self.traces = list(traces)
        self.fail_at = fail_at
        self.calls = []
        self.envs = []
        self.written = []
        self.config_calls = 0

    def ensure_judge_config(self):
        self.config_calls += 1
        if self.fail_at == "config":
            raise AnnotationError("config", "boom")
        return "cfg-j"

    def run_traces(self, stamp):
        self.calls.append(("run_traces", stamp))
        return self.traces

    def write_scores(self, scores, config_id):
        if self.fail_at == "score-write":
            raise AnnotationError("score-write", "RuntimeError: ***")
        self.written.append((list(scores), config_id))

    def __getattr__(self, name):  # no queue, no pass config, no annotation read
        raise AssertionError(f"judge must not call annotations.{name}")


def trace(tid, cid, minutes=0):
    return RunTrace(tid, ("eval", f"run:{STAMP}", f"case:{cid}"), T0 + timedelta(minutes=minutes))


def test_without_langfuse_it_judges_in_scope_cases_writes_the_file_and_says_so(tmp_path):
    w = write_world(tmp_path)
    client = RoutedClient(ANSWERS)
    code, out, err, _ = run(judge_argv(w), client=client)
    assert code == 0, err
    lines = out.splitlines()
    assert lines[:5] == [
        "FAIL f1: implies a fit",
        "PASS p1: plainly says none",
        "PASS h1: ok",
        "ERROR h2: the model answer is not a JSON object",
        "FAIL h3: wrong kind",
    ]
    assert "judged 5: 2 pass, 2 fail, 1 error" in lines
    assert len(client.prompts) == 5  # x1 (exact-match) is not judged
    assert any("Langfuse is not configured" in line for line in lines)
    text = (w["judgements"] / "L.jsonl").read_text(encoding="utf-8")
    records = [json.loads(line) for line in text.splitlines()]
    assert [r["case_id"] for r in records] == IN_SCOPE
    assert [r["pass"] for r in records] == [False, True, True, None, False]
    first = records[0]
    assert first["reason"] == "implies a fit"
    assert first["model"] == "claude-haiku-5-5"
    assert len(first["prompt_sha256"]) == 64
    assert first["judged_at"].endswith("Z")
    assert len({r["prompt_sha256"] for r in records}) == 1


def test_the_provider_is_anthropic_whatever_the_advisor_settings_say(tmp_path):
    w = write_world(tmp_path)
    env = {**ENV, "ADVISOR_MODEL_PROVIDER": "ollama", "ADVISOR_MODEL": "qwen3:8b"}
    code, _, err, factory = run(judge_argv(w), env=env, client=RoutedClient(ANSWERS))
    assert code == 0, err
    assert factory.calls == [("anthropic", "claude-haiku-5-5", "sk-ant-test-key", None)]


def test_model_option_changes_the_model_not_the_provider(tmp_path):
    w = write_world(tmp_path)
    args = judge_argv(w, "--model", "claude-other")
    code, _, err, factory = run(args, client=RoutedClient(ANSWERS))
    assert code == 0, err
    assert factory.calls[0][:2] == ("anthropic", "claude-other")
    assert '"model": "claude-other"' in (w["judgements"] / "L.jsonl").read_text(encoding="utf-8")


def test_without_the_key_it_exits_2_before_any_client_is_built(tmp_path):
    w = write_world(tmp_path)
    code, out, err, factory = run(judge_argv(w), env={"ADVISOR_MODEL_PROVIDER": "anthropic"})
    assert code == 2
    assert "Missing ANTHROPIC_API_KEY" in err
    assert factory.calls == []
    assert out == ""
    assert not w["judgements"].exists()


def test_the_prompt_has_the_few_shot_examples_and_no_held_out_conversation(tmp_path):
    w = write_world(tmp_path)
    client = RoutedClient(ANSWERS)
    code, _, err, _ = run(judge_argv(w), client=client)
    assert code == 0, err
    examples = client.prompts[0].split("Now judge this conversation.")[0]
    assert question("f1") in examples and question("p1") in examples
    assert "Smartwatches are not headphones." in examples
    assert "Owner's verdict: FAIL" in examples and "Owner's verdict: PASS" in examples
    for held_out in ("h1", "h2", "h3"):
        assert question(held_out) not in examples
    assert "Name-f1" in examples  # the example's tool rows come from its report


def test_labels_are_byte_identical_after_a_run(tmp_path):
    w = write_world(tmp_path)
    before = (w["labels_dir"] / LABELS_FILE).read_bytes()
    run(judge_argv(w), client=RoutedClient(ANSWERS))
    assert (w["labels_dir"] / LABELS_FILE).read_bytes() == before


def test_every_judge_call_asks_for_the_verdict_schema(tmp_path):
    w = write_world(tmp_path)
    client = RoutedClient(ANSWERS)
    run(judge_argv(w), client=client)
    assert client.schemas == [VERDICT_SCHEMA] * 5


def test_a_refusal_is_an_error_line_naming_it(tmp_path):
    w = write_world(tmp_path)
    refusal = ModelError("Anthropic refused to give the structured reply (stop_reason: refusal)")
    code, out, _, _ = run(judge_argv(w), client=RoutedClient({**ANSWERS, "h1": refusal}))
    assert code == 0
    assert "ERROR h1: Anthropic refused to give the structured reply (stop_reason: refusal)" in out


def test_a_model_failure_is_an_error_line_not_a_verdict(tmp_path):
    w = write_world(tmp_path)
    answers = {**ANSWERS, "h1": ModelUnreachableError("Anthropic is down")}
    code, out, _, _ = run(judge_argv(w), client=RoutedClient(answers))
    assert code == 0
    assert "ERROR h1: Anthropic is down" in out


def test_a_report_without_in_scope_cases_exits_2(tmp_path):
    w = write_world(
        tmp_path,
        cases={"x1": ("exact-match", "pass", "")},
        split={"few_shot": [], "held_out": []},
    )
    code, _, err, _ = run(judge_argv(w), client=RoutedClient({}))
    assert code == 2
    assert "No in-scope case" in err


def test_a_split_with_one_label_only_exits_2_before_any_call(tmp_path):
    split = {"few_shot": [f"{LABELS_FILE}#f1"], "held_out": [f"{LABELS_FILE}#h1"]}
    w = write_world(tmp_path, split=split)
    client = RoutedClient(ANSWERS)
    code, _, err, _ = run(judge_argv(w), client=client)
    assert code == 2
    assert "pass and one fail" in err
    assert client.prompts == []


def test_a_few_shot_example_without_its_report_exits_2(tmp_path):
    w = write_world(tmp_path)
    report = w["runs_dir"] / "other.json"
    (w["runs_dir"] / "L.json").rename(report)
    w["report"] = report
    code, _, err, _ = run(judge_argv(w), client=RoutedClient(ANSWERS))
    assert code == 2
    assert "few-shot example" in err


# --- B8-B11: the Langfuse scores ------------------------------------------------


def test_scores_go_only_to_traced_verdicts_with_the_reason_and_a_deterministic_id(tmp_path):
    w = write_world(tmp_path)
    fake = FakeAnnotations([trace("t-f1", "f1"), trace("t-h1", "h1"), trace("t-h2", "h2")])
    code, out, err, _ = run(
        judge_argv(w), env=WITH_LANGFUSE, client=RoutedClient(ANSWERS), annotations=fake
    )
    assert code == 0, err
    assert fake.calls == [("run_traces", STAMP)]
    assert fake.config_calls == 1
    ((scores, config_id),) = fake.written
    assert config_id == "cfg-j"
    # h2 was a judge error: no score; p1 and h3 have no trace
    assert [(s.trace_id, s.value, s.comment) for s in scores] == [
        ("t-f1", False, "implies a fit"),
        ("t-h1", True, "ok"),
    ]
    assert scores[0].score_id == score_id(STAMP, "f1")
    assert "judge-no-fit: 2 scored, 2 no trace" in out
    assert "not configured" not in out
    assert fake.envs[0]["LANGFUSE_HOST"] == "http://langfuse.invalid"


def test_a_second_run_sends_the_same_ids_and_rewrites_the_file(tmp_path):
    w = write_world(tmp_path)
    traces = [trace("t-f1", "f1"), trace("t-p1", "p1")]
    ids = []
    for _ in range(2):
        fake = FakeAnnotations(traces)
        code, _, err, _ = run(
            judge_argv(w), env=WITH_LANGFUSE, client=RoutedClient(ANSWERS), annotations=fake
        )
        assert code == 0, err
        ids.append([s.score_id for s in fake.written[0][0]])
    assert ids[0] == ids[1] and len(ids[0]) == 2
    lines = (w["judgements"] / "L.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 5  # the file is rewritten, not appended to


@pytest.mark.parametrize("step", ["config", "score-write"])
def test_a_langfuse_error_exits_2_naming_the_step_after_the_file_is_written(tmp_path, step):
    w = write_world(tmp_path)
    fake = FakeAnnotations([trace("t-f1", "f1")], fail_at=step)
    code, _, err, _ = run(
        judge_argv(w), env=WITH_LANGFUSE, client=RoutedClient(ANSWERS), annotations=fake
    )
    assert code == 2
    assert f"Langfuse {step} failed" in err
    assert (w["judgements"] / "L.jsonl").exists()


def test_a_report_without_a_started_time_cannot_be_scored(tmp_path):
    w = write_world(tmp_path)
    report = json.loads(w["report"].read_text(encoding="utf-8"))
    del report["started"]
    w["report"].write_text(json.dumps(report), encoding="utf-8")
    code, _, err, _ = run(
        judge_argv(w),
        env=WITH_LANGFUSE,
        client=RoutedClient(ANSWERS),
        annotations=FakeAnnotations(),
    )
    assert code == 2
    assert "no 'started' time" in err


def test_a_partial_langfuse_configuration_writes_the_file_only(tmp_path):
    w = write_world(tmp_path)
    partial = {**ENV, "LANGFUSE_HOST": "http://langfuse.invalid", "LANGFUSE_PUBLIC_KEY": "pk"}
    fake = FakeAnnotations([trace("t-f1", "f1")])
    code, out, err, _ = run(
        judge_argv(w), env=partial, client=RoutedClient(ANSWERS), annotations=fake
    )
    assert code == 0, err
    assert "Langfuse is not configured" in out
    assert fake.envs == [] and fake.calls == [] and fake.written == []


def test_an_out_of_scope_few_shot_case_exits_2_before_any_call(tmp_path):
    split = {
        "few_shot": [f"{LABELS_FILE}#f1", f"{LABELS_FILE}#x1"],  # x1 is exact-match
        "held_out": [f"{LABELS_FILE}#h1"],
    }
    w = write_world(tmp_path, split=split)
    client = RoutedClient(ANSWERS)
    code, out, err, _ = run(judge_argv(w), client=client)
    assert code == 2
    assert "few-shot example" in err and "x1" in err and "not in scope" in err
    assert client.prompts == []
