import pytest

from advisor.catalogue import CATEGORIES, load_catalogue, search_products
from advisor.evals.coverage import (
    PERSONAS,
    Probe,
    cells,
    check_coverage,
    parse_probe,
    sample_cells,
)

CAT = load_catalogue()


def ok(scenario, probe, question="q"):
    return check_coverage(scenario, probe, question, CAT)[0]


def reason(scenario, probe, question="q"):
    return check_coverage(scenario, probe, question, CAT)[1]


def count(**kw):
    return len(search_products(CAT, limit=10, **kw))


def test_fixture_facts():
    # Headphones cost 59, 79, 129, 159, 189, 249 euros.
    assert count(category="headphones", max_price=59) == 1
    assert count(category="headphones", max_price=79) == 2
    assert count(category="headphones", max_price=58) == 0
    assert count(category="laptop") >= 1
    assert count(category="headphones", keywords=["noise cancelling"]) >= 1


# exact-match: 0 vs 1 result
def test_exact_match_threshold():
    assert not ok("exact-match", Probe(category="headphones", max_price=58))
    assert ok("exact-match", Probe(category="headphones", max_price=59))


# several-matches: 1 vs 2 results
def test_several_matches_threshold():
    assert not ok("several-matches", Probe(category="headphones", max_price=59))
    assert ok("several-matches", Probe(category="headphones", max_price=79))


# no-match: 0 vs 1 result
def test_no_match_threshold():
    assert ok("no-match", Probe(category="headphones", max_price=58))
    assert not ok("no-match", Probe(category="headphones", max_price=59))


def test_budget_too_low_needs_zero_within_budget_and_some_without():
    assert ok("budget-too-low", Probe(category="headphones", max_price=58))
    # one product within the budget: dropped
    assert not ok("budget-too-low", Probe(category="headphones", max_price=59))
    # nothing even without the budget: dropped
    assert not ok("budget-too-low", Probe(category="headphones", max_price=58, keywords=("zzzz",)))


def test_budget_too_low_without_a_max_price_is_dropped():
    assert not ok("budget-too-low", Probe(category="headphones"))
    assert not ok("budget-too-low", Probe(category="headphones", keywords=("zzzz",)))


def test_out_of_stock_needs_a_real_out_of_stock_product():
    assert ok("out-of-stock", Probe(product_id="P-004"))
    assert "in stock" in reason("out-of-stock", Probe(product_id="P-001"))
    assert "not in the catalogue" in reason("out-of-stock", Probe(product_id="P-999"))
    assert not ok("out-of-stock", Probe())


def test_spelling_differs_keyword_must_not_appear_verbatim():
    probe = Probe(category="headphones", keywords=("noise cancelling",))
    assert ok("spelling-differs", probe, "I want noise-cancelling headphones")
    assert not ok("spelling-differs", probe, "I want noise cancelling headphones")
    assert not ok("spelling-differs", probe, "I want NOISE CANCELLING headphones")
    assert "verbatim" in reason("spelling-differs", probe, "noise cancelling")


def test_spelling_differs_needs_a_match_and_keywords():
    assert not ok("spelling-differs", Probe(category="laptop", keywords=("zzzz",)), "q")
    assert "no keywords" in reason("spelling-differs", Probe(category="laptop"), "q")


def test_off_topic_needs_no_probe():
    assert ok("off-topic", None)


def test_other_scenarios_need_a_probe():
    assert reason("exact-match", None) == "no probe"


def test_cells_pair_off_topic_only_with_off_topic():
    grid = cells()
    for feature, scenario, persona in grid:
        assert (feature == "off-topic") == (scenario == "off-topic")
        assert persona in PERSONAS
    assert {f for f, _, _ in grid} == {*CATEGORIES, "off-topic"}
    assert len(grid) == len(set(grid)) == 8 * 6 * 4 + 4


def test_personas_are_the_four_of_the_spec():
    assert len(PERSONAS) == 4


def test_sample_cells_are_two_questions_per_cell():
    assert len(sample_cells(60, 9)) == 30
    assert len(sample_cells(7, 9)) == 4
    assert len(sample_cells(1, 9)) == 1
    assert len(set(sample_cells(60, 9))) == 30


def test_sample_cells_are_stable_for_a_seed_and_differ_for_another():
    assert sample_cells(60, 9)[:3] == [
        ("camera", "spelling-differs", "a student on a tight budget"),
        ("phone", "budget-too-low", "an enthusiast who knows the specs"),
        ("phone", "several-matches", "a non-technical buyer"),
    ]
    assert sample_cells(60, 9) != sample_cells(60, 10)


@pytest.mark.parametrize(
    ("raw", "valid"),
    [
        ({"category": "laptop", "max_price": 500, "keywords": ["a"]}, True),
        ({}, True),
        ({"category": "toaster"}, False),
        ({"max_price": "cheap"}, False),
        ({"max_price": True}, False),
        ({"keywords": "a"}, False),
        ({"keywords": [1]}, False),
        ({"product_id": 4}, False),
        ("probe", False),
        (None, False),
    ],
)
def test_parse_probe(raw, valid):
    assert (parse_probe(raw) is not None) is valid


def test_probe_note_is_stable_json():
    p = Probe(category="laptop", max_price=500, keywords=("a",))
    assert p.to_note() == 'probe: {"category": "laptop", "keywords": ["a"], "max_price": 500}'
