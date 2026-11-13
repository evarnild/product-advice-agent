"""The cases-versus-catalogue consistency check (§13 B1-B4), on a tiny catalogue."""

from advisor.catalogue import Product
from advisor.evals.cases import Case, catalogue_problems


def prod(pid, price, category="laptop", in_stock=True, name="Thing", desc="plain"):
    return Product(pid, name, "Brand", category, price, in_stock, {}, desc)


def case(**kw):
    return Case(id="c1", question="q?", **kw)


def test_consistent_case_gives_no_problem():
    cat = [prod("P-001", 100), prod("P-002", 300)]
    c = case(expect_ids=("P-001",), forbid_ids=("P-002",), expect_search={"max_price": 200})
    assert catalogue_problems([c], cat) == []


def test_expected_id_in_another_category_is_a_problem_naming_case_and_id():
    cat = [prod("P-001", 100, category="tablet")]
    c = case(expect_ids=("P-001",), expect_search={"category": "laptop"})
    (p,) = catalogue_problems([c], cat)
    assert "c1" in p and "P-001" in p and "not matched by expect_search" in p


def test_max_price_boundary():
    c = case(expect_ids=("P-001",), expect_search={"max_price": 200})
    assert catalogue_problems([c], [prod("P-001", 200)]) == []
    assert len(catalogue_problems([c], [prod("P-001", 201)])) == 1


def test_min_price_boundary():
    c = case(expect_ids=("P-001",), expect_search={"min_price": 200})
    assert catalogue_problems([c], [prod("P-001", 200)]) == []
    assert len(catalogue_problems([c], [prod("P-001", 199)])) == 1


def test_in_stock_only():
    cat = [prod("P-001", 100, in_stock=False)]
    stocked = case(expect_ids=("P-001",), expect_search={"in_stock_only": True})
    assert len(catalogue_problems([stocked], cat)) == 1
    loose = case(expect_ids=("P-001",), expect_search={"category": "laptop"})
    assert catalogue_problems([loose], cat) == []


def test_keywords_any_matches_any_word_case_and_hyphen_insensitively():
    cat = [prod("P-001", 100, name="Noise Cancelling Buds", desc="Great")]
    c = case(expect_ids=("P-001",), expect_search={"keywords_any": ["zzz", "NOISE-cancelling"]})
    assert catalogue_problems([c], cat) == []
    miss = case(expect_ids=("P-001",), expect_search={"keywords_any": ["zzz"]})
    assert len(catalogue_problems([miss], cat)) == 1


def test_keywords_look_in_brand_and_description():
    cat = [Product("P-001", "X", "Acme", "laptop", 1, True, {}, "Fast OLED screen")]
    c = case(expect_ids=("P-001",), expect_search={"keywords_any": ["oled"]})
    assert catalogue_problems([c], cat) == []
    b = case(expect_ids=("P-001",), expect_search={"keywords_any": ["acme"]})
    assert catalogue_problems([b], cat) == []


def test_rank_ten_of_eleven_is_fine_eleven_of_eleven_is_not():
    cat = [prod(f"P-{n:03d}", n) for n in range(1, 12)]
    ok = case(expect_ids=("P-010",), expect_search={"category": "laptop"})
    assert catalogue_problems([ok], cat) == []
    bad = case(expect_ids=("P-011",), expect_search={"category": "laptop"})
    (p,) = catalogue_problems([bad], cat)
    assert "c1" in p and "P-011" in p and "11 of 11" in p


def test_ties_are_broken_by_id():
    # 10 cheap products plus two at the same price: P-020 sorts before P-021.
    cat = [prod(f"P-{n:03d}", n) for n in range(1, 10)]
    cat += [prod("P-021", 50), prod("P-020", 50)]
    first = case(expect_ids=("P-020",), expect_search={"category": "laptop"})
    assert catalogue_problems([first], cat) == []
    second = case(expect_ids=("P-021",), expect_search={"category": "laptop"})
    assert "11 of 11" in catalogue_problems([second], cat)[0]


def test_forbidden_id_that_matches_is_a_problem():
    cat = [prod("P-001", 100), prod("P-002", 500)]
    c = case(forbid_ids=("P-002",), expect_search={"category": "laptop"})
    (p,) = catalogue_problems([c], cat)
    assert "c1" in p and "P-002" in p and "forbidden but matched" in p
    out = case(forbid_ids=("P-002",), expect_search={"max_price": 200})
    assert catalogue_problems([out], cat) == []


def test_case_without_expect_search_is_not_checked():
    cat = [prod("P-001", 100)]
    c = case(expect_ids=("P-001",), forbid_ids=("P-001",))
    assert catalogue_problems([c], cat) == []
