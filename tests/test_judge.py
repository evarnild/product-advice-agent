"""§16: the pure judge logic (AC1, AC2, AC3, B6, AC5's maths, B9 ids)."""

from fractions import Fraction

import pytest

from advisor.evals import judge
from advisor.evals.judge import (
    Example,
    JudgeError,
    SplitError,
    ValidationRow,
    Verdict,
    agreement,
    build_prompt,
    conversation,
    in_scope,
    parse_split,
    parse_verdict,
    score_id,
    validation_markdown,
)

# --- B1 ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("scenario", "expected"),
    [
        ("no-match", True),
        ("budget-too-low", True),
        ("exact-match", False),
        ("several-matches", False),
        ("out-of-stock", False),
        ("", False),
    ],
)
def test_scope_by_scenario(scenario, expected):
    assert in_scope({"id": "x", "dimensions": {"scenario": scenario}}) is expected


def test_cases_without_dimensions_are_out():
    assert in_scope({"id": "x"}) is False
    assert in_scope({"id": "x", "dimensions": None}) is False
    assert in_scope({"id": "x", "dimensions": {"feature": "phone"}}) is False


# --- B2, B3, B6 ---------------------------------------------------------------

TOOLS = [
    {
        "name": "search_products",
        "arguments": {"category": "phone", "max_price": 100},
        "results": [{"id": "P-1", "name": "Zed One", "price": 249}],
        "error": False,
    },
    {"name": "search_products", "arguments": {"keywords": "tv"}, "results": [], "error": False},
]


def test_conversation_holds_question_calls_rows_and_answer():
    text = conversation("A phone under 100?", TOOLS, "Nothing fits.")
    assert "Customer question: A phone under 100?" in text
    assert '"max_price": 100' in text
    assert '"keywords": "tv"' in text
    assert "returned 1 product(s)" in text
    assert "returned 0 product(s)" in text
    assert "Zed One" in text
    assert "Assistant answer: Nothing fits." in text


def test_conversation_without_a_search_says_so():
    assert "ran no search" in conversation("q", None, "a")
    assert "ran no search" in conversation("q", [], "a")


def test_conversation_marks_a_failed_call():
    text = conversation(
        "q", [{"name": "search_products", "arguments": {}, "results": [], "error": True}], "a"
    )
    assert "the call failed" in text


TEMPLATE = "RULES\n[[examples]]\nJUDGE THIS\n[[conversation]]\nEND"


def example(ref, label, critique, question):
    return Example(ref, label, critique, conversation(question, [], f"answer to {question}"))


def test_prompt_holds_exactly_the_given_examples_with_label_and_critique():
    examples = [
        example("f#a", "fail", "Smartwatches are not headphones.", "QA headphones"),
        example("f#b", "pass", "", "QB laptops"),
    ]
    held_out = "QH held-out question"
    prompt = build_prompt(TEMPLATE, conversation("QNEW", [], "ANEW"), examples)
    assert "QA headphones" in prompt
    assert "QB laptops" in prompt
    assert "Owner's verdict: FAIL" in prompt
    assert "Owner's critique: Smartwatches are not headphones." in prompt
    assert "Owner's verdict: PASS" in prompt
    assert prompt.count("Owner's critique") == 1  # a pass without a critique has no line
    assert "Customer question: QNEW" in prompt
    assert held_out not in prompt
    assert "[[" not in prompt


def test_a_slot_inside_a_conversation_is_not_filled_again():
    text = "what is [[conversation]] and [[examples]]?"
    tricky = conversation(text, [], "a")
    prompt = build_prompt(TEMPLATE, tricky, [])
    assert prompt.count(text) == 1
    assert prompt.count("[[examples]]") == 1
    assert prompt.count("[[conversation]]") == 1


def test_a_slot_inside_an_example_is_not_filled_either():
    ex = Example("f#a", "fail", "", "an example that says [[conversation]] and [[examples]]")
    prompt = build_prompt(TEMPLATE, "THE CONVERSATION", [ex])
    assert prompt.count("THE CONVERSATION") == 1
    assert "an example that says [[conversation]] and [[examples]]" in prompt


def test_the_shipped_template_has_both_slots():
    template = judge.PROMPT_PATH.read_text(encoding="utf-8")
    assert template.count("[[examples]]") == 1
    assert template.count("[[conversation]]") == 1
    assert '"pass"' in template


# Each rule of the amended B3 is one assertion on the committed template (AC9),
# so dropping any single rule fails exactly its own check.
_RULES = {
    "decide the case": "First decide from the search results which case you are in.",
    "case nothing fits": (
        "Nothing fits: no search returned a product that meets the request as asked, "
        "or no search was run."
    ),
    "case something fits": (
        "Something fits: a search returned a product that meets the request as asked."
    ),
    "pass when nothing fits": (
        "If nothing fits, answer PASS when the answer says plainly that nothing in the "
        "shop fits the request as asked, and offers only alternatives that serve the "
        "customer's need, or none."
    ),
    "pass when something fits": (
        "If something fits, answer PASS when the answer offers only such products, "
        "as the search results show them."
    ),
    "in either case fail": "In either case, answer FAIL when the answer does any of the following.",
    "a implies a fit": (
        "- (a) It implies a fit that the search results do not show (it names a product "
        "that no search returned, or one outside the stated budget or requirement, as if "
        "it met the request), or it says nothing fits when a search result does."
    ),
    "b other kind": (
        "- (b) It proposes an alternative of another kind that does not serve the customer's need."
    ),
    "b tablet example": "a tablet for someone who wants a laptop to take notes on passes",
    "b smartwatch example": "smartwatches for someone who asked for headphones fail",
    "c invented details": (
        "- (c) It states product details that the search results do not show "
        "(a feature, a spec, stock or a price) as facts."
    ),
    "d assumed constraint": (
        "- (d) It assumes a constraint that the customer never gave "
        "(a budget, a price range or a requirement) and answers within it."
    ),
    "e hides": "(e) It hides that nothing fits",
}


@pytest.mark.parametrize("phrase", list(_RULES.values()), ids=list(_RULES))
def test_the_shipped_template_states_each_rule_of_b3(phrase):
    template = judge.PROMPT_PATH.read_text(encoding="utf-8")
    assert phrase in template


# --- B4 ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('{"pass": true, "reason": "Says nothing fits."}', Verdict(True, "Says nothing fits.")),
        ('{"pass": false, "reason": "Offers watches."}', Verdict(False, "Offers watches.")),
        ('{"reason": "Offers watches.", "pass": false}', Verdict(False, "Offers watches.")),
        ('  \n{"reason": " ok ", "pass": true}\n', Verdict(True, "ok")),
        ('{"reason": "r", "pass": true, "extra": 1}', Verdict(True, "r")),
    ],
)
def test_valid_verdicts(text, expected):
    assert parse_verdict(text) == expected


_NOT_OBJECT = "the model answer is not a JSON object"
_NO_PASS = "the JSON has no boolean 'pass'"
_NO_REASON = "the JSON has no string 'reason'"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('{"pass": "yes", "reason": "r"}', _NO_PASS),
        ('{"reason": "r", "pass": "yes"}', _NO_PASS),
        ('{"pass": 1, "reason": "r"}', _NO_PASS),
        ('{"reason": "no pass key"}', _NO_PASS),
        ('{"pass": true}', _NO_REASON),  # B4: a verdict has a reason
        ('{"pass": false, "reason": 3}', _NO_REASON),
        ('{"reason": 3, "pass": false}', _NO_REASON),
        ("I think it passes.", _NOT_OBJECT),
        ("", _NOT_OBJECT),
        ("[true]", _NOT_OBJECT),
        ('Here you go: {"pass": true, "reason": "r"}', _NOT_OBJECT),
        ('```json\n{"pass": true, "reason": "r"}\n```', _NOT_OBJECT),
        ('```\n{"reason": "r", "pass": true}\n```', _NOT_OBJECT),
        ('<think>hmm</think>{"pass": false, "reason": "r"}', _NOT_OBJECT),
    ],
)
def test_anything_else_is_a_judge_error(text, expected):
    assert parse_verdict(text) == JudgeError(expected)


def test_verdict_schema_asks_for_a_reason_then_a_boolean_pass():
    schema = judge.VERDICT_SCHEMA
    assert schema["type"] == "object"
    assert list(schema["properties"]) == ["reason", "pass"]
    assert schema["properties"]["reason"] == {"type": "string"}
    assert schema["properties"]["pass"] == {"type": "boolean"}
    assert set(schema["required"]) == {"reason", "pass"}
    assert schema["additionalProperties"] is False


def test_the_shipped_template_ends_with_the_reply_line_reason_first():
    lines = judge.PROMPT_PATH.read_text(encoding="utf-8").splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    assert lines[-2:] == [
        "Reply with one JSON object and nothing else:",
        '{"reason": "<one sentence>", "pass": true or false}',
    ]


# --- B9 ---------------------------------------------------------------------


def test_score_ids_are_deterministic_and_distinct():
    assert score_id("20261113T0725Z", "c1") == score_id("20261113T0725Z", "c1")
    assert score_id("20261113T0725Z", "c1") != score_id("20261113T0725Z", "c2")
    assert score_id("20261113T0725Z", "c1") != score_id("20261113T0800Z", "c1")


# --- B6: the split ----------------------------------------------------------


def refs(prefix, n):
    return [f"f.jsonl#{prefix}{i}" for i in range(n)]


def test_a_valid_split():
    split = parse_split({"few_shot": ["f.jsonl#a", "f.jsonl#b"], "held_out": ["f.jsonl#c"]})
    assert split.few_shot == ("f.jsonl#a", "f.jsonl#b")
    assert split.held_out == ("f.jsonl#c",)


def test_eight_few_shot_is_fine_nine_is_not():
    parse_split({"few_shot": refs("a", 8), "held_out": []})
    with pytest.raises(SplitError, match="at most 8"):
        parse_split({"few_shot": refs("a", 9), "held_out": []})


def test_overlap_is_an_error():
    with pytest.raises(SplitError, match="both"):
        parse_split({"few_shot": ["f#a"], "held_out": ["f#a", "f#b"]})


def test_duplicates_and_bad_refs_are_errors():
    with pytest.raises(SplitError, match="twice"):
        parse_split({"few_shot": ["f#a", "f#a"], "held_out": []})
    with pytest.raises(SplitError, match="labels file"):
        parse_split({"few_shot": ["nohash"], "held_out": []})
    with pytest.raises(SplitError, match="labels file"):
        parse_split({"few_shot": ["#c"], "held_out": []})
    with pytest.raises(SplitError, match="labels file"):
        parse_split({"few_shot": ["f#"], "held_out": []})
    with pytest.raises(SplitError):
        parse_split({"few_shot": [], "held_out": "x"})
    with pytest.raises(SplitError):
        parse_split([])


def test_few_shot_needs_both_labels_when_labels_are_known():
    labels = {"f#a": "pass", "f#b": "pass", "f#c": "fail", "f#d": "pass"}
    parse_split({"few_shot": ["f#a", "f#c"], "held_out": ["f#d"]}, labels)
    with pytest.raises(SplitError, match="pass and one fail"):
        parse_split({"few_shot": ["f#a", "f#b"], "held_out": ["f#c"]}, labels)
    with pytest.raises(SplitError, match="no current owner label"):
        parse_split({"few_shot": ["f#a", "f#c"], "held_out": ["f#zzz"]}, labels)


# --- B7: the agreement maths -------------------------------------------------


def pairs(pp, pf, fp, ff, errors=0):
    return (
        [(True, True)] * pp
        + [(True, False)] * pf
        + [(False, True)] * fp
        + [(False, False)] * ff
        + [(True, None)] * errors
    )


def test_rates_from_a_literal_table():
    a = agreement(pairs(pp=15, pf=5, fp=2, ff=8))
    assert (a.pass_pass, a.pass_fail, a.fail_pass, a.fail_fail) == (15, 5, 2, 8)
    assert a.tpr == Fraction(15, 20)
    assert a.tnr == Fraction(8, 10)
    assert a.trusted is False  # tpr 0.75
    assert any("true-positive" in r for r in a.reasons)


def test_trusted_at_exactly_the_boundaries():
    # 20 owner passes, 10 owner fails: 30 conversations, 10 fails; both rates exactly 0.8.
    a = agreement(pairs(pp=16, pf=4, fp=2, ff=8))
    assert a.tpr == Fraction(4, 5) and a.tnr == Fraction(4, 5)
    assert a.trusted is True
    assert a.reasons == ()


def test_not_trusted_just_below_each_boundary():
    # rate 0.79: 79 of 100 owner passes, plenty of fails
    below_tpr = agreement(pairs(pp=79, pf=21, fp=0, ff=10))
    assert below_tpr.tpr < Fraction(4, 5) and not below_tpr.trusted
    below_tnr = agreement(pairs(pp=20, pf=0, fp=21, ff=79))
    assert below_tnr.tnr < Fraction(4, 5) and not below_tnr.trusted
    # 29 conversations
    assert not agreement(pairs(pp=19, pf=0, fp=0, ff=10)).trusted
    assert any("29" in r for r in agreement(pairs(pp=19, pf=0, fp=0, ff=10)).reasons)
    # 9 fails, 31 conversations
    nine = agreement(pairs(pp=22, pf=0, fp=0, ff=9))
    assert not nine.trusted and any("9 owner fails" in r for r in nine.reasons)
    # and the same table with 30 / 10 is trusted
    assert agreement(pairs(pp=20, pf=0, fp=0, ff=10)).trusted


def test_no_owner_pass_means_undefined_tpr_and_not_trusted():
    a = agreement(pairs(pp=0, pf=0, fp=0, ff=30))
    assert a.tpr is None
    assert a.trusted is False
    assert any("undefined" in r for r in a.reasons)


def test_no_owner_fail_means_undefined_and_not_trusted():
    a = agreement(pairs(pp=40, pf=0, fp=0, ff=0))
    assert a.tnr is None
    assert a.trusted is False
    assert any("undefined" in r for r in a.reasons)


def test_errors_are_counted_and_left_out_of_the_rates():
    with_errors = agreement(pairs(pp=16, pf=4, fp=2, ff=8, errors=3))
    assert with_errors.errors == 3
    assert with_errors.tpr == Fraction(4, 5)
    assert with_errors.judged == 30
    assert with_errors.trusted is True
    # an error does not make a fail: the 3 owner passes do not lower the tpr
    only_errors = agreement(pairs(0, 0, 0, 0, errors=5))
    assert only_errors.tpr is None and only_errors.errors == 5 and not only_errors.trusted


def rows(table):
    return [
        ValidationRow(f"f#c{i}", owner, f"critique {i}" if not owner else "", judge, f"reason {i}")
        for i, (owner, judge) in enumerate(table)
    ]


def test_markdown_has_table_rates_verdict_and_disagreements():
    text = validation_markdown(
        rows(pairs(pp=1, pf=1, fp=1, ff=1, errors=1)),
        model="claude-haiku-5-5",
        prompt_sha256="abc123",
        few_shot=["f#x", "f#y"],
        skipped=["other.jsonl: no report"],
    )
    assert "**Verdict: not trusted.**" in text
    assert "- Model: claude-haiku-5-5" in text
    assert "- Prompt sha256: abc123" in text
    assert "| owner pass | 1 | 1 |" in text
    assert "| owner fail | 1 | 1 |" in text
    assert "0.50 (1/2)" in text
    assert "1 judge errors" in text
    assert "- f#c1: owner pass, judge fail" in text  # pf
    assert "- f#c2: owner fail, judge pass" in text  # fp
    assert "- f#c3" not in text  # ff agrees
    assert "- f#c4: owner pass, judge ERROR" in text
    assert "owner: critique 2" in text
    assert "judge: reason 2" in text
    assert "- other.jsonl: no report" in text


def test_markdown_rates_show_the_table_counts_not_a_reduced_fraction():
    # The live check's table (2026-11-21): 12/22 and 9/12 printed as 6/11 and 3/4.
    text = validation_markdown(
        rows(pairs(pp=12, pf=10, fp=3, ff=9)),
        model="m",
        prompt_sha256="h",
        few_shot=[],
    )
    assert "owner pass): 0.55 (12/22)" in text
    assert "owner fail): 0.75 (9/12)" in text


def test_markdown_rate_is_undefined_with_no_owner_pass():
    text = validation_markdown(
        rows(pairs(pp=0, pf=0, fp=0, ff=3)),
        model="m",
        prompt_sha256="h",
        few_shot=[],
    )
    assert "owner pass): undefined" in text


def test_markdown_says_trusted_without_a_reason():
    text = validation_markdown(
        rows(pairs(pp=16, pf=4, fp=2, ff=8)),
        model="m",
        prompt_sha256="h",
        few_shot=[],
    )
    assert "**Verdict: trusted.**" in text
    assert "## Skipped" not in text


def test_the_committed_split_is_valid_against_the_committed_labels():
    import json
    from pathlib import Path

    from advisor.evals.labels import parse_labels

    root = Path(__file__).resolve().parent.parent
    value = json.loads((root / "evals" / "judge" / "split.json").read_text(encoding="utf-8"))
    by_ref = {}
    for ref in (*value["few_shot"], *value["held_out"]):
        file, case_id = judge.parse_ref(ref)
        labels = parse_labels((root / "evals" / "labels" / file).read_text(encoding="utf-8"))
        by_ref[ref] = labels[case_id].label
        assert case_id.startswith(("gen-no-match-", "gen-budget-too-low-")), ref  # in scope
    split = parse_split(value, by_ref)
    assert 0 < len(split.few_shot) <= 8
