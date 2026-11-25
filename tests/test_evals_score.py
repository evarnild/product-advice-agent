import inspect
import json
from pathlib import Path

import pytest

from advisor.catalogue import load_catalogue
from advisor.evals import score as score_module
from advisor.evals.cases import Case
from advisor.evals.score import cited_ids, invented_names, price_mentioned, score
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
    assert names == ["grounded", "names", "invented", "prices", "stock"]
    with_search = Case("c", "q", expect_search={"category": "laptop"})
    names = [c.name for c in score(with_search, GOOD, [], CATALOGUE)]
    assert names == ["grounded", "names", "invented", "prices", "stock", "search"]


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
    assert one == ["grounded", "names", "invented", "prices", "stock", "search", "a-match"]
    other = [c.name for c in score(prop_case("cites_only_matches"), GOOD, [], CATALOGUE)]
    assert other == ["grounded", "names", "invented", "prices", "stock", "search", "only-matches"]


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


def test_names_fold_keeps_every_position():
    # The name ends exactly 80 characters after the id; a fold that grew the
    # text by one character (U+0130 lowercases to two) would push it out.
    assert not names_check("\u0130 P-009" + " " * 66 + "Auralis Home 1").ok


def test_names_fold_reads_a_hyphen_as_a_space():
    assert not names_check("auralis-home 1 (P-009)").ok


def test_search_keywords_fold_joined_words():  # §32 T7
    def ok(want, got):
        case = Case("c", "q", expect_search={"keywords_any": want})
        return verdicts(case, GOOD, [{"keywords": got}])["search"]

    assert ok(["heart-rate"], ["heartrate"])
    assert ok(["heartrate"], ["heart rate"])
    assert ok(["heart-rate"], ["optical heartrate sensor"])
    assert not ok(["wireless"], ["noise"])


def test_names_do_not_fold_spaces():  # §32 T11
    assert not names_check("Auralis Home 1 (P-009)").ok
    # Joined, it is not the name "Auralis Home 1" (which `_norm` still keeps apart).
    assert names_check("Auralis Home1 (P-009)").ok


# --- invented: a name the catalogue lacks next to a cited id (§35) ---


def inv(answer):
    return invented_names(answer, {p.id: p for p in CATALOGUE})


def runs(answer):
    return [(i, run) for i, _own, run in inv(answer)]


def invented_check(answer):
    return {c.name: c for c in score(Case("c", "q"), answer, [], CATALOGUE)}["invented"]


def test_invented_the_four_intent_lines_fail():  # T1
    assert inv("1. **Acme Foldable (P-004)** - 399.00") == [
        ("P-004", "Sonavo Quiet Pro", "Acme Foldable")
    ]
    assert runs("2. **TechFold Pro (P-007)** - 429.00") == [("P-007", "TechFold Pro")]
    assert runs("- **Aurelis Home 2 (P-012)** - 299.00") == [("P-012", "Aurelis Home 2")]
    assert runs("- **Aurelis Home 3 (P-013)** - 349.00") == [("P-013", "Aurelis Home 3")]


def test_invented_reasons():  # T2
    got = invented_check("- Acme Foldable (P-004)\n- TechFold Pro (P-007)")
    assert not got.ok
    assert got.reason == (
        "P-004 is the Sonavo Quiet Pro, cited as Acme Foldable; "
        "P-007 is the Norvik Slate 14, cited as TechFold Pro"
    )
    twice = invented_check("Acme Foldable (P-004) and Zorp Max (P-004)")
    assert twice.reason == "P-004 is the Sonavo Quiet Pro, cited as Acme Foldable"


def test_invented_brand_with_new_model_and_other_makers_product_fail():  # T3
    assert runs("Norvik Flex (P-123)") == [("P-123", "Norvik Flex")]
    assert runs("Dell XPS 15 (P-009)") == [("P-009", "Dell XPS 15")]


@pytest.mark.parametrize(
    "answer",
    [
        "Auralis Home 1 (P-032)",
        "Kestrel Calm 46 (P-123)",
        "auralis-home 1 (P-032)",
        "AURALIS HOME 1 (P-032)",
        "Go 13 (P-009)",
        "a Kestrel model (P-123)",
        "P-009 costs 649.",
        "Zephra (P-013)",
    ],
)
def test_invented_passes(answer):  # T4
    assert inv(answer) == []


def test_invented_whole_catalogue_name_is_not_invented():  # T5
    assert inv("Zephra One (P-012)") == []


def test_invented_tail_is_whole_words():  # T6
    assert inv("Slate 14 (P-007)") == []
    assert runs("Pelagic Go (P-009)") == [("P-009", "Pelagic Go")]


def test_invented_misspelling_only_next_to_its_own_id():  # T7
    assert inv("Aurelis Home 1 (P-032)") == []
    assert runs("Aurelis Home 1 (P-012)") == [("P-012", "Aurelis Home 1")]


def test_invented_digits_must_equal():  # T8
    assert runs("Aurelis Home 2 (P-032)") == [("P-032", "Aurelis Home 2")]
    assert inv("Aurelis Home 1 (P-032)") == []


def test_invented_threshold_pinned_both_sides():  # T9
    assert score_module._SIMILARITY == 0.85
    assert inv("Aurelis Hume 1 (P-032)") == []
    assert runs("Aurelis Hum 1 (P-032)") == [("P-032", "Aurelis Hum 1")]


def test_invented_slot_edges():  # T10
    assert inv("I recommend the Kestrel Air Plus (P-005)") == []
    assert runs("I recommend the Acme Foldable (P-004)") == [("P-004", "Acme Foldable")]
    assert inv("The Norvik Fold (P-017)") == []
    assert runs("The Acme Foldable (P-004)") == [("P-004", "Acme Foldable")]
    assert inv("It has GPS. The Auralis Tick S (P-025)") == []
    assert runs("1. Acme Foldable (P-004)") == [("P-004", "Acme Foldable")]
    assert inv("**Price:** (P-004)") == []
    six = runs("Alpha Beta Gamma Delta Epsilon Zeta (P-004)")
    assert six == [("P-004", "Beta Gamma Delta Epsilon Zeta")]


def test_invented_what_is_not_read():  # T11
    assert inv("P-004 - Acme Foldable") == []
    assert inv("| Acme Foldable | P-004 |") == []
    assert inv("Acme Foldable\n(P-004)") == []
    assert inv("Acme Foldable\nP-004") == []
    assert [i for i, _ in runs("Acme Foldable P-007 then P-004")] == ["P-007"]


def test_invented_markdown_and_punctuation():  # T12
    assert inv("[Acme Foldable](P-004)") == []
    assert runs("**Acme Foldable** (P-004)") == [("P-004", "Acme Foldable")]
    assert runs('"Acme Foldable" (P-004)') == [("P-004", "Acme Foldable")]


def test_invented_unknown_id_and_no_id():  # T13
    got = {c.name: c.ok for c in score(Case("c", "q"), "Acme Foldable (P-999)", [], CATALOGUE)}
    assert got["invented"] and not got["grounded"]
    assert invented_check("No ids here, Acme Foldable.").ok


def test_invented_is_independent_of_names():  # T14
    got = {c.name: c.ok for c in score(Case("c", "q"), "Auralis Home 1 (P-009)", [], CATALOGUE)}
    assert not got["names"] and got["invented"]
    both = {
        c.name: c.ok
        for c in score(
            Case("c", "q"), "Acme Foldable (P-004), not the Auralis Home 1", [], CATALOGUE
        )
    }
    assert not both["names"] and not both["invented"]


def test_invented_comes_right_after_names_for_every_case():  # T15
    full = Case(
        "c",
        "q",
        expect_ids=("P-001",),
        must_decline=True,
        expect_properties=("cites_a_match",),
        expect_search={"category": "laptop"},
    )
    got = [c.name for c in score(full, GOOD, [], CATALOGUE)]
    assert got[:3] == ["grounded", "names", "invented"]


def test_invented_ok_reason():  # T16
    got = invented_check(GOOD)
    assert got.ok and got.reason == "no invented product name next to a cited id"


def test_invented_names_is_pure_and_deterministic():  # T17
    assert list(inspect.signature(invented_names).parameters) == ["answer", "by_id"]
    text = "Acme Foldable (P-004)"
    assert inv(text) == inv(text)


def test_invented_literal_pair():  # T20
    assert invented_check("The Auralis Calm 300 (P-001) costs 189 euros.").ok
    assert not invented_check("The Auralis Calm 301 Max (P-001) costs 189 euros.").ok


REPLAY = json.loads(
    (Path(__file__).parent / "fixtures" / "invented_replay.json").read_text("utf-8")
)


def test_invented_replay_flagged_answers():  # T18
    by_id = {p.id: p for p in CATALOGUE}
    known = {p.name.lower().replace("-", " ") for p in CATALOGUE}
    assert len(REPLAY["flagged"]) == 63
    assert sum(len(x["expected"]) for x in REPLAY["flagged"]) == 112
    for x in REPLAY["flagged"]:
        got = [[i, run] for i, _own, run in invented_names(x["answer"], by_id)]
        assert got == x["expected"], (x["report"], x["case"])
        assert all(run.lower().replace("-", " ") not in known for _, run in got)


def test_invented_replay_clean_answers():  # T19
    by_id = {p.id: p for p in CATALOGUE}
    assert len(REPLAY["clean"]) == 50
    for x in REPLAY["clean"]:
        assert invented_names(x["answer"], by_id) == [], (x["report"], x["case"])
