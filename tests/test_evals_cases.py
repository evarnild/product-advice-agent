import json
from pathlib import Path

import pytest

from advisor.catalogue import CATEGORIES, load_catalogue
from advisor.evals.cases import FEATURES, SCENARIOS, CaseFileError, parse_cases

COMMITTED = Path(__file__).parent.parent / "evals" / "cases.jsonl"
CATALOGUE = load_catalogue()


def line(**fields):
    base = {"id": "c1", "question": "q?"}
    base.update(fields)
    return json.dumps(base)


def load_committed():
    return parse_cases(COMMITTED.read_text(encoding="utf-8"), CATALOGUE)


def test_committed_file_validates_and_has_12_to_20_cases():
    assert 12 <= len(load_committed()) <= 20


def test_committed_file_covers_every_category():
    by_id = {p.id: p for p in CATALOGUE}
    seen = set()
    for c in load_committed():
        seen.update(by_id[i].category for i in c.expect_ids)
        if "category" in c.expect_search:
            seen.add(c.expect_search["category"])
    assert seen == set(CATEGORIES)


def test_committed_file_covers_budget_nothing_matches_stock_offtopic_and_section_7():
    cases = {c.id: c for c in load_committed()}
    assert any("max_price" in c.expect_search for c in cases.values())
    assert not cases["no-laptop-under-200"].expect_ids
    assert any("P-004" in c.expect_ids for c in cases.values())
    assert sum(c.must_decline for c in cases.values()) >= 2
    nc = cases["nc-headphones-under-200"]
    assert nc.question == "I need noise-cancelling headphones under 200 euros"
    assert set(nc.expect_ids) == {"P-005", "P-001"}


def test_blank_lines_are_ignored_and_defaults_apply():
    (case,) = parse_cases("\n" + line() + "\n\n", CATALOGUE)
    assert (case.expect_ids, case.forbid_ids, case.must_decline, case.expect_search) == (
        (),
        (),
        False,
        {},
    )


@pytest.mark.parametrize(
    ("text", "needles"),
    [
        (line(colour="red"), ["case 'c1'", "'colour'"]),
        (line(expect_ids=["P-099"]), ["case 'c1'", "'expect_ids'", "P-099"]),
        (line(forbid_ids=["P-098"]), ["case 'c1'", "'forbid_ids'", "P-098"]),
        (line(must_decline=True, expect_ids=["P-001"]), ["case 'c1'", "'expect_ids'"]),
        (line(expect_search={"colour": "red"}), ["case 'c1'", "'expect_search'", "colour"]),
        (line() + "\n" + line(), ["line 2", "case 'c1'", "'id'", "duplicate"]),
        (line() + "\n{not json", ["line 2", "not valid JSON"]),
        (line(question=""), ["case 'c1'", "'question'"]),
        (line(expect_search={"max_price": "cheap"}), ["'expect_search'", "max_price"]),
        (line(expect_search={"category": "toaster"}), ["case 'c1'", "'expect_search'", "category"]),
        (
            line(expect_search={"in_stock_only": "yes"}),
            ["case 'c1'", "'expect_search'", "in_stock"],
        ),
        (
            line(expect_search={"keywords_any": []}),
            ["case 'c1'", "'expect_search'", "keywords_any"],
        ),
        (line(must_decline="yes"), ["case 'c1'", "'must_decline'"]),
        ("", ["no cases"]),
    ],
)
def test_bad_files_name_the_case_and_field(text, needles):
    with pytest.raises(CaseFileError) as e:
        parse_cases(text, CATALOGUE)
    for needle in needles:
        assert needle in str(e.value)


# --- §9 B1: dimensions ---------------------------------------------------

GOOD_DIMS = {"feature": "laptop", "scenario": "exact-match", "persona": "a student"}


def test_a_case_without_dimensions_has_none():
    (case,) = parse_cases(line(), CATALOGUE)
    assert case.dimensions is None


def test_valid_dimensions_are_kept():
    (case,) = parse_cases(line(dimensions=GOOD_DIMS), CATALOGUE)
    assert case.dimensions == GOOD_DIMS


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_each_scenario_is_accepted(scenario):
    dims = {**GOOD_DIMS, "scenario": scenario}
    (case,) = parse_cases(line(dimensions=dims), CATALOGUE)
    assert case.dimensions["scenario"] == scenario


def test_scenarios_are_the_seven_of_the_spec():
    assert set(SCENARIOS) == {
        "exact-match",
        "several-matches",
        "no-match",
        "budget-too-low",
        "out-of-stock",
        "off-topic",
        "spelling-differs",
    }


@pytest.mark.parametrize("feature", [*CATEGORIES, "off-topic"])
def test_each_category_and_off_topic_is_a_feature(feature):
    dims = {**GOOD_DIMS, "feature": feature}
    (case,) = parse_cases(line(dimensions=dims), CATALOGUE)
    assert case.dimensions["feature"] == feature
    assert set(FEATURES) == {*CATEGORIES, "off-topic"}


@pytest.mark.parametrize("missing", ["feature", "scenario", "persona"])
def test_each_missing_key_is_an_error(missing):
    dims = {k: v for k, v in GOOD_DIMS.items() if k != missing}
    with pytest.raises(CaseFileError) as e:
        parse_cases(line(dimensions=dims), CATALOGUE)
    assert "line 1, case 'c1': field 'dimensions'" in str(e.value)
    assert missing in str(e.value)


@pytest.mark.parametrize(
    "dims",
    [
        {**GOOD_DIMS, "colour": "red"},
        {**GOOD_DIMS, "feature": "toaster"},
        {**GOOD_DIMS, "scenario": "weird"},
        {**GOOD_DIMS, "persona": ""},
        {**GOOD_DIMS, "persona": "  "},
        {**GOOD_DIMS, "persona": 3},
        "laptop",
        [],
    ],
)
def test_bad_dimensions_name_line_case_and_field(dims):
    with pytest.raises(CaseFileError) as e:
        parse_cases(line(dimensions=dims), CATALOGUE)
    assert "line 1, case 'c1': field 'dimensions'" in str(e.value)


def test_committed_cases_are_consistent_with_the_catalogue():
    from advisor.evals.cases import catalogue_problems

    problems = catalogue_problems(load_committed(), CATALOGUE)
    assert problems == [], "\n".join(problems)
