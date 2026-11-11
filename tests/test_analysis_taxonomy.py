import json

import pytest

from advisor.evals.labels import Label
from advisor.evals.taxonomy import (
    Mode,
    Taxonomy,
    build_prompt,
    dumps,
    parse_draft,
    parse_taxonomy,
    validate,
)


def lab(cid, label, critique="c", question="q", answer="a"):
    return Label(cid, label, critique, "t", question, answer)


LABELS = {
    "a": lab("a", "fail", "invented a price", "Q-of-a", "A-of-a"),
    "b": lab("b", "fail", "ignored the budget", "Q-of-b", "A-of-b"),
    "c": lab("c", "pass"),
}
MODES = (Mode("price", "Price", "wrong price"), Mode("budget", "Budget", "ignores budget"))


def tax(mapping=None, modes=MODES):
    return Taxonomy(
        "evals/labels/run.jsonl",
        tuple(modes),
        {"a": ("price",), "b": ("budget", "price")} if mapping is None else mapping,
    )


def test_a_valid_taxonomy_has_no_errors():
    assert validate(tax(), LABELS) == []


def test_a_duplicate_mode_id_is_an_error():
    modes = (*MODES, Mode("price", "Again", "dup"))
    (error,) = validate(tax(modes=modes), LABELS)
    assert "'price' is used more than once" in error


@pytest.mark.parametrize("empty", ["", "   "])
def test_an_empty_mode_id_is_an_error(empty):
    errors = validate(tax(modes=(*MODES, Mode(empty, "n", "d"))), LABELS)
    assert errors == ["a mode has an empty id"]


def test_an_unknown_mode_in_the_mapping_is_an_error():
    (error,) = validate(tax({"a": ("price", "ghost"), "b": ("budget",)}), LABELS)
    assert "case 'a'" in error and "unknown mode 'ghost'" in error


def test_a_mapped_case_that_is_a_pass_is_an_error():
    (error,) = validate(tax({"a": ("price",), "b": ("budget",), "c": ("price",)}), LABELS)
    assert "case 'c'" in error and "not a fail" in error and "pass" in error


def test_a_mapped_case_without_a_label_is_an_error():
    (error,) = validate(tax({"a": ("price",), "b": ("budget",), "zz": ("price",)}), LABELS)
    assert "case 'zz'" in error and "no label" in error


def test_a_failed_case_that_is_not_mapped_is_an_error():
    (error,) = validate(tax({"a": ("price",)}), LABELS)
    assert "failed case 'b'" in error


def test_a_failed_case_mapped_to_an_empty_list_is_not_mapped():
    (error,) = validate(tax({"a": ("price",), "b": ()}), LABELS)
    assert "failed case 'b'" in error


def test_a_case_may_have_several_modes_and_a_mode_may_be_unused():
    t = tax({"a": ("price", "budget"), "b": ("budget",)}, modes=(*MODES, Mode("x", "X", "unused")))
    assert validate(t, LABELS) == []


def test_every_rule_is_independent_a_valid_one_passes_where_the_invalid_one_fails():
    assert validate(tax({"a": ("price",), "b": ("budget",)}), LABELS) == []
    assert validate(tax({"a": ("price",), "b": ("ghost",)}), LABELS) != []


def test_the_prompt_lists_only_failed_conversations_with_their_critiques():
    prompt = build_prompt(LABELS)
    assert "case id: a" in prompt and "case id: b" in prompt
    assert "case id: c" not in prompt
    for needle in ("Q-of-a", "A-of-a", "invented a price", "Q-of-b", "ignored the budget"):
        assert needle in prompt
    assert "[[failures]]" not in prompt


def draft(**over):
    value = {
        "modes": [
            {"id": "price", "name": "Price", "description": "d"},
            {"id": "budget", "name": "Budget", "description": "d"},
        ],
        "mapping": {"a": ["price"], "b": ["budget"]},
    }
    value.update(over)
    return value


def test_a_draft_with_prose_and_think_blocks_parses_and_gets_the_labels_reference():
    text = "<think>x</think>Here:\n" + json.dumps(draft()) + "\nDone."
    t, errors = parse_draft(text, LABELS, "evals/labels/run.jsonl")
    assert errors == []
    assert t.labels == "evals/labels/run.jsonl"
    assert t.mapping == {"a": ("price",), "b": ("budget",)}


@pytest.mark.parametrize(
    ("text", "needle"),
    [
        ("no json here", "no JSON object"),
        (json.dumps(draft(mapping={"a": ["price"]})), "failed case 'b'"),
        (json.dumps(draft(mapping={"a": ["price"], "b": ["nope"]})), "unknown mode 'nope'"),
        (json.dumps(draft(modes="x")), "'modes' must be a list"),
        (json.dumps(draft(mapping=[])), "'mapping' must be an object"),
        (json.dumps(draft(modes=[{"id": "a"}])), "mode 1"),
        (json.dumps(draft(mapping={"a": "price", "b": ["budget"]})), "list of mode ids"),
        ("[1, 2]", "must be a JSON object"),
    ],
)
def test_an_invalid_draft_gives_no_taxonomy_and_a_reason(text, needle):
    t, errors = parse_draft(text, LABELS, "ref")
    assert t is None
    assert any(needle in e for e in errors), errors


def test_a_saved_taxonomy_round_trips_through_parse_taxonomy():
    t = tax()
    parsed, errors = parse_taxonomy(json.loads(dumps(t)))
    assert errors == [] and parsed == t
    assert dumps(t).endswith("\n")


def test_a_saved_taxonomy_must_name_its_labels_file():
    value = json.loads(dumps(tax()))
    del value["labels"]
    parsed, errors = parse_taxonomy(value)
    assert parsed is None and "'labels'" in errors[0]
