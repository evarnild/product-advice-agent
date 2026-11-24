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
    assert not verdicts(case, GOOD + " Or P-999 at 10 euros.")["grounded"]


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
    assert names == ["grounded", "names", "prices", "stock"]
    with_search = Case("c", "q", expect_search={"category": "laptop"})
    names = [c.name for c in score(with_search, GOOD, [], CATALOGUE)]
    assert names == ["grounded", "names", "prices", "stock", "search"]


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


OOS_NO_PRICE = "The Sonavo Quiet Pro (P-004) is out of stock."


def test_prices_exempts_out_of_stock_cited_id_that_says_so():
    assert verdicts(Case("c", "q"), OOS_NO_PRICE)["prices"]


def test_prices_out_of_stock_without_saying_so_fails_naming_the_id():
    case = Case("c", "q")
    answer = "The Sonavo Quiet Pro (P-004) is great."
    assert not verdicts(case, answer)["prices"]
    reasons = {c.name: c.reason for c in score(case, answer, [], CATALOGUE)}
    assert "P-004" in reasons["prices"]


def test_prices_in_stock_cited_id_still_needs_price_when_out_of_stock_said_elsewhere():
    case = Case("c", "q")
    answer = "The Auralis Calm 300 (P-001) is good. The Sonavo Quiet Pro (P-004) is out of stock."
    assert not verdicts(case, answer)["prices"]
    reasons = {c.name: c.reason for c in score(case, answer, [], CATALOGUE)}
    assert "P-001" in reasons["prices"] and "P-004" not in reasons["prices"]


def test_prices_out_of_stock_exemption_is_case_insensitive():
    assert verdicts(Case("c", "q"), "The Sonavo Quiet Pro (P-004) is Out Of Stock.")["prices"]


@pytest.mark.parametrize(
    "answer",
    [
        "The Sonavo Quiet Pro (P-004) is in stock.",
        "The Sonavo Quiet Pro (P-004) is out of budget.",
        "The Sonavo Quiet Pro (P-004) is out-of-stock.",
    ],
)
def test_near_misses_of_out_of_stock_do_not_count(answer):
    # Only the exact phrase "out of stock" flags stock and exempts the price.
    v = verdicts(Case("c", "q"), answer)
    assert not v["stock"]
    assert not v["prices"]


def test_out_of_stock_phrase_counts_mid_text():
    answer = (
        "The Sonavo Quiet Pro (P-004) is out of stock; the Kestrel Air Plus (P-005) costs 129 €."
    )
    v = verdicts(Case("c", "q"), answer)
    assert v["stock"]
    assert v["prices"]


# --- §15 B3: a-match and only-matches ----------------------------------------

LAPTOPS = {"category": "laptop"}
# P-001 is a headphone in the catalogue (see GOOD); P-008 and P-009 are laptops.


def prop_case(*props, search=LAPTOPS):
    return Case("c", "q", expect_search=search, expect_properties=props)


def checks_by_name(case, answer):
    return {c.name: c for c in score(case, answer, [], CATALOGUE)}


def test_a_match_ok_with_one_fitting_id_among_misfits():
    answer = "The Auralis Calm 300 (P-001) costs 189 euros. P-009 costs 649 euros."
    check = checks_by_name(prop_case("cites_a_match"), answer)["a-match"]
    assert check.ok


def test_a_match_fails_naming_cited_ids_when_none_fits():
    check = checks_by_name(prop_case("cites_a_match"), GOOD)["a-match"]
    assert not check.ok and "P-001" in check.reason


def test_a_match_fails_when_nothing_is_cited():
    check = checks_by_name(prop_case("cites_a_match"), "No idea, sorry.")["a-match"]
    assert not check.ok and "cites no product" in check.reason


def test_only_matches_ok_when_all_cited_fit():
    answer = "P-009 costs 649 euros."
    assert checks_by_name(prop_case("cites_only_matches"), answer)["only-matches"].ok


def test_only_matches_names_exactly_the_misfit():
    answer = "P-009 costs 649 euros, and P-001 costs 189 euros."
    check = checks_by_name(prop_case("cites_only_matches"), answer)["only-matches"]
    assert not check.ok and "P-001" in check.reason and "P-009" not in check.reason


def test_only_matches_ok_when_nothing_is_cited():
    assert checks_by_name(prop_case("cites_only_matches"), "Nothing fits.")["only-matches"].ok


def test_unknown_cited_ids_are_ignored_by_both_property_checks():
    answer = "P-009 costs 649 euros. P-999 is great."
    got = checks_by_name(prop_case("cites_a_match", "cites_only_matches"), answer)
    assert got["a-match"].ok and got["only-matches"].ok
    only_unknown = checks_by_name(prop_case("cites_a_match"), "P-999 is great.")
    assert not only_unknown["a-match"].ok and "P-999" not in only_unknown["a-match"].reason


def test_property_checks_appear_only_with_their_property():
    one = [c.name for c in score(prop_case("cites_a_match"), GOOD, [], CATALOGUE)]
    assert one == ["grounded", "names", "prices", "stock", "search", "a-match"]
    other = [c.name for c in score(prop_case("cites_only_matches"), GOOD, [], CATALOGUE)]
    assert other == ["grounded", "names", "prices", "stock", "search", "only-matches"]


# --- names: a cited id next to another product's name (§25) ---

WRONG = "You could check the product page for the Auralis Home 1 (P-009) for any updates."


def names_check(answer):
    return {c.name: c for c in score(Case("c", "q"), answer, [], CATALOGUE)}["names"]


def test_names_catches_a_real_id_under_another_products_name():
    got = names_check(WRONG)
    assert not got.ok
    assert "P-009" in got.reason
    assert "Pelagic Go 13" in got.reason
    assert "Auralis Home 1" in got.reason
    assert names_check(WRONG).reason == "P-009 is the Pelagic Go 13, cited as Auralis Home 1"


def test_names_passes_the_right_id():
    got = names_check(WRONG.replace("P-009", "P-032"))
    assert got.ok


def test_names_passes_with_no_name_nearby_or_own_name():
    assert names_check("P-009 costs 649 euros.").ok
    assert names_check(GOOD).ok


def test_names_passes_with_own_name_and_another_name_in_the_window():
    assert names_check("Unlike the Auralis Home 1, the Pelagic Go 13 (P-009) is in stock.").ok


def test_names_reads_after_the_id_ignoring_case_and_hyphen():
    assert not names_check("P-009 - auralis home 1").ok
    assert names_check("auralis-home 1 (P-032)").ok


def test_names_window_bounds():
    other = "Auralis Home 1"
    # More than 80 characters before the id: not counted.
    assert names_check(other + " " + "x" * 90 + " P-009").ok
    # Within 80: counted.
    assert not names_check(other + " " + "x" * 40 + " P-009").ok
    # More than 80 after the id: not counted.
    assert names_check("P-009 " + "x" * 90 + " " + other).ok
    # On the previous line: not counted.
    assert names_check(other + "\nP-009 costs 649 euros.").ok
    assert names_check("P-009 costs 649 euros.\n" + other).ok
    # Before an earlier id: not counted for the later id.
    assert names_check("Auralis Home 1 P-032 then P-009 costs 649.").ok


def test_names_longest_name_wins():
    by_name = {p.name: p.id for p in CATALOGUE}
    one, mx = by_name["Zephra One"], by_name["Zephra One Max"]
    assert names_check(f"Zephra One Max ({mx})").ok
    got = names_check(f"Zephra One ({mx})")
    assert not got.ok
    assert "cited as Zephra One" in got.reason
    assert "Zephra One Max" not in got.reason.split("cited as")[1]
    assert names_check(f"Zephra One ({one})").ok
    assert names_check("Pelagic Go 130 (P-032)").ok


def test_names_leaves_unknown_ids_to_grounded_and_reports_once():
    got = verdicts(Case("c", "q"), "Auralis Home 1 (P-999) is nice.")
    assert got["names"] and not got["grounded"]
    twice = names_check(WRONG + " Again the Auralis Home 1 (P-009).")
    assert not twice.ok
    assert twice.reason.count("P-009") == 1


def test_prices_reason_names_the_product():
    answer = "The Auralis Home 1 (P-009) is great."
    got = {c.name: c for c in score(Case("c", "q"), answer, [], CATALOGUE)}
    assert not got["prices"].ok
    assert got["prices"].reason == "price of P-009 (Pelagic Go 13) not stated"


def test_names_next_id_bound():
    # A name after the next id is not in this id's window.
    assert names_check("P-009 costs 649, and P-032 is the Auralis Home 1.").ok


def test_names_needs_a_word_boundary_before_a_name():
    assert names_check("MegaAuralis Home 1 (P-009)").ok
    assert not names_check("Mega Auralis Home 1 (P-009)").ok


def test_names_window_width_is_80_characters():
    other = "Auralis Home 1"
    for gap, counts in ((80 - len(other), True), (81 - len(other), False)):
        before = other + " " * gap  # the name starts 80 or 81 characters before the id
        assert (not names_check(before + "P-009").ok) is counts
        after = " " * gap + other  # the name ends 80 or 81 characters after the id
        assert (not names_check("P-009" + after).ok) is counts


def test_names_joins_several_mismatches_with_semicolons():
    got = names_check("Auralis Home 1 (P-009). Norvik Slate 14 (P-001).")
    assert not got.ok
    assert got.reason == (
        "P-009 is the Pelagic Go 13, cited as Auralis Home 1; "
        "P-001 is the Auralis Calm 300, cited as Norvik Slate 14"
    )


def test_names_a_name_just_before_the_next_id_belongs_to_that_id():
    assert names_check("the first one (P-001), or Norvik Slate 14 (P-007)").ok
    assert names_check("the first one (P-001), or Norvik Slate 14 P-007").ok
    assert not names_check("Auralis Home 1 (P-009)").ok
    # A name after the id that is not right before the next id still counts.
    assert not names_check("P-009 is like the Auralis Home 1, and P-032 is cheap").ok


def test_names_folds_case_without_changing_length():
    got = names_check("\u0130 Auralis Home 1 (P-009)")
    assert not got.ok
    assert got.reason == "P-009 is the Pelagic Go 13, cited as Auralis Home 1"
