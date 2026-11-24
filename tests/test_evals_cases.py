import json
import re
from collections import Counter
from pathlib import Path

import pytest

from advisor.catalogue import CATEGORIES, load_catalogue
from advisor.evals.cases import FEATURES, SCENARIOS, Case, CaseFileError, parse_cases
from advisor.evals.coverage import PERSONAS, check_coverage, parse_probe

COMMITTED = Path(__file__).parent.parent / "evals" / "cases.jsonl"
CATALOGUE = load_catalogue()


def line(**fields):
    base = {"id": "c1", "question": "q?"}
    base.update(fields)
    return json.dumps(base)


def load_committed():
    return parse_cases(COMMITTED.read_text(encoding="utf-8"), CATALOGUE)


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
    assert not nc.expect_ids
    assert set(nc.expect_properties) == {"cites_a_match", "cites_only_matches"}


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
        (line(expect_ids=["P-999"]), ["case 'c1'", "'expect_ids'", "P-999"]),
        (line(forbid_ids=["P-998"]), ["case 'c1'", "'forbid_ids'", "P-998"]),
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


# --- §15 B1: expect_properties --------------------------------------------

SEARCH = {"category": "laptop"}


def test_valid_properties_parse_to_a_tuple():
    both = ["cites_a_match", "cites_only_matches"]
    (case,) = parse_cases(line(expect_search=SEARCH, expect_properties=both), CATALOGUE)
    assert case.expect_properties == ("cites_a_match", "cites_only_matches")
    (one,) = parse_cases(
        line(expect_search=SEARCH, expect_properties=["cites_only_matches"]), CATALOGUE
    )
    assert one.expect_properties == ("cites_only_matches",)


def test_no_properties_by_default():
    (case,) = parse_cases(line(expect_search=SEARCH), CATALOGUE)
    assert case.expect_properties == ()


@pytest.mark.parametrize(
    ("props", "needle"),
    [
        (["cites_everything"], "unknown property"),
        (["cites_a_match", "cites_a_match"], "twice"),
        ("cites_a_match", "non-empty list"),
        ([], "non-empty list"),
        ([3], "unknown property"),
        (None, "non-empty list"),
    ],
)
def test_bad_properties_name_line_case_and_field(props, needle):
    with pytest.raises(CaseFileError) as e:
        parse_cases(line(expect_search=SEARCH, expect_properties=props), CATALOGUE)
    assert "line 1, case 'c1': field 'expect_properties'" in str(e.value)
    assert needle in str(e.value)


def test_a_property_without_expect_search_is_rejected():
    with pytest.raises(CaseFileError) as e:
        parse_cases(line(expect_properties=["cites_a_match"]), CATALOGUE)
    assert "line 1, case 'c1': field 'expect_properties'" in str(e.value)
    assert "expect_search" in str(e.value)


# --- §15 B5, B7, B8: the 50 and their spread --------------------------------

VARIETIES = ("typo", "multi", "vague", "casual")
MIN_VARIETY = {"typo": 5, "multi": 5, "vague": 1, "casual": 5}  # B8, as amended
SCENARIO_RANGE = (5, 12)
OFF_TOPIC_RANGE = (2, 4)
MIN_PER_FEATURE = 4
NOTE_RE = re.compile(
    r"^(?:source: (?P<source>[^;]+); )?probe: (?P<probe>\{.*?\})(?:; variety: (?P<variety>.*))?$"
)


def dims_case(n, feature, scenario, persona=PERSONAS[0], note=""):
    return Case(
        f"c{n}",
        f"question {n}",
        note=note,
        dimensions={"feature": feature, "scenario": scenario, "persona": persona},
    )


def spread_problems(cases):
    """What is wrong with the spread of `cases`; empty when it meets B5 and B7."""
    problems = []
    if len(cases) != 50:
        problems.append(f"{len(cases)} cases, not 50")
    if any(c.dimensions is None for c in cases):
        return [*problems, "a case has no dimensions"]
    dims = [c.dimensions for c in cases]
    scenarios = Counter(d["scenario"] for d in dims)
    for scenario in SCENARIOS:
        low, high = OFF_TOPIC_RANGE if scenario == "off-topic" else SCENARIO_RANGE
        if not low <= scenarios[scenario] <= high:
            problems.append(f"scenario {scenario}: {scenarios[scenario]}, not {low}-{high}")
    features = Counter(d["feature"] for d in dims)
    for category in CATEGORIES:
        if features[category] < MIN_PER_FEATURE:
            problems.append(f"feature {category}: {features[category]}, fewer than 4")
    if any(d["persona"] not in PERSONAS for d in dims):
        problems.append("a persona is not in PERSONAS")
    if len({c.id for c in cases}) != len(cases):
        problems.append("duplicate ids")
    if len({c.question for c in cases}) != len(cases):
        problems.append("duplicate questions")
    return problems


def variety_counts(cases):
    counts = Counter()
    for c in cases:
        m = NOTE_RE.match(c.note)
        if m and m["variety"]:
            counts.update(v.strip() for v in m["variety"].split(","))
    return counts


def variety_problems(cases):
    """What misses B8's per-variety minimum (`MIN_VARIETY`); empty when it is met."""
    counts = variety_counts(cases)
    problems = [
        f"{v}: {counts[v]}, fewer than {MIN_VARIETY[v]}"
        for v in VARIETIES
        if counts[v] < MIN_VARIETY[v]
    ]
    problems += [f"unknown variety {v}" for v in counts if v not in (*VARIETIES, "none")]
    return problems


BALANCED_SIZES = {
    "exact-match": 10,
    "several-matches": 9,
    "no-match": 8,
    "budget-too-low": 5,
    "out-of-stock": 7,
    "spelling-differs": 7,
    "off-topic": 4,
}


def balanced(**overrides):
    """50 cases that meet the spread; `overrides` changes scenario sizes (keys use _ for -)."""
    sizes = {**BALANCED_SIZES, **{k.replace("_", "-"): v for k, v in overrides.items()}}
    cases = []
    for scenario, size in sizes.items():
        for _ in range(size):
            n = len(cases)
            feature = "off-topic" if scenario == "off-topic" else CATEGORIES[n % 8]
            cases.append(dims_case(n, feature, scenario))
    return cases


def test_the_committed_file_has_exactly_50_cases_that_meet_the_spread():
    cases = load_committed()
    assert len(cases) == 50
    assert spread_problems(cases) == []


def test_new_cases_name_their_source_and_a_probe_that_passes_the_coverage_check():
    cases = load_committed()
    with_source = [c for c in cases if "source:" in c.note]
    assert len(with_source) == 35
    for c in with_source:
        m = NOTE_RE.match(c.note)
        assert m and m["source"] and m["variety"], c.id
        probe = parse_probe(json.loads(m["probe"]))
        assert probe is not None, c.id
        assert probe.to_note() == "probe: " + m["probe"], c.id  # as Probe.to_note writes it
        ok, why = check_coverage(c.dimensions["scenario"], probe, c.question, CATALOGUE)
        assert ok, f"{c.id}: {why}"


def test_the_committed_file_has_the_customer_style_variety():
    assert variety_problems(load_committed()) == []


def test_new_cases_expect_what_their_scenario_says():
    """B6's table, as amended: each scenario's expectations on the 35 new cases."""
    for c in load_committed():
        if "source:" not in c.note:
            continue
        scenario = c.dimensions["scenario"]
        probe = json.loads(NOTE_RE.match(c.note)["probe"])
        props = c.expect_properties
        if scenario == "off-topic":
            assert c.must_decline, c.id
        elif scenario == "out-of-stock":
            assert list(c.expect_ids) == [probe["product_id"]], c.id
            assert not props, c.id
        elif scenario in ("no-match", "budget-too-low"):
            assert c.expect_search and not c.expect_ids, c.id
            assert not props and not c.must_decline, c.id
        elif scenario == "exact-match":
            assert c.expect_search, c.id
            assert c.expect_ids or "cites_a_match" in props, c.id
        elif scenario == "several-matches":
            assert c.expect_search and "cites_a_match" in props, c.id
        else:
            assert scenario == "spelling-differs", c.id
            assert c.expect_search and "keywords_any" in c.expect_search, c.id
            assert "cites_a_match" in props, c.id


def test_the_balanced_list_meets_the_spread():
    assert spread_problems(balanced()) == []


@pytest.mark.parametrize("scenario", [s for s in SCENARIOS if s != "off-topic"])
def test_scenario_bounds_are_exact(scenario):
    # Trade cases with off-topic-free "no-match" (or "exact-match") to stay at 50.
    other = "no-match" if scenario != "no-match" else "exact-match"
    base = BALANCED_SIZES

    def problems(size):
        sizes = {scenario.replace("-", "_"): size}
        sizes[other.replace("-", "_")] = base[other] + base[scenario] - size
        return [p for p in spread_problems(balanced(**sizes)) if f"scenario {scenario}" in p]

    assert problems(5) == [] and problems(12) == []
    assert problems(4) != [] and problems(13) != []


def test_off_topic_bounds_are_two_to_four():
    def problems(size):
        cases = balanced(off_topic=size, no_match=8 + 4 - size)
        return [p for p in spread_problems(cases) if "scenario off-topic" in p]

    assert problems(2) == [] and problems(4) == []
    assert problems(1) != [] and problems(5) != []


def test_each_category_needs_four_features_not_three():
    first = CATEGORIES[0]

    def relabelled(keep):
        out, seen = [], 0
        for c in balanced():
            d = dict(c.dimensions)
            if d["feature"] == first:
                seen += 1
                if seen > keep:
                    d["feature"] = CATEGORIES[1]
            out.append(Case(c.id, c.question, note=c.note, dimensions=d))
        return out

    assert [p for p in spread_problems(relabelled(4)) if first in p] == []
    assert [p for p in spread_problems(relabelled(3)) if first in p] != []


def test_spread_rejects_a_wrong_count_bad_personas_and_duplicates():
    cases = balanced()
    assert spread_problems(cases[:-1])
    assert spread_problems([*cases, dims_case(99, "laptop", "exact-match")])
    bad = [*cases[:-1], dims_case(98, "off-topic", "off-topic", persona="a pirate")]
    assert any("persona" in p for p in spread_problems(bad))
    dup = [*cases[:-1], cases[0]]
    assert any("duplicate ids" in p for p in spread_problems(dup))
    same_question = [*cases[:-1], Case("other", cases[0].question, dimensions=cases[0].dimensions)]
    assert any("duplicate questions" in p for p in spread_problems(same_question))


def test_variety_is_counted_from_the_note_with_a_boundary():
    def cs(n):
        note = "source: gen-x; probe: {}; variety: typo, multi"
        return [dims_case(i, "laptop", "exact-match", note=note) for i in range(n)]

    assert variety_counts(cs(5))["typo"] == 5 and variety_counts(cs(5))["multi"] == 5
    assert variety_counts(cs(4))["typo"] == 4
    assert variety_counts([dims_case(1, "laptop", "exact-match", note="probe: {}")]) == Counter()
    assert (
        variety_counts([dims_case(1, "laptop", "exact-match", note="a typo in prose")]) == Counter()
    )


def test_variety_needs_five_of_each_not_four():
    def cs(n, variety):
        note = f"probe: {{}}; variety: {variety}"
        return [dims_case(i, "laptop", "exact-match", note=note) for i in range(n)]

    def with_n(variety, n):
        return [
            *(c for v in VARIETIES if v != variety for c in cs(MIN_VARIETY[v], v)),
            *cs(n, variety),
        ]

    for variety, low in MIN_VARIETY.items():
        assert [p for p in variety_problems(with_n(variety, low)) if variety in p] == []
        assert [p for p in variety_problems(with_n(variety, low - 1)) if variety in p] != []
    assert MIN_VARIETY == {"typo": 5, "multi": 5, "vague": 1, "casual": 5}
    assert variety_problems(with_n("vague", 0)) == ["vague: 0, fewer than 1"]
    assert variety_problems(with_n("typo", 4)) == ["typo: 4, fewer than 5"]
    assert variety_problems([*with_n("typo", 5), *cs(1, "wild")]) == ["unknown variety wild"]


def test_expect_search_is_the_notes_probe_for_every_new_case():
    checked = 0
    for c in load_committed()[15:]:
        if c.dimensions["scenario"] in ("out-of-stock", "off-topic"):
            continue
        probe = json.loads(NOTE_RE.match(c.note)["probe"])
        want = {("keywords_any" if k == "keywords" else k): v for k, v in probe.items()}
        assert c.expect_search == want, c.id
        checked += 1
    assert checked >= 25
