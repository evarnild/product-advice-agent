import json
from pathlib import Path

import pytest

from advisor.catalogue import CATEGORIES, load_catalogue
from advisor.evals.cases import CaseFileError, parse_cases

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
        ("", ["no cases"]),
    ],
)
def test_bad_files_name_the_case_and_field(text, needles):
    with pytest.raises(CaseFileError) as e:
        parse_cases(text, CATALOGUE)
    for needle in needles:
        assert needle in str(e.value)
