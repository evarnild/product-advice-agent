"""§14: the seeded catalogue generator (B1, B3-B8) and the committed file (B2, B3)."""

import hashlib
import json
from collections import Counter

import pytest

from advisor.catalogue import CATEGORIES, DEFAULT_CATALOGUE_PATH, load_catalogue
from advisor.catalogue_build import (
    NEW_BRANDS,
    SEED,
    TARGET_COUNTS,
    build_products,
    main,
)

HAND_WRITTEN = 32
COMMITTED = json.loads(DEFAULT_CATALOGUE_PATH.read_text(encoding="utf-8"))
FIRST_32 = COMMITTED[:HAND_WRITTEN]
BUILT = build_products(FIRST_32, SEED)
NEW = BUILT[HAND_WRITTEN:]
# §14 spec B5 and B4, written out here so a change to the module's tables cannot
# change what the test expects.
BANDS = {
    "headphones": (19, 449),
    "laptop": (249, 2999),
    "monitor": (89, 1499),
    "phone": (99, 1799),
    "smartwatch": (29, 799),
    "tablet": (99, 1499),
    "camera": (149, 2999),
    "speaker": (19, 699),
}
KEYS = {
    "headphones": ["type", "noise_cancelling", "battery"],
    "laptop": ["cpu", "ram", "storage", "screen"],
    "monitor": ["size", "resolution", "refresh"],
    "phone": ["screen", "storage", "camera"],
    "smartwatch": ["screen", "battery", "gps"],
    "tablet": ["screen", "storage", "stylus"],
    "camera": ["sensor", "video", "waterproof"],
    "speaker": ["type", "battery", "waterproof"],
}
# sha256 of the 32 hand-written products as they are on main (sorted keys).
FIRST_32_SHA256 = "7b19c2785849fb227c1a9647c442ed2260ca275e0a5e4a83c46c1178f89f21f4"
OLD_BRANDS = {"Auralis", "Kestrel", "Sonavo", "Norvik", "Pelagic", "Tolvane", "Lumino", "Zephra"}


def test_same_seed_twice_is_equal():
    assert build_products(FIRST_32, SEED) == build_products(FIRST_32, SEED)


def test_other_seed_differs():
    assert build_products(FIRST_32, SEED + 1) != BUILT


def test_the_32_hand_written_products_are_main_content():
    """Independent of the committed file's own first 32: a hand edit shows here."""
    blob = json.dumps(COMMITTED[:HAND_WRITTEN], sort_keys=True, ensure_ascii=False)
    assert hashlib.sha256(blob.encode()).hexdigest() == FIRST_32_SHA256


def test_first_32_come_back_unchanged_and_first():
    assert BUILT[:HAND_WRITTEN] == FIRST_32
    assert build_products(FIRST_32, SEED)[0]["id"] == "P-001"


def test_input_is_not_mutated():
    before = json.dumps(FIRST_32)
    build_products(FIRST_32, SEED)
    assert json.dumps(FIRST_32) == before


def test_500_products_with_contiguous_ids():
    assert [p["id"] for p in BUILT] == [f"P-{n:03d}" for n in range(1, 501)]


def test_counts_per_category():
    counts = Counter(p["category"] for p in BUILT)
    assert dict(counts) == TARGET_COUNTS
    assert {c: counts[c] for c in ("laptop", "phone", "headphones", "monitor")} == dict.fromkeys(
        ("laptop", "phone", "headphones", "monitor"), 63
    )
    assert {c: counts[c] for c in ("tablet", "smartwatch", "camera", "speaker")} == dict.fromkeys(
        ("tablet", "smartwatch", "camera", "speaker"), 62
    )


def test_generated_products_load_through_the_real_loader(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps(BUILT), encoding="utf-8")
    assert len(load_catalogue(path)) == 500


@pytest.mark.parametrize("category", CATEGORIES)
def test_spec_keys_are_fixed_per_category(category):
    products = [p for p in NEW if p["category"] == category]
    assert products
    for p in products:
        assert list(p["specs"]) == KEYS[category], p["id"]
        assert all(isinstance(v, str) and v for v in p["specs"].values())


@pytest.mark.parametrize("category", CATEGORIES)
def test_prices_are_whole_end_in_9_inside_the_band_and_spread(category):
    lo, hi = BANDS[category]
    prices = [p["price_eur"] for p in NEW if p["category"] == category]
    for price in prices:
        assert price == int(price) and int(price) % 10 == 9
        assert lo <= price <= hi
    third = (hi - lo) / 3
    assert any(x < lo + third for x in prices)
    assert any(lo + third <= x < lo + 2 * third for x in prices)
    assert any(x >= lo + 2 * third for x in prices)


def test_out_of_stock_share_and_minimum_per_category():
    share = sum(not p["in_stock"] for p in NEW) / len(NEW)
    assert 0.12 <= share <= 0.18
    for c in CATEGORIES:
        assert sum(not p["in_stock"] for p in NEW if p["category"] == c) >= 5


def test_twelve_brands_and_four_per_category():
    assert len(NEW_BRANDS) == 4
    assert not set(NEW_BRANDS) & OLD_BRANDS
    assert {p["brand"] for p in BUILT} == OLD_BRANDS | set(NEW_BRANDS)
    for c in CATEGORIES:
        assert len({p["brand"] for p in NEW if p["category"] == c}) >= 4


def test_names_are_unique_and_start_with_the_brand():
    names = [p["name"] for p in BUILT]
    assert len(set(names)) == len(names)
    for p in NEW:
        assert p["name"].startswith(p["brand"] + " ")
        assert len(p["name"].split()) >= 3


def test_every_field_is_present_in_order():
    for p in NEW:
        assert list(p) == [
            "id", "name", "brand", "category", "price_eur", "in_stock", "specs", "description",
        ]  # fmt: skip


def _has(p, phrase):
    return phrase in p["description"].lower()


PRINTED = {
    "headphones": ("type", "battery"),
    "laptop": ("cpu", "ram", "storage", "screen"),
    "monitor": ("size", "resolution", "refresh"),
    "phone": ("screen", "storage", "camera"),
    "smartwatch": ("screen", "battery"),
    "tablet": ("screen", "storage"),
    "camera": ("sensor", "video"),
    "speaker": ("type",),
}


def _every_printed_value_is_in_the_description(p):
    d = p["description"].lower()
    for key in PRINTED[p["category"]]:
        value = (
            p["specs"][key].lower().replace(" in", " inch")
            if key in ("screen", "size") and p["specs"][key].endswith(" in")
            else p["specs"][key].lower()
        )
        assert value in d, (p["id"], key, value, d)
    if p["category"] == "speaker" and p["specs"]["battery"] != "mains":
        assert p["specs"]["battery"].lower() in d, p["id"]


def test_descriptions_name_the_category_and_the_features():
    for p in NEW:
        s, d = p["specs"], p["description"].lower()
        assert p["category"] in d, p["id"]
        assert d.endswith(".") and ". " not in d
        if p["category"] == "headphones":
            assert _has(p, "active noise cancelling") == (s["noise_cancelling"] == "active")
            assert "noise" not in d or s["noise_cancelling"] == "active"
        if p["category"] == "smartwatch":
            assert _has(p, "built-in gps") == (s["gps"] == "yes")
            assert ("gps" in d) == (s["gps"] == "yes")
        if p["category"] == "tablet":
            assert _has(p, "stylus support") == (s["stylus"] == "yes")
        if p["category"] in ("camera", "speaker"):
            assert _has(p, "waterproof") == (s["waterproof"] == "yes")
        if p["category"] == "laptop":
            assert s["ram"].lower() in d and s["storage"].lower() in d
            assert s["screen"].replace(" in", " inch") in d
        if p["category"] == "monitor":
            assert s["size"].replace(" in", " inch") in d and s["refresh"].lower() in d
            assert s["resolution"].lower() in d
        if p["category"] == "phone":
            assert s["storage"].lower() in d and s["camera"].lower() in d
        if p["category"] == "speaker":
            assert s["type"] in d
        _every_printed_value_is_in_the_description(p)


def test_committed_file_is_the_rebuild_of_its_first_32():
    """B2/AC2: a hand edit or a nondeterministic generator shows here."""
    assert COMMITTED == build_products(COMMITTED[:HAND_WRITTEN], SEED)
    assert len(COMMITTED) == 500


def _tmp_copy(tmp_path):
    path = tmp_path / "catalogue.json"
    path.write_text(json.dumps(COMMITTED, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def test_check_is_0_on_an_unedited_copy_and_1_after_an_edit(tmp_path, capsys):
    path = _tmp_copy(tmp_path)
    assert main(["--check"], path=path) == 0
    edited = json.loads(path.read_text(encoding="utf-8"))
    edited[40]["price_eur"] += 10
    path.write_text(json.dumps(edited), encoding="utf-8")
    assert main(["--check"], path=path) == 1
    assert "differs" in capsys.readouterr().out


def test_check_writes_nothing(tmp_path):
    path = _tmp_copy(tmp_path)
    path.write_text(json.dumps(COMMITTED[:HAND_WRITTEN]), encoding="utf-8")
    before = path.read_bytes()
    assert main(["--check"], path=path) == 1
    assert path.read_bytes() == before


def test_rewrite_writes_exactly_the_indented_utf8_json_of_the_build(tmp_path):
    path = tmp_path / "catalogue.json"
    path.write_text(json.dumps(FIRST_32), encoding="utf-8")
    assert main([], path=path) == 0
    expected = json.dumps(build_products(FIRST_32, SEED), indent=2, ensure_ascii=False)
    assert path.read_bytes() == expected.encode("utf-8")


# A band edge no price reaches (the lowest camera is 199, its band starts at 149)
# cannot be seen from the data one price at a time, so the spend per category is
# pinned too. Changing the generator on purpose means updating these numbers.
NEW_PRICE_TOTALS = {
    "laptop": 92443,
    "phone": 55042,
    "headphones": 13343,
    "monitor": 46751,
    "tablet": 47131,
    "smartwatch": 24391,
    "camera": 94440,
    "speaker": 21151,
}


def test_generated_price_totals_per_category_are_pinned():
    totals = {c: sum(int(p["price_eur"]) for p in NEW if p["category"] == c) for c in CATEGORIES}
    assert totals == NEW_PRICE_TOTALS
