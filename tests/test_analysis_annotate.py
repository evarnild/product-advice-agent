"""§10 pure logic: case selection, trace matching and label building (B8, B9, B14-B16)."""

import json
from datetime import UTC, datetime, timedelta

import pytest

from advisor.evals.annotate import (
    AnnotationError,
    RunTrace,
    Score,
    case_traces,
    default_queue_name,
    labels_from_scores,
    plan_additions,
    report_stamp,
    select_cases,
)
from advisor.evals.labels import Label, parse_labels

T0 = datetime(2026, 11, 12, 10, 0, 0, tzinfo=UTC)


def case(cid, status, feature, scenario, persona="p"):
    return {
        "id": cid,
        "question": f"question {cid}",
        "answer": f"answer {cid}",
        "status": status,
        "dimensions": {"feature": feature, "scenario": scenario, "persona": persona},
    }


REPORT = {
    "started": "2026-11-12T11:30:05+01:00",
    "cases": [
        case("a", "PASS", "laptop", "no-match", "gift buyer"),
        case("b", "FAIL", "laptop", "exact-match", "gift buyer"),
        case("c", "FAIL", "phone", "no-match", "student"),
        case("d", "ERROR", "phone", "exact-match", "student"),
        {"id": "e", "question": "q", "answer": "", "status": "PASS"},  # no dimensions
    ],
}


def ids(cases):
    return [c["id"] for c in cases]


# --- stamp and name -------------------------------------------------------


def test_stamp_is_the_started_time_in_utc_as_run_py_formats_it():
    assert report_stamp(REPORT) == "20261112T103005Z"
    assert report_stamp({"started": "2026-11-12T10:30:05+00:00"}) == "20261112T103005Z"
    # a time without an offset is read as UTC
    assert report_stamp({"started": "2026-11-12T10:30:05"}) == "20261112T103005Z"


@pytest.mark.parametrize("bad", [{}, {"started": 5}, {"started": "yesterday"}])
def test_a_report_without_a_usable_started_time_is_refused(bad):
    with pytest.raises(ValueError, match="started"):
        report_stamp(bad)


def test_default_queue_name():
    assert default_queue_name("20261112T103005Z") == "advisor-eval 20261112T103005Z"


def test_annotation_error_message_has_step_and_text():
    assert str(AnnotationError("queue", "X: boom")) == "Langfuse queue failed: X: boom"


# --- B8 filters -----------------------------------------------------------


def test_no_filter_selects_every_case():
    assert ids(select_cases(REPORT)) == ["a", "b", "c", "d", "e"]


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"feature": "laptop"}, ["a", "b"]),
        ({"scenario": "no-match"}, ["a", "c"]),
        ({"persona": "student"}, ["c", "d"]),
        ({"status": "FAIL"}, ["b", "c"]),
        ({"status": "ERROR"}, ["d"]),
        ({"feature": "laptop", "scenario": "no-match"}, ["a"]),
        ({"scenario": "no-match", "status": "FAIL"}, ["c"]),
        ({"feature": "phone", "scenario": "no-match", "persona": "gift buyer"}, []),
    ],
)
def test_filters_combine_with_and(kwargs, expected):
    assert ids(select_cases(REPORT, **kwargs)) == expected


def test_a_dimension_filter_excludes_cases_without_dimensions():
    assert "e" not in ids(select_cases(REPORT, feature="laptop"))
    assert ids(select_cases(REPORT, status="PASS")) == ["a", "e"]


# --- B9 matching ----------------------------------------------------------


def trace(tid, case_id, minutes=0, extra=()):
    return RunTrace(
        tid, ("eval", "run:x", f"case:{case_id}", *extra), T0 + timedelta(minutes=minutes)
    )


def test_each_case_tag_maps_to_its_trace():
    mapping, dups = case_traces([trace("t1", "a"), trace("t2", "b")])
    assert mapping == {"a": "t1", "b": "t2"}
    assert dups == 0


def test_a_repeated_case_tag_takes_the_latest_start_and_counts_the_repeat():
    traces = [trace("old", "a", 5), trace("new", "a", 9), trace("older", "a", 1), trace("t", "b")]
    mapping, dups = case_traces(traces)
    assert mapping == {"a": "new", "b": "t"}
    assert dups == 2


def test_a_trace_without_a_case_tag_is_ignored():
    mapping, dups = case_traces([RunTrace("t", ("eval", "run:x"), T0)])
    assert (mapping, dups) == ({}, 0)


def test_case_ids_keep_their_colons_and_spaces():
    mapping, _ = case_traces([trace("t", "a:b c")])
    assert mapping == {"a:b c": "t"}


# --- B10 plan -------------------------------------------------------------


def test_plan_separates_new_queued_and_without_trace():
    selected = REPORT["cases"][:4]
    plan = plan_additions(selected, {"a": "t1", "b": "t2", "c": "t3"}, {"t2"})
    assert plan.to_add == [("a", "t1"), ("c", "t3")]
    assert plan.already_queued == 1
    assert plan.no_trace == 1  # d


# --- B14-B16 labels -------------------------------------------------------

TRACES = {"a": "ta", "b": "tb", "c": "tc"}


def score(tid, value, comment="", minutes=0):
    return Score(tid, value, comment, T0 + timedelta(minutes=minutes))


def records(result):
    return [json.loads(line) for line in result.lines]


def test_true_is_pass_and_false_with_a_comment_is_fail():
    result = labels_from_scores(
        REPORT, [score("ta", True), score("tb", False, "  wrong price  ")], TRACES, {}
    )
    first, second = records(result)
    assert first == {
        "case_id": "a",
        "label": "pass",
        "critique": "",
        "labelled_at": "2026-11-12T10:00:00Z",
        "question": "question a",
        "answer": "answer a",
    }
    assert second["case_id"] == "b" and second["label"] == "fail"
    assert second["critique"] == "wrong price"
    assert second["question"] == "question b" and second["answer"] == "answer b"


def test_the_latest_score_per_trace_wins_whatever_the_order():
    scores = [score("ta", False, "late", 10), score("ta", True, "", 1)]
    (rec,) = records(labels_from_scores(REPORT, scores, TRACES, {}))
    assert rec["label"] == "fail" and rec["critique"] == "late"
    (rec,) = records(labels_from_scores(REPORT, scores[::-1], TRACES, {}))
    assert rec["label"] == "fail" and rec["critique"] == "late"


def test_a_pass_comment_is_kept_as_the_critique():
    (rec,) = records(labels_from_scores(REPORT, [score("ta", True, "nice")], TRACES, {}))
    assert rec["critique"] == "nice"


def test_scores_on_traces_outside_the_run_are_counted_and_skipped():
    result = labels_from_scores(
        REPORT,
        [score("ta", True), score("foreign", False, "x"), score("foreign", True)],
        TRACES,
        {},
    )
    assert result.outside_run == 2
    assert [r["case_id"] for r in records(result)] == ["a"]


def test_a_trace_of_a_case_missing_from_the_report_is_outside_the_run():
    result = labels_from_scores(REPORT, [score("tz", True)], {"zzz": "tz"}, {})
    assert result.outside_run == 1 and result.lines == []


def test_a_fail_without_a_comment_is_not_written_but_listed():
    result = labels_from_scores(
        REPORT, [score("ta", False), score("tb", False, "   "), score("tc", True)], TRACES, {}
    )
    assert result.fail_without_critique == ["a", "b"]
    assert [r["case_id"] for r in records(result)] == ["c"]


def current(case_id, label, critique):
    return {case_id: Label(case_id, label, critique, "t", "q", "a")}


def test_a_label_equal_in_label_and_critique_is_unchanged():
    result = labels_from_scores(
        REPORT, [score("tb", False, "wrong")], TRACES, current("b", "fail", "wrong")
    )
    assert result.lines == [] and result.unchanged == 1


@pytest.mark.parametrize(
    "existing", [current("b", "pass", ""), current("b", "fail", "other reason")]
)
def test_a_different_label_or_critique_is_appended(existing):
    result = labels_from_scores(REPORT, [score("tb", False, "wrong")], TRACES, existing)
    assert len(result.lines) == 1 and result.unchanged == 0


def test_a_viewer_label_is_overridden_by_a_different_import():
    viewer = current("a", "pass", "")
    result = labels_from_scores(REPORT, [score("ta", False, "bad")], TRACES, viewer)
    assert records(result)[0]["label"] == "fail"


def test_lines_follow_report_order_and_parse_as_a_labels_file():
    scores = [score("tc", True), score("ta", False, "x"), score("tb", True)]
    result = labels_from_scores(REPORT, scores, TRACES, {})
    assert [r["case_id"] for r in records(result)] == ["a", "b", "c"]
    parsed = parse_labels("".join(result.lines))
    assert {k: v.label for k, v in parsed.items()} == {"a": "fail", "b": "pass", "c": "pass"}


def test_appending_the_lines_makes_a_second_import_write_nothing():
    scores = [score("ta", False, "x"), score("tb", True)]
    first = labels_from_scores(REPORT, scores, TRACES, {})
    again = labels_from_scores(REPORT, scores, TRACES, parse_labels("".join(first.lines)))
    assert again.lines == [] and again.unchanged == 2
