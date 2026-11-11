import pytest

from advisor.catalogue import load_catalogue
from advisor.evals.cases import Case
from advisor.evals.score import cited_ids, price_mentioned, score
from advisor.guardrails import REFUSAL_TEXT

CATALOGUE = load_catalogue()


def verdicts(case, answer, searches=()):
    return {c.name: c.ok for c in score(case, answer, list(searches), CATALOGUE)}


def test_cited_ids_finds_ids_in_context():
    assert cited_ids("Acme (P-001), also P-002, and P-001 again.") == ["P-001", "P-002"]
    assert cited_ids("P-001,") == ["P-001"]


@pytest.mark.parametrize("text", ["P-0011", "XP-001", "P-01", "p-001", "AP-123x"])
def test_cited_ids_ignores_longer_or_malformed_tokens(text):
    assert cited_ids(text) == []


@pytest.mark.parametrize("text", ["costs €189", "189 €", "189.00 euros", "189,00 €", "is 189."])
def test_price_mentioned_accepts_formats(text):
    assert price_mentioned(text, 189.0)


@pytest.mark.parametrize("text", ["1189", "18.9", "190", "189.5", "1,189", "189.005", "none"])
def test_price_mentioned_rejects_other_numbers(text):
    assert not price_mentioned(text, 189.0)


def test_price_with_cents_needs_two_decimals():
    assert price_mentioned("only 19.99 euros", 19.99)
    assert price_mentioned("only 19,99", 19.99)
    assert not price_mentioned("only 19 euros", 19.99)
    assert not price_mentioned("only 19.9", 19.99)


@pytest.mark.parametrize(
    "text",
    [
        "€1,799",
        "1.799 €",
        "1 799 euros",
        "1,799.00",
        "1.799,00",
        "1799",
        "1799.00",
        "1\u00a0799",
        "1\u202f799",
    ],
)
def test_price_over_1000_accepts_thousands_separators(text):
    assert price_mentioned(text, 1799.0)


@pytest.mark.parametrize(
    "text",
    [
        "1,79",
        "11,799",
        "1,7990",
        "1,799.5",
        "799",
        "21 799",
        "1.7990",
        "1,798",
        "1.800",
        "1 899",
        "1-799",
        "1/799",
    ],
)
def test_price_over_1000_rejects_other_numbers(text):
    assert not price_mentioned(text, 1799.0)


def test_price_of_exactly_1000_takes_a_separator():
    assert price_mentioned("1,000", 1000.0)
    assert price_mentioned("1.000,00", 1000.0)


def test_price_with_cents_over_1000_accepts_separator():
    assert price_mentioned("1,234.56", 1234.56)
    assert price_mentioned("1234,56", 1234.56)
    assert not price_mentioned("1,234", 1234.56)


GOOD = "The Auralis Calm 300 (P-001) costs 189 euros."


def test_grounded():
    case = Case("c", "q")
    assert verdicts(case, GOOD)["grounded"]
    assert not verdicts(case, GOOD + " Or P-099 at 10 euros.")["grounded"]


def test_prices():
    case = Case("c", "q")
    assert verdicts(case, GOOD)["prices"]
    assert not verdicts(case, "The Auralis Calm 300 (P-001) costs 188 euros.")["prices"]
    assert not verdicts(case, "The Auralis Calm 300 (P-001) costs 1189 euros.")["prices"]


def test_expected_and_forbidden():
    case = Case("c", "q", expect_ids=("P-001", "P-005"), forbid_ids=("P-003",))
    both = GOOD + " The Kestrel Air Plus (P-005) costs 129 euros."
    assert verdicts(case, both)["expected"]
    assert not verdicts(case, GOOD)["expected"]
    assert verdicts(case, both)["forbidden"]
    assert not verdicts(case, both + " P-003 costs 249 euros.")["forbidden"]


def test_checks_only_apply_when_the_case_asks():
    names = [c.name for c in score(Case("c", "q"), GOOD, [], CATALOGUE)]
    assert names == ["grounded", "prices", "stock"]


def test_declines():
    case = Case("c", "q", must_decline=True)
    assert verdicts(case, "Sorry, I only talk about electronics.")["declines"]
    assert verdicts(case, REFUSAL_TEXT)["declines"]
    assert not verdicts(case, GOOD)["declines"]


def test_stock():
    case = Case("c", "q")
    unflagged = "The Sonavo Quiet Pro (P-004) costs 159 euros."
    assert not verdicts(case, unflagged)["stock"]
    assert verdicts(case, unflagged + " It is OUT OF STOCK.")["stock"]
    assert verdicts(case, GOOD)["stock"]  # P-001 is in stock


def test_search_max_price_category_and_keywords():
    case = Case(
        "c",
        "q",
        expect_search={"category": "headphones", "max_price": 200, "keywords_any": ["noise"]},
    )

    def call(**kw):
        base = {"category": "headphones", "max_price": 180, "keywords": ["noise-cancelling"]}
        return {**base, **kw}

    assert verdicts(case, GOOD, [call()])["search"]
    assert verdicts(case, GOOD, [call(max_price=200)])["search"]
    assert not verdicts(case, GOOD, [call(max_price=250)])["search"]
    assert not verdicts(case, GOOD, [{"category": "headphones", "keywords": ["noise"]}])["search"]
    assert not verdicts(case, GOOD, [call(category="laptop")])["search"]
    assert not verdicts(case, GOOD, [call(keywords=["wireless"])])["search"]
    assert not verdicts(case, GOOD, [])["search"]
    assert verdicts(case, GOOD, [call(max_price=999), call()])["search"]  # any one call


def test_search_keywords_are_normalised_on_both_sides():
    def ok(want, got):
        case = Case("c", "q", expect_search={"keywords_any": want})
        return verdicts(case, GOOD, [{"keywords": got}])["search"]

    assert ok(["noise cancelling"], ["Noise-Cancelling"])  # hyphen and case, call side
    assert ok(["noise-cancelling"], ["noise cancelling"])  # hyphen, case-file side
    assert ok(["noise"], ["NOISE"])
    assert ok(["NOISE"], ["noise"])
    assert not ok(["noise"], ["wireless"])


def test_search_min_price_and_stock_only():
    case = Case("c", "q", expect_search={"min_price": 100, "in_stock_only": True})
    assert verdicts(case, GOOD, [{"min_price": 100, "in_stock_only": True}])["search"]
    assert not verdicts(case, GOOD, [{"min_price": 50, "in_stock_only": True}])["search"]
    assert not verdicts(case, GOOD, [{"min_price": 100}])["search"]
