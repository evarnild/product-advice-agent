import copy
import json

import pytest

from advisor.catalogue import (
    CATEGORIES,
    DEFAULT_CATALOGUE_PATH,
    CatalogueError,
    Product,
    load_catalogue,
    search_products,
)

FIELDS = ["id", "name", "brand", "category", "price_eur", "in_stock", "specs", "description"]


def _product(**over):
    base = {
        "id": "P-001",
        "name": "Acme One",
        "brand": "Acme",
        "category": "laptop",
        "price_eur": 100.0,
        "in_stock": True,
        "specs": {"ram": "8 GB"},
        "description": "A plain thing.",
    }
    base.update(over)
    return base


def _write(tmp_path, products):
    path = tmp_path / "c.json"
    path.write_text(json.dumps(products), encoding="utf-8")
    return path


def _p(pid, price, name="Thing", brand="Acme", category="laptop", in_stock=True, description="d"):
    return Product(pid, name, brand, category, price, in_stock, {}, description)


def test_committed_catalogue_loads():
    products = load_catalogue(DEFAULT_CATALOGUE_PATH)
    assert 25 <= len(products) <= 40
    assert {p.category for p in products} <= set(CATEGORIES)
    assert len({p.id for p in products}) == len(products)


def test_valid_file_loads(tmp_path):
    products = load_catalogue(_write(tmp_path, [_product()]))
    assert products == [
        Product(
            "P-001", "Acme One", "Acme", "laptop", 100.0, True, {"ram": "8 GB"}, "A plain thing."
        )
    ]


@pytest.mark.parametrize("field", FIELDS)
def test_missing_field_names_product_and_field(tmp_path, field):
    bad = _product(id="P-002")
    del bad[field]
    with pytest.raises(CatalogueError) as e:
        load_catalogue(_write(tmp_path, [_product(), bad]))
    msg = str(e.value)
    assert f"'{field}'" in msg
    assert "is missing" in msg
    if field != "id":
        assert "P-002" in msg


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("price_eur", "cheap"),
        ("price_eur", 0),
        ("price_eur", -5),
        ("price_eur", True),
        ("in_stock", "yes"),
        ("specs", ["a"]),
        ("specs", {"a": 1}),
        ("name", 5),
        ("id", "X-1"),
    ],
)
def test_wrong_type_names_product_and_field(tmp_path, field, value):
    with pytest.raises(CatalogueError) as e:
        load_catalogue(_write(tmp_path, [_product(**{field: value})]))
    assert f"'{field}'" in str(e.value)
    if field != "id":
        assert "P-001" in str(e.value)


def test_duplicate_id(tmp_path):
    with pytest.raises(CatalogueError) as e:
        load_catalogue(_write(tmp_path, [_product(), _product(name="Other")]))
    assert "P-001" in str(e.value)
    assert "'id'" in str(e.value)
    assert "duplicate" in str(e.value)


def test_unknown_category(tmp_path):
    with pytest.raises(CatalogueError) as e:
        load_catalogue(_write(tmp_path, [_product(category="toaster")]))
    assert "P-001" in str(e.value)
    assert "'category'" in str(e.value)


def test_not_a_list_bad_json_missing_file_bad_entry(tmp_path):
    with pytest.raises(CatalogueError) as e:
        load_catalogue(_write(tmp_path, {"a": 1}))
    assert "must be a JSON list" in str(e.value)
    p = tmp_path / "bad.json"
    p.write_text("{nope", encoding="utf-8")
    with pytest.raises(CatalogueError):
        load_catalogue(p)
    with pytest.raises(CatalogueError):
        load_catalogue(tmp_path / "absent.json")
    with pytest.raises(CatalogueError) as e:
        load_catalogue(_write(tmp_path, ["x"]))
    assert "entry 0" in str(e.value)


def test_load_does_not_alias_input(tmp_path):
    raw = [_product()]
    snapshot = copy.deepcopy(raw)
    load_catalogue(_write(tmp_path, raw))
    assert raw == snapshot


# P-003 is listed before P-002, they tie on price, and their names sort the other way
# round, forwards and reversed (Gamma Laptop vs Zeta Handset): only the id tie-break orders them.
CAT = [
    _p("P-001", 100, name="Alpha Phone", category="phone"),
    _p("P-003", 50, name="Gamma Laptop", category="laptop", description="Has NOISE cancelling"),
    _p("P-002", 50, name="Zeta Handset", category="phone", in_stock=False),
    _p(
        "P-004",
        200,
        name="Delta",
        brand="Quiet",
        category="laptop",
        description="noise cancelling and light",
    ),
]


def ids(results):
    return [p.id for p in results]


def test_no_filters_sorted_price_then_id():
    assert ids(search_products(CAT)) == ["P-002", "P-003", "P-001", "P-004"]


def test_filters_and_together():
    assert ids(search_products(CAT, category="phone", max_price=60)) == ["P-002"]
    assert ids(search_products(CAT, category="phone", min_price=60)) == ["P-001"]
    assert ids(search_products(CAT, category="laptop", min_price=60, max_price=300)) == ["P-004"]
    assert ids(search_products(CAT, category="phone", in_stock_only=True)) == ["P-001"]


def test_price_bounds_inclusive():
    assert ids(search_products(CAT, min_price=100, max_price=100)) == ["P-001"]


def test_keywords_case_insensitive_all_must_match():
    assert ids(search_products(CAT, keywords=["noise"])) == ["P-003", "P-004"]
    assert ids(search_products(CAT, keywords=["NOISE", "light"])) == ["P-004"]
    assert ids(search_products(CAT, keywords=["quiet", "noise"])) == ["P-004"]
    assert ids(search_products(CAT, keywords=["alpha"])) == ["P-001"]
    assert search_products(CAT, keywords=["noise", "alpha"]) == []


def test_limit_default_and_clamp():
    many = [_p(f"P-{i:03d}", i) for i in range(1, 21)]
    assert len(search_products(many)) == 5
    assert len(search_products(many, limit=3)) == 3
    assert len(search_products(many, limit=0)) == 1
    assert len(search_products(many, limit=-4)) == 1
    assert len(search_products(many, limit=11)) == 10
    assert len(search_products(many, limit=10)) == 10


def test_no_match_is_empty_list():
    assert search_products(CAT, category="monitor") == []
    assert search_products([]) == []


@pytest.mark.parametrize("field", ["name", "brand", "description"])
def test_blank_text_field_is_rejected(tmp_path, field):
    with pytest.raises(CatalogueError) as e:
        load_catalogue(_write(tmp_path, [_product(**{field: "   "})]))
    assert f"'{field}'" in str(e.value)
    assert "P-001" in str(e.value)


# §7: a hyphen counts as a space, in keywords and product text alike.
def test_hyphenated_keyword_matches_spaced_text():
    assert ids(search_products(CAT, keywords=["noise cancelling"])) == ["P-003", "P-004"]
    assert ids(search_products(CAT, keywords=["noise-cancelling"])) == ["P-003", "P-004"]


def test_spaced_keyword_matches_hyphenated_text():
    hyphenated = [_p("P-001", 10, description="compact in-ear buds")]
    assert ids(search_products(hyphenated, keywords=["in ear"])) == ["P-001"]
    assert ids(search_products(hyphenated, keywords=["IN-EAR"])) == ["P-001"]


def test_committed_catalogue_noise_cancelling_headphones_under_200():
    found = search_products(
        load_catalogue(), category="headphones", max_price=200, keywords=["noise-cancelling"]
    )
    assert ids(found) == ["P-005", "P-004", "P-001"]


def test_hyphen_only_keyword_is_ignored():
    assert ids(search_products(CAT, keywords=["-"])) == ids(search_products(CAT))
    assert ids(search_products(CAT, keywords=["--", "noise"])) == ["P-003", "P-004"]
