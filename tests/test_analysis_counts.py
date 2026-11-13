from advisor.evals.counts import agreement, counts_markdown, mode_counts
from advisor.evals.labels import Label
from advisor.evals.taxonomy import Mode, Taxonomy


def case(cid, status, feature=None, scenario="exact-match", persona="p1"):
    c = {"id": cid, "question": "q", "answer": "a", "status": status}
    if feature is not None:
        c["dimensions"] = {"feature": feature, "scenario": scenario, "persona": persona}
    return c


def lab(cid, label):
    return Label(cid, label, "crit" if label == "fail" else "", "t", "q", "a")


# Each agreement cell has its own case; two modes with different counts.
REPORT = {
    "cases": [
        case("pp", "PASS", "laptop"),  # both pass
        case("ff1", "FAIL", "laptop", "no-match"),  # both fail
        case("ff2", "FAIL", "phone", "no-match", "p2"),  # both fail
        case("miss", "PASS", "phone"),  # owner fail, status PASS
        case("strict", "FAIL", "laptop"),  # owner pass, status FAIL
        case("err1", "ERROR", "laptop"),  # ERROR, labelled
        case("err2", "ERROR", "laptop"),  # ERROR, unlabelled
        case("open1", "PASS", "laptop"),  # unlabelled
        case("open2", "FAIL", "phone"),  # unlabelled
        case("nodim", "FAIL"),  # both fail, no dimensions
    ]
}
LABELS = {
    "pp": lab("pp", "pass"),
    "ff1": lab("ff1", "fail"),
    "ff2": lab("ff2", "fail"),
    "miss": lab("miss", "fail"),
    "strict": lab("strict", "pass"),
    "err1": lab("err1", "pass"),
    "nodim": lab("nodim", "fail"),
    "not-in-report": lab("not-in-report", "fail"),
}
TAX = Taxonomy(
    "evals/labels/run.jsonl",
    (Mode("rare", "Rare", "d"), Mode("price", "Price", "d"), Mode("budget", "Budget", "d")),
    {
        "ff1": ("price", "budget"),
        "ff2": ("price",),
        "miss": ("price",),
        "nodim": ("budget",),
        "not-in-report": ("budget",),
    },
)


def test_modes_are_counted_and_sorted_descending():
    # price: ff1, ff2, miss; budget: ff1, nodim (not-in-report is not in the report)
    assert mode_counts(REPORT, LABELS, TAX) == [
        ("price", "Price", 3),
        ("budget", "Budget", 2),
        ("rare", "Rare", 0),
    ]


def test_equal_counts_sort_by_id():
    tax = Taxonomy("l", (Mode("b", "B", "d"), Mode("a", "A", "d")), {"ff1": ("a", "b")})
    assert [r[0] for r in mode_counts(REPORT, LABELS, tax)] == ["a", "b"]


def test_each_agreement_cell_has_its_own_case():
    cells = agreement(REPORT, LABELS)
    assert cells["both_pass"] == ["pp"]
    assert cells["both_fail"] == ["ff1", "ff2", "nodim"]
    assert cells["misses"] == ["miss"]
    assert cells["too_strict"] == ["strict"]


def test_error_and_unlabelled_are_counted_apart():
    cells = agreement(REPORT, LABELS)
    assert cells["error"] == ["err1", "err2"]  # labelled or not
    assert cells["unlabelled"] == ["open1", "open2"]
    total = sum(len(v) for v in cells.values())
    assert total == len(REPORT["cases"])


def test_the_markdown_has_the_mode_table_sorted_with_counts():
    md = counts_markdown(REPORT, LABELS, TAX)
    lines = md.splitlines()
    start = lines.index("| mode | name | failed |")
    assert lines[start + 2 : start + 5] == [
        "| price | Price | 3 |",
        "| budget | Budget | 2 |",
        "| rare | Rare | 0 |",
    ]


def section(md, heading):
    start = md.index("## " + heading) + len(heading) + 3
    end = md.find("## ", start)
    return md[start : end if end != -1 else len(md)]


def test_the_per_dimension_tables_have_a_cell_per_mode_and_value():
    md = counts_markdown(REPORT, LABELS, TAX)
    feature = section(md, "Failure modes by feature")
    # price: ff1 laptop, ff2 phone, miss phone. budget: nodim (none), ff1 laptop.
    assert "| mode | (none) | laptop | phone |" in feature
    assert "| price | 0 | 1 | 2 |" in feature
    assert "| budget | 1 | 1 | 0 |" in feature
    assert "| rare | 0 | 0 | 0 |" in feature
    scenario = section(md, "Failure modes by scenario")
    assert "| mode | (none) | exact-match | no-match |" in scenario
    assert "| price | 0 | 1 | 2 |" in scenario  # miss exact-match; ff1, ff2 no-match
    assert "| budget | 1 | 0 | 1 |" in scenario  # nodim; ff1
    persona = section(md, "Failure modes by persona")
    assert "| mode | (none) | p1 | p2 |" in persona
    assert "| price | 0 | 2 | 1 |" in persona  # ff2 is the only p2
    assert "| budget | 1 | 1 | 0 |" in persona


def test_the_agreement_table_lists_the_disagreement_ids():
    md = counts_markdown(REPORT, LABELS, TAX)
    assert "| both pass | 1 | - |" in md
    assert "| both fail | 3 | - |" in md
    assert "| owner fail, status PASS (a check misses it) | 1 | miss |" in md
    assert "| owner pass, status FAIL (a check is too strict) | 1 | strict |" in md
    assert "| status ERROR (any label) | 2 | - |" in md
    assert "| unlabelled (status not ERROR) | 2 | - |" in md


def test_several_disagreements_are_listed_in_report_order():
    report = {"cases": [case("m2", "PASS", "laptop"), case("m1", "PASS", "laptop")]}
    labels = {"m1": lab("m1", "fail"), "m2": lab("m2", "fail")}
    tax = Taxonomy("l", (Mode("x", "X", "d"),), {"m1": ("x",), "m2": ("x",)})
    assert "| 2 | m2, m1 |" in counts_markdown(report, labels, tax)


def test_it_ends_with_a_newline():
    assert counts_markdown(REPORT, LABELS, TAX).endswith("|\n")
