"""§10: `advisor-analysis queue` over a fake `Annotations` (B5-B11, AC5, AC7)."""

import io
import json

import pytest

from advisor.evals.analysis import main
from advisor.evals.annotate import AnnotationError, RunTrace
from tests.fake_langfuse_api import T0

LANGFUSE_ENV = {
    "ADVISOR_MODEL_PROVIDER": "ollama",
    "ADVISOR_MODEL": "m",
    "LANGFUSE_HOST": "http://langfuse.invalid",
    "LANGFUSE_PUBLIC_KEY": "pk-secret-public",
    "LANGFUSE_SECRET_KEY": "sk-secret-private",
}
STAMP = "20261112T103005Z"


def case(cid, status, feature, scenario, persona="p"):
    return {
        "id": cid,
        "question": f"q {cid}",
        "answer": f"a {cid}",
        "status": status,
        "dimensions": {"feature": feature, "scenario": scenario, "persona": persona},
    }


REPORT = {
    "started": "2026-11-12T10:30:05+00:00",
    "cases": [
        case("a", "PASS", "laptop", "no-match"),
        case("b", "FAIL", "laptop", "out-of-stock"),
        case("c", "FAIL", "phone", "out-of-stock"),
        case("d", "ERROR", "phone", "exact-match"),
    ],
}


def trace(tid, cid, minutes=0):
    from datetime import timedelta

    return RunTrace(tid, ("eval", f"run:{STAMP}", f"case:{cid}"), T0 + timedelta(minutes=minutes))


class FakeAnnotations:
    def __init__(self, traces=(), queued=(), fail_at=None, fail_add_after=None):
        self.traces = list(traces)
        self.queued = set(queued)
        self.fail_at = fail_at
        self.fail_add_after = fail_add_after
        self.calls = []
        self.added = []

    def _maybe_fail(self, step):
        if self.fail_at == step:
            raise AnnotationError(step, "RuntimeError: boom")

    def ensure_score_config(self):
        self.calls.append("ensure_score_config")
        self._maybe_fail("config")
        return "cfg-1"

    def ensure_queue(self, name, config_id):
        self.calls.append(("ensure_queue", name, config_id))
        self._maybe_fail("queue")
        return "q-1"

    def find_queue(self, name):
        raise AssertionError("queue must not look a queue up without creating it")

    def run_traces(self, stamp):
        self.calls.append(("run_traces", stamp))
        self._maybe_fail("traces")
        return self.traces

    def queued_trace_ids(self, queue_id):
        self.calls.append(("queued_trace_ids", queue_id))
        return set(self.queued)

    def add_trace(self, queue_id, trace_id):
        if self.fail_add_after is not None and len(self.added) >= self.fail_add_after:
            raise AnnotationError("add", "RuntimeError: boom")
        self.added.append((queue_id, trace_id))

    def annotation_scores(self, queue_id):
        raise AssertionError("queue must not read scores")


class Factory:
    def __init__(self, annotations):
        self.annotations = annotations
        self.envs = []

    def __call__(self, env):
        self.envs.append(dict(env))
        return self.annotations


def report_file(tmp_path, report=REPORT):
    path = tmp_path / "run.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


def run(argv, annotations=None, *, env=LANGFUSE_ENV):
    out, err = io.StringIO(), io.StringIO()
    factory = Factory(annotations if annotations is not None else FakeAnnotations())
    code = main(list(argv), env=env, out=out, err=err, annotations_factory=factory)
    return code, out.getvalue(), err.getvalue(), factory


ALL_TRACES = [trace("ta", "a"), trace("tb", "b"), trace("tc", "c"), trace("td", "d")]


def test_a_new_queue_gets_every_case_and_the_summary_line(tmp_path):
    fake = FakeAnnotations(ALL_TRACES)
    code, out, err, factory = run(["queue", str(report_file(tmp_path))], fake)
    assert code == 0, err
    assert fake.added == [("q-1", "ta"), ("q-1", "tb"), ("q-1", "tc"), ("q-1", "td")]
    assert out.strip() == f"queue advisor-eval {STAMP}: 4 added, 0 already queued, 0 no trace"
    assert ("ensure_queue", f"advisor-eval {STAMP}", "cfg-1") in fake.calls
    assert ("run_traces", STAMP) in fake.calls
    assert factory.envs[0]["LANGFUSE_HOST"] == "http://langfuse.invalid"


def test_queue_name_can_be_overridden(tmp_path):
    fake = FakeAnnotations(ALL_TRACES)
    code, out, _, _ = run(["queue", str(report_file(tmp_path)), "--queue", "my queue"], fake)
    assert code == 0
    assert ("ensure_queue", "my queue", "cfg-1") in fake.calls
    assert out.startswith("queue my queue: ")


@pytest.mark.parametrize(
    ("flags", "expected"),
    [
        (["--feature", "laptop"], ["ta", "tb"]),
        (["--scenario", "out-of-stock"], ["tb", "tc"]),
        (["--persona", "p"], ["ta", "tb", "tc", "td"]),
        (["--status", "FAIL"], ["tb", "tc"]),
        (["--scenario", "out-of-stock", "--feature", "phone"], ["tc"]),
    ],
)
def test_filters_choose_the_cases_to_queue(tmp_path, flags, expected):
    fake = FakeAnnotations(ALL_TRACES)
    code, _, err, _ = run(["queue", str(report_file(tmp_path)), *flags], fake)
    assert code == 0, err
    assert [t for _, t in fake.added] == expected


def test_a_bad_status_is_a_usage_error(tmp_path):
    fake = FakeAnnotations(ALL_TRACES)
    code, _, err, factory = run(["queue", str(report_file(tmp_path)), "--status", "MAYBE"], fake)
    assert code == 2 and factory.envs == [] and fake.calls == [] and fake.added == []
    assert "No case" not in err


def test_traces_already_queued_are_skipped_and_counted(tmp_path):
    fake = FakeAnnotations(ALL_TRACES, queued={"tb"})
    code, out, _, _ = run(["queue", str(report_file(tmp_path))], fake)
    assert code == 0
    assert [t for _, t in fake.added] == ["ta", "tc", "td"]
    assert out.strip().endswith("3 added, 1 already queued, 0 no trace")


def test_a_second_run_with_everything_queued_adds_nothing(tmp_path):
    fake = FakeAnnotations(ALL_TRACES, queued={"ta", "tb", "tc", "td"})
    code, out, _, _ = run(["queue", str(report_file(tmp_path))], fake)
    assert code == 0 and fake.added == []
    assert "0 added, 4 already queued" in out


def test_cases_without_a_trace_are_counted_not_failed(tmp_path):
    fake = FakeAnnotations([trace("ta", "a"), trace("other", "zzz")])
    code, out, _, _ = run(["queue", str(report_file(tmp_path))], fake)
    assert code == 0
    assert [t for _, t in fake.added] == ["ta"]
    assert out.strip().endswith("1 added, 0 already queued, 3 no trace")


def test_duplicate_case_traces_use_the_latest_and_print_the_count(tmp_path):
    fake = FakeAnnotations([trace("old", "a", 1), trace("new", "a", 9), trace("tb", "b")])
    code, out, _, _ = run(["queue", str(report_file(tmp_path)), "--feature", "laptop"], fake)
    assert code == 0
    assert [t for _, t in fake.added] == ["new", "tb"]
    assert "1 duplicate trace" in out


def test_no_duplicates_prints_no_duplicate_line(tmp_path):
    code, out, _, _ = run(["queue", str(report_file(tmp_path))], FakeAnnotations(ALL_TRACES))
    assert code == 0 and "duplicate" not in out


@pytest.mark.parametrize("missing", ["LANGFUSE_HOST", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"])
def test_a_missing_variable_exits_2_naming_it_without_calling_langfuse(tmp_path, missing):
    env = {k: v for k, v in LANGFUSE_ENV.items() if k != missing}
    code, out, err, factory = run(["queue", str(report_file(tmp_path))], env=env)
    assert code == 2 and missing in err and out == ""
    assert factory.envs == [] and factory.annotations.calls == []


def test_all_missing_variables_are_named(tmp_path):
    code, _, err, factory = run(["queue", str(report_file(tmp_path))], env={})
    assert code == 2 and factory.envs == []
    for name in ("LANGFUSE_HOST", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"):
        assert name in err


@pytest.mark.parametrize("step", ["config", "queue", "traces"])
def test_a_langfuse_error_before_any_add_exits_2_with_the_step(tmp_path, step):
    fake = FakeAnnotations(ALL_TRACES, fail_at=step)
    code, out, err, _ = run(["queue", str(report_file(tmp_path))], fake)
    assert code == 2 and fake.added == []
    assert err.strip() == f"Langfuse {step} failed: RuntimeError: boom"


def test_an_error_after_some_adds_keeps_them_and_exits_2(tmp_path):
    fake = FakeAnnotations(ALL_TRACES, fail_add_after=2)
    code, out, err, _ = run(["queue", str(report_file(tmp_path))], fake)
    assert code == 2
    assert [t for _, t in fake.added] == ["ta", "tb"]
    assert "Langfuse add failed" in err
    assert "2 added" in err or "2 added" in out


def test_the_factory_failing_is_reported_like_any_langfuse_error(tmp_path):
    def broken(env):
        raise AnnotationError("config", "ValueError: bad host")

    out, err = io.StringIO(), io.StringIO()
    code = main(
        ["queue", str(report_file(tmp_path))],
        env=LANGFUSE_ENV,
        out=out,
        err=err,
        annotations_factory=broken,
    )
    assert code == 2 and err.getvalue().strip() == "Langfuse config failed: ValueError: bad host"


def test_the_keys_never_reach_the_output(tmp_path):
    fake = FakeAnnotations(ALL_TRACES, fail_add_after=1)
    _, out, err, _ = run(["queue", str(report_file(tmp_path))], fake)
    for text in (out, err):
        assert "sk-secret-private" not in text and "pk-secret-public" not in text


def test_a_report_that_cannot_be_read_exits_2(tmp_path):
    code, _, err, factory = run(["queue", str(tmp_path / "none.json")])
    assert code == 2 and "Cannot read" in err and factory.annotations.calls == []
    bad = tmp_path / "bad.json"
    bad.write_text("{oops", encoding="utf-8")
    assert run(["queue", str(bad)])[0] == 2


def test_a_report_without_a_started_time_exits_2_before_langfuse(tmp_path):
    path = report_file(tmp_path, {"cases": REPORT["cases"]})
    code, _, err, factory = run(["queue", str(path)])
    assert code == 2 and "started" in err and factory.annotations.calls == []


def test_filters_matching_no_case_exit_2_without_creating_a_queue(tmp_path):
    code, _, err, factory = run(
        ["queue", str(report_file(tmp_path)), "--feature", "toaster"], FakeAnnotations(ALL_TRACES)
    )
    assert code == 2 and "No case" in err and factory.annotations.calls == []


def test_queue_never_calls_a_delete_or_update_method(tmp_path):
    fake = FakeAnnotations(ALL_TRACES)
    run(["queue", str(report_file(tmp_path))], fake)
    assert not [n for n in dir(fake) if n.startswith(("delete", "update", "remove"))]
