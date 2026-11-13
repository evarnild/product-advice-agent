import json
from datetime import UTC, datetime, timedelta, timezone

import pytest

from advisor.evals.labels import LabelFileError, check_label, label_line, parse_labels

T = datetime(2026, 11, 11, 9, 30, 5, tzinfo=UTC)


def line(case_id="a", label="pass", critique="", at=T, question="q?", answer="an answer"):
    return label_line(case_id, label, critique, at, question, answer)


def test_a_line_has_every_field_and_is_one_json_line():
    text = line("c1", "fail", "  wrong price  ", question="Q é", answer="A")
    assert text.endswith("\n") and text.count("\n") == 1
    assert json.loads(text) == {
        "case_id": "c1",
        "label": "fail",
        "critique": "wrong price",
        "labelled_at": "2026-11-11T09:30:05Z",
        "question": "Q é",
        "answer": "A",
    }
    assert "é" in text  # not escaped


def test_the_timestamp_is_utc():
    local = datetime(2026, 11, 11, 11, 30, 5, tzinfo=timezone(timedelta(hours=2)))
    assert json.loads(line(at=local))["labelled_at"] == "2026-11-11T09:30:05Z"


def test_last_line_per_case_wins():
    text = (
        line("a", "pass")
        + line("b", "pass")
        + line("a", "fail", "bad")
        + line("b", "pass", "fine")
        + line("a", "pass", "after all")
    )
    current = parse_labels(text)
    assert set(current) == {"a", "b"}
    assert (current["a"].label, current["a"].critique) == ("pass", "after all")
    assert current["b"].critique == "fine"


def test_an_earlier_line_does_not_beat_a_later_one_in_either_direction():
    assert parse_labels(line("a", "fail", "x") + line("a", "pass"))["a"].label == "pass"
    assert parse_labels(line("a", "pass") + line("a", "fail", "x"))["a"].label == "fail"


def test_blank_lines_and_empty_text():
    assert parse_labels("") == {}
    assert parse_labels("\n" + line("a") + "\n\n").keys() == {"a"}


@pytest.mark.parametrize(
    ("text", "needle"),
    [
        ("{not json", "line 2: not valid JSON"),
        ("[]", "expected a JSON object"),
        (json.dumps({"case_id": "a"}), "field 'label'"),
        (
            json.dumps(
                {
                    "case_id": "a",
                    "label": "maybe",
                    "critique": "",
                    "labelled_at": "t",
                    "question": "q",
                    "answer": "a",
                }
            ),
            "must be one of pass, fail",
        ),
    ],
)
def test_bad_label_files_name_the_line(text, needle):
    with pytest.raises(LabelFileError) as e:
        parse_labels(line("ok") + text)
    assert needle in str(e.value)
    assert "line 2" in str(e.value)


def test_a_fail_needs_a_critique_and_a_pass_does_not():
    assert check_label("pass", "") is None
    assert check_label("fail", "") == "a fail needs a critique"
    assert check_label("fail", "   ") == "a fail needs a critique"
    assert check_label("fail", "bad") is None
    assert check_label("maybe", "x") is not None
    with pytest.raises(ValueError, match="needs a critique"):
        line("a", "fail", "")
