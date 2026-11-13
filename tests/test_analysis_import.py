"""§10: `advisor-analysis import` over a fake `Annotations` (B12-B18, AC6, AC7)."""

import io
import json
from datetime import timedelta

import pytest

from advisor.evals.analysis import main
from advisor.evals.annotate import AnnotationError, Score
from advisor.evals.labels import label_line, parse_labels
from tests.fake_langfuse_api import T0
from tests.test_analysis_queue import LANGFUSE_ENV, STAMP, report_file, trace


@pytest.fixture(autouse=True)
def _in_tmp(tmp_path, monkeypatch):
    # The default labels path is relative to the working directory.
    monkeypatch.chdir(tmp_path)


TRACES = [trace("ta", "a"), trace("tb", "b"), trace("tc", "c"), trace("td", "d")]


def score(tid, value, comment="", minutes=0):
    return Score(tid, value, comment, T0 + timedelta(minutes=minutes))


class FakeAnnotations:
    def __init__(self, scores=(), traces=TRACES, queue_id="q-1", fail_at=None):
        self.scores = list(scores)
        self.traces = list(traces)
        self.queue_id = queue_id
        self.fail_at = fail_at
        self.calls = []

    def _maybe_fail(self, step):
        if self.fail_at == step:
            raise AnnotationError(step, "RuntimeError: boom")

    def ensure_score_config(self):
        raise AssertionError("import must not create a config")

    def ensure_queue(self, name, config_id):
        raise AssertionError("import must not create a queue")

    def find_queue(self, name):
        self.calls.append(("find_queue", name))
        self._maybe_fail("queue")
        return self.queue_id

    def run_traces(self, stamp):
        self.calls.append(("run_traces", stamp))
        self._maybe_fail("traces")
        return self.traces

    def queued_trace_ids(self, queue_id):
        raise AssertionError("import must not read items")

    def add_trace(self, queue_id, trace_id):
        raise AssertionError("import must not add items")

    def annotation_scores(self, queue_id):
        self.calls.append(("annotation_scores", queue_id))
        self._maybe_fail("scores")
        return self.scores


def run(argv, annotations, *, env=LANGFUSE_ENV):
    out, err = io.StringIO(), io.StringIO()
    made = []

    def factory(e):
        made.append(e)
        return annotations

    code = main(list(argv), env=env, out=out, err=err, annotations_factory=factory)
    return code, out.getvalue(), err.getvalue(), made


def records(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]


def test_scores_become_label_lines_in_the_default_labels_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = report_file(tmp_path)
    fake = FakeAnnotations([score("ta", True), score("tb", False, "wrong price")])
    code, out, err, _ = run(["import", str(path)], fake)
    assert code == 0, err
    labels = tmp_path / "evals" / "labels" / "run.jsonl"  # <report stem>.jsonl
    first, second = records(labels)
    assert (first["case_id"], first["label"], first["critique"]) == ("a", "pass", "")
    assert (second["case_id"], second["label"], second["critique"]) == ("b", "fail", "wrong price")
    assert second["question"] == "q b" and second["answer"] == "a b"
    assert out.strip() == (
        "import: 2 labels written, 0 unchanged, 0 fail without critique, 0 outside the run"
    )
    assert ("find_queue", f"advisor-eval {STAMP}") in fake.calls
    assert ("annotation_scores", "q-1") in fake.calls


def test_labels_and_queue_flags_are_honoured(tmp_path):
    labels = tmp_path / "mine.jsonl"
    fake = FakeAnnotations([score("ta", True)])
    code, _, _, _ = run(
        ["import", str(report_file(tmp_path)), "--labels", str(labels), "--queue", "other"], fake
    )
    assert code == 0 and len(records(labels)) == 1
    assert ("find_queue", "other") in fake.calls


def test_a_second_import_appends_nothing(tmp_path):
    labels = tmp_path / "l.jsonl"
    scores = [score("ta", True), score("tb", False, "wrong")]
    args = ["import", str(report_file(tmp_path)), "--labels", str(labels)]
    run(args, FakeAnnotations(scores))
    before = labels.read_bytes()
    code, out, _, _ = run(args, FakeAnnotations(scores))
    assert code == 0 and labels.read_bytes() == before
    assert "0 labels written, 2 unchanged" in out


def test_the_latest_score_wins_and_a_changed_score_is_appended(tmp_path):
    labels = tmp_path / "l.jsonl"
    args = ["import", str(report_file(tmp_path)), "--labels", str(labels)]
    run(args, FakeAnnotations([score("tb", True, "", 1)]))
    run(args, FakeAnnotations([score("tb", True, "", 1), score("tb", False, "changed my mind", 5)]))
    rows = records(labels)
    assert [(r["label"], r["critique"]) for r in rows] == [
        ("pass", ""),
        ("fail", "changed my mind"),
    ]
    assert parse_labels(labels.read_text(encoding="utf-8"))["b"].label == "fail"


def test_scores_outside_the_run_are_counted_and_not_written(tmp_path):
    labels = tmp_path / "l.jsonl"
    fake = FakeAnnotations([score("ta", True), score("foreign", False, "x")])
    code, out, _, _ = run(["import", str(report_file(tmp_path)), "--labels", str(labels)], fake)
    assert code == 0
    assert [r["case_id"] for r in records(labels)] == ["a"]
    assert out.strip().endswith("1 outside the run")


def test_a_fail_without_a_comment_is_not_written_and_its_case_is_printed(tmp_path):
    labels = tmp_path / "l.jsonl"
    fake = FakeAnnotations([score("ta", False), score("tb", False, "  "), score("tc", True)])
    code, out, _, _ = run(["import", str(report_file(tmp_path)), "--labels", str(labels)], fake)
    assert code == 0
    assert [r["case_id"] for r in records(labels)] == ["c"]
    assert "a, b" in out and "without a critique" in out
    assert "2 fail without critique" in out


def test_nothing_to_write_creates_no_file(tmp_path):
    labels = tmp_path / "sub" / "l.jsonl"
    code, out, _, _ = run(
        ["import", str(report_file(tmp_path)), "--labels", str(labels)], FakeAnnotations([])
    )
    assert code == 0 and not labels.exists()
    assert out.strip().startswith("import: 0 labels written")


def test_viewer_lines_stay_and_the_last_line_wins(tmp_path):
    labels = tmp_path / "l.jsonl"
    viewer = label_line("a", "pass", "", T0, "q a", "a a")
    labels.write_text(viewer, encoding="utf-8")
    run(
        ["import", str(report_file(tmp_path)), "--labels", str(labels)],
        FakeAnnotations([score("ta", False, "bad")]),
    )
    text = labels.read_text(encoding="utf-8")
    assert text.startswith(viewer)  # never rewritten
    assert parse_labels(text)["a"].label == "fail"


def test_a_file_without_a_final_newline_gets_one_before_the_append(tmp_path):
    labels = tmp_path / "l.jsonl"
    labels.write_text(label_line("c", "pass", "", T0, "q", "a").rstrip("\n"), encoding="utf-8")
    run(
        ["import", str(report_file(tmp_path)), "--labels", str(labels)],
        FakeAnnotations([score("ta", True)]),
    )
    assert [r["case_id"] for r in records(labels)] == ["c", "a"]


def test_an_imported_file_feeds_counts(tmp_path):
    labels = tmp_path / "l.jsonl"
    report = report_file(tmp_path)
    run(
        ["import", str(report), "--labels", str(labels)],
        FakeAnnotations([score("ta", False, "bad"), score("tb", True)]),
    )
    taxonomy = tmp_path / "tax.json"
    taxonomy.write_text(
        json.dumps(
            {
                "labels": str(labels),
                "modes": [{"id": "m1", "name": "One", "description": "d"}],
                "mapping": {"a": ["m1"]},
            }
        ),
        encoding="utf-8",
    )
    out, err = io.StringIO(), io.StringIO()
    code = main(
        ["counts", str(report), "--labels", str(labels), "--taxonomy", str(taxonomy)],
        env={},
        out=out,
        err=err,
    )
    assert code == 0, err.getvalue()
    assert "| m1 | One | 1 |" in out.getvalue()


def test_a_queue_that_does_not_exist_exits_2(tmp_path):
    labels = tmp_path / "l.jsonl"
    fake = FakeAnnotations([score("ta", True)], queue_id=None)
    code, _, err, _ = run(["import", str(report_file(tmp_path)), "--labels", str(labels)], fake)
    assert code == 2 and f"advisor-eval {STAMP}" in err and "queue" in err
    assert not labels.exists() and ("annotation_scores", None) not in fake.calls


@pytest.mark.parametrize("missing", ["LANGFUSE_HOST", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"])
def test_a_missing_variable_exits_2_without_calling_langfuse(tmp_path, missing):
    env = {k: v for k, v in LANGFUSE_ENV.items() if k != missing}
    fake = FakeAnnotations([score("ta", True)])
    code, _, err, made = run(["import", str(report_file(tmp_path))], fake, env=env)
    assert code == 2 and missing in err and made == [] and fake.calls == []


@pytest.mark.parametrize("step", ["queue", "traces", "scores"])
def test_a_failed_read_writes_nothing_and_exits_2(tmp_path, step):
    labels = tmp_path / "l.jsonl"
    fake = FakeAnnotations([score("ta", True)], fail_at=step)
    code, _, err, _ = run(["import", str(report_file(tmp_path)), "--labels", str(labels)], fake)
    assert code == 2 and not labels.exists()
    assert err.strip() == f"Langfuse {step} failed: RuntimeError: boom"
    assert "sk-secret-private" not in err


def test_a_labels_file_that_does_not_parse_exits_2_before_langfuse(tmp_path):
    labels = tmp_path / "l.jsonl"
    labels.write_text("{oops", encoding="utf-8")
    fake = FakeAnnotations([score("ta", True)])
    code, _, err, _ = run(["import", str(report_file(tmp_path)), "--labels", str(labels)], fake)
    assert code == 2 and "Labels file error" in err and fake.calls == []
    assert labels.read_text(encoding="utf-8") == "{oops"


def test_a_report_that_cannot_be_read_exits_2(tmp_path):
    fake = FakeAnnotations()
    code, _, err, _ = run(["import", str(tmp_path / "none.json")], fake)
    assert code == 2 and "Cannot read" in err and fake.calls == []


def test_duplicate_run_traces_print_the_count(tmp_path):
    labels = tmp_path / "l.jsonl"
    fake = FakeAnnotations(
        [score("new", True)], traces=[trace("old", "a", 1), trace("new", "a", 9)]
    )
    code, out, _, _ = run(["import", str(report_file(tmp_path)), "--labels", str(labels)], fake)
    assert code == 0 and "1 duplicate trace" in out
    assert [r["case_id"] for r in records(labels)] == ["a"]
