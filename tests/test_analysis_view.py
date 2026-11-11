import json
import re
from datetime import UTC, datetime
from urllib.parse import unquote

import pytest
from starlette.testclient import TestClient

from advisor.evals import view
from advisor.evals.labels import parse_labels
from advisor.evals.report import ReportError
from advisor.evals.view import make_app, serve

NOW = datetime(2026, 11, 11, 9, 30, 5, tzinfo=UTC)

PRODUCTS = [
    {"id": "P-701", "name": "Zephyr Cans", "price_eur": 59.0, "in_stock": True},
    {"id": "P-702", "name": "Boreal Buds", "price_eur": 79.5, "in_stock": False},
]


def case(cid, status, feature, scenario, persona, **extra):
    base = {
        "id": cid,
        "question": f"question of {cid}",
        "status": status,
        "answer": f"answer of {cid}",
        "error": None,
        "searches": [],
        "checks": [],
        "dimensions": {"feature": feature, "scenario": scenario, "persona": persona},
    }
    base.update(extra)
    return base


REPORT = {
    "provider": "ollama",
    "cases": [
        case(
            "a",
            "PASS",
            "headphones",
            "exact-match",
            "a student",
            question="Headphones for <b>a student</b>?",
            answer="Try the Zephyr Cans (P-701).",
            checks=[
                {"name": "grounded", "ok": True, "reason": ""},
                {"name": "price", "ok": False, "reason": "price of P-701 not stated"},
            ],
            turns=[
                {"text": "Let me look. Thinking-text-1", "tools": ["search_products"]},
                {"text": "Final-turn-text", "tools": []},
            ],
            tools=[
                {
                    "name": "search_products",
                    "arguments": {"category": "headphones", "max_price": 90},
                    "results": PRODUCTS,
                    "error": False,
                }
            ],
            guardrails=[
                {"stage": "input", "allowed": True, "reason": "input-reason-x"},
                {"stage": "output", "allowed": True, "reason": "output-reason-y"},
            ],
        ),
        case("b", "FAIL", "laptop", "no-match", "a gift buyer"),
        case("c", "ERROR", "phone", "no-match", "a student", error="boom"),
        case("d", "PASS", "laptop", "exact-match", "a gift buyer"),
    ],
}


@pytest.fixture
def paths(tmp_path):
    report = tmp_path / "run.json"
    report.write_text(json.dumps(REPORT), encoding="utf-8")
    return report, tmp_path / "labels" / "run.jsonl"


def client(paths, now=lambda: NOW):
    report, labels = paths
    return TestClient(make_app(report, labels, now), follow_redirects=False)


def label_lines(paths):
    path = paths[1]
    return (
        [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]
        if path.exists()
        else []
    )


def next_href(html):
    m = re.search(r'<a href="([^"]+)" id="next"', html)
    return unquote(m.group(1)) if m else None


def prev_href(html):
    m = re.search(r'<a href="([^"]+)" id="prev"', html)
    return unquote(m.group(1)) if m else None


# --- B9 -------------------------------------------------------------------


def test_one_conversation_shows_every_part(paths):
    html = client(paths).get("/c/a").text
    # question (escaped) and the three dimensions
    assert "Headphones for &lt;b&gt;a student&lt;/b&gt;?" in html
    assert "<b>a student</b>" not in html
    assert "feature: headphones" in html
    assert "scenario: exact-match" in html
    assert "persona: a student" in html
    # status and each check with its reason
    assert '<span class="ok">PASS</span>' in html
    assert "grounded: ok" in html
    assert "price: FAILED" in html and "price of P-701 not stated" in html
    # each model turn in order, with its tool call, arguments and products
    assert (
        html.index("Thinking-text-1")
        < html.index("search_products")
        < html.index("Final-turn-text")
    )
    assert "Model turn 1" in html and "Model turn 2" in html
    assert '{"category": "headphones", "max_price": 90}' in html
    for fragment in ("P-701", "Zephyr Cans", "59.00", "in stock", "P-702", "Boreal Buds", "79.50"):
        assert fragment in html
    assert "OUT OF STOCK" in html
    # the answer and the guardrail verdicts
    assert "Try the Zephyr Cans (P-701)." in html
    assert "input: allowed (input-reason-x)" in html
    assert "output: allowed (output-reason-y)" in html
    # position and counts
    assert "1 / 4" in html
    assert "labelled 0, pass 0, fail 0" in html
    assert "unlabelled" in html


def test_an_error_case_shows_its_error(paths):
    html = client(paths).get("/c/c").text
    assert "boom" in html
    assert '<span class="bad">ERROR</span>' in html


def test_old_reports_without_turns_still_render(paths):
    html = client(paths).get("/c/b").text
    assert "not recorded in this report" in html
    assert "answer of b" in html


def test_unknown_case_is_404(paths):
    assert client(paths).get("/c/zzz").status_code == 404
    assert client(paths).post("/c/zzz/label", data={"action": "pass"}).status_code == 404


# --- B10, B11 -------------------------------------------------------------


def test_pass_saves_without_a_critique_as_a_full_line(paths):
    c = client(paths)
    r = c.post("/c/a/label", data={"action": "pass"})
    assert r.status_code == 303
    assert r.headers["location"].startswith("/c/a?")
    (line,) = label_lines(paths)
    assert line == {
        "case_id": "a",
        "label": "pass",
        "critique": "",
        "labelled_at": "2026-11-11T09:30:05Z",
        "question": "Headphones for <b>a student</b>?",
        "answer": "Try the Zephyr Cans (P-701).",
    }
    page = c.get(r.headers["location"]).text
    assert "Saved" in page
    assert "labelled 1, pass 1, fail 0" in page


def test_fail_without_a_critique_is_refused_and_writes_nothing(paths):
    c = client(paths)
    for data in (
        {"action": "fail"},
        {"action": "fail", "critique": "   "},
        {"action": "save", "label": "fail", "critique": ""},
    ):
        r = c.post("/c/a/label", data=data)
        assert r.status_code == 422
        assert "A fail needs a critique." in r.text
    assert label_lines(paths) == []
    assert "labelled 0" in c.get("/c/a").text


def test_a_refused_fail_keeps_the_typed_critique_in_the_box(paths):
    r = client(paths).post("/c/a/label", data={"action": "fail", "critique": " "})
    assert r.status_code == 422
    r = client(paths).post("/c/a/label", data={"action": "save", "label": "", "critique": "hmm"})
    assert r.status_code == 422
    assert "Choose pass or fail first." in r.text
    assert ">hmm</textarea>" in r.text


def test_fail_with_a_critique_is_saved(paths):
    c = client(paths)
    r = c.post("/c/b/label", data={"action": "fail", "critique": "wrong price"})
    assert r.status_code == 303
    (line,) = label_lines(paths)
    assert (line["case_id"], line["label"], line["critique"]) == ("b", "fail", "wrong price")
    assert "labelled 1, pass 0, fail 1" in c.get("/c/b").text


def test_enter_saves_the_pending_label_and_moves_to_the_next_conversation(paths):
    c = client(paths)
    r = c.post("/c/a/label", data={"action": "save", "label": "fail", "critique": "bad"})
    assert r.status_code == 303
    assert r.headers["location"].startswith("/c/b?")
    assert label_lines(paths)[0]["label"] == "fail"
    # a pass with an optional critique saves too
    r = c.post("/c/b/label", data={"action": "save", "label": "pass", "critique": "fine"})
    assert r.headers["location"].startswith("/c/c?")
    assert [x["critique"] for x in label_lines(paths)] == ["bad", "fine"]


def test_enter_on_the_last_conversation_stays_on_it(paths):
    r = client(paths).post("/c/d/label", data={"action": "save", "label": "pass"})
    assert r.status_code == 303
    assert r.headers["location"].startswith("/c/d?")


def test_every_change_appends_a_line_and_the_last_one_is_current(paths):
    c = client(paths)
    c.post("/c/a/label", data={"action": "pass"})
    c.post("/c/a/label", data={"action": "fail", "critique": "second thoughts"})
    lines = label_lines(paths)
    assert [x["label"] for x in lines] == ["pass", "fail"]
    page = c.get("/c/a").text
    assert "labelled 1, pass 0, fail 1" in page
    assert ">second thoughts</textarea>" in page
    assert parse_labels(paths[1].read_text(encoding="utf-8"))["a"].label == "fail"


def test_labels_reload_on_start(paths):
    c = client(paths)
    c.post("/c/a/label", data={"action": "fail", "critique": "kept"})
    c.post("/c/b/label", data={"action": "pass"})
    again = client(paths)  # a restart
    page = again.get("/c/a").text
    assert "labelled 2, pass 1, fail 1" in page
    assert ">kept</textarea>" in page
    assert '<span class="label-fail">fail</span>' in page


def test_the_labels_file_is_created_with_its_directory_and_utf8(paths):
    client(paths).post("/c/a/label", data={"action": "fail", "critique": "prix: 5 €"})
    assert "prix: 5 €" in paths[1].read_text(encoding="utf-8")


# --- B12 ------------------------------------------------------------------


def first_of(c, query):
    r = c.get("/?" + query)
    if r.status_code == 200:
        return None
    return re.match(r"/c/([^?]+)", r.headers["location"]).group(1)


def ids_in(c, query):
    """The filtered list in order, found by stepping 'next' from its first conversation."""
    first = first_of(c, query)
    if first is None:
        return []
    path = f"/c/{first}?{query}"
    out = [first]
    while True:
        nxt = next_href(c.get(path).text)
        if nxt is None:
            return out
        out.append(re.match(r"/c/([^?]+)", nxt).group(1))
        path = nxt


@pytest.fixture
def labelled(paths):
    c = client(paths)
    c.post("/c/a/label", data={"action": "pass"})
    c.post("/c/b/label", data={"action": "fail", "critique": "bad"})
    return c


def test_each_dimension_filter_alone(labelled):
    assert ids_in(labelled, "f_feature=laptop") == ["b", "d"]
    assert ids_in(labelled, "f_scenario=no-match") == ["b", "c"]
    assert ids_in(labelled, "f_persona=a+student") == ["a", "c"]


def test_label_and_status_filters_alone(labelled):
    assert ids_in(labelled, "f_label=unlabelled") == ["c", "d"]
    assert ids_in(labelled, "f_label=pass") == ["a"]
    assert ids_in(labelled, "f_label=fail") == ["b"]
    assert ids_in(labelled, "f_status=PASS") == ["a", "d"]
    assert ids_in(labelled, "f_status=FAIL") == ["b"]
    assert ids_in(labelled, "f_status=ERROR") == ["c"]


def test_filters_combine_with_and(labelled):
    assert ids_in(labelled, "f_feature=laptop&f_status=PASS") == ["d"]
    assert ids_in(labelled, "f_feature=laptop&f_scenario=no-match") == ["b"]
    assert ids_in(labelled, "f_scenario=no-match&f_persona=a+student") == ["c"]
    assert ids_in(labelled, "f_feature=laptop&f_label=unlabelled&f_status=PASS") == ["d"]
    assert ids_in(labelled, "f_feature=phone&f_status=PASS") == []


def test_a_filter_with_no_match_says_so(labelled):
    r = labelled.get("/?f_feature=camera")
    assert r.status_code == 200
    assert "No conversation matches" in r.text


def test_next_and_previous_stay_within_the_filter(labelled):
    page = labelled.get("/c/b?f_feature=laptop").text
    assert "1 / 2" in page
    assert prev_href(page) is None
    assert next_href(page).startswith("/c/d?")
    assert "f_feature=laptop" in next_href(page)
    page = labelled.get("/c/d?f_feature=laptop").text
    assert "2 / 2" in page
    assert next_href(page) is None
    assert prev_href(page).startswith("/c/b?")  # skips the unfiltered 'c'


def test_without_a_filter_next_and_previous_walk_every_conversation(labelled):
    assert next_href(labelled.get("/c/b").text).startswith("/c/c?")
    assert prev_href(labelled.get("/c/c").text).startswith("/c/b?")
    assert prev_href(labelled.get("/c/a").text) is None


def test_the_filters_survive_a_save(labelled):
    r = labelled.post(
        "/c/d/label", data={"action": "pass", "f_feature": "laptop", "f_status": "PASS"}
    )
    assert "f_feature=laptop" in r.headers["location"]
    assert "f_status=PASS" in r.headers["location"]
    r = labelled.post("/c/c/label", data={"action": "save", "label": "pass", "f_feature": "phone"})
    assert r.headers["location"].startswith("/c/c?")  # no next inside the filter


def test_enter_moves_to_the_next_inside_the_filter(labelled):
    r = labelled.post(
        "/c/b/label",
        data={"action": "save", "label": "pass", "f_feature": "laptop"},
    )
    assert r.headers["location"].startswith("/c/d?")  # not 'c'


def test_a_conversation_that_leaves_the_filter_after_labelling_still_navigates(labelled):
    page = labelled.get("/c/c?f_label=unlabelled").text
    assert "1 / 2" in page
    labelled.post("/c/c/label", data={"action": "pass"})
    page = labelled.get("/c/c?f_label=unlabelled").text
    assert "not in this filter / 1" in page
    assert next_href(page).startswith("/c/d?")
    assert prev_href(page) is None


# --- hotkeys and wiring ---------------------------------------------------


def test_the_page_carries_the_hotkeys_and_loads_nothing_external(paths):
    html = client(paths).get("/c/a").text
    for key in ("'p'", "'f'", "'j'", "'k'", "'Enter'"):
        assert f"e.key === {key}" in html
    assert 'id="critique"' in html
    assert "http://" not in html and "https://" not in html
    assert "src=" not in html


def test_serve_binds_to_loopback_only(paths, monkeypatch):
    calls = []
    monkeypatch.setattr(view.uvicorn, "run", lambda app, **kw: calls.append(kw))
    app = make_app(*paths)
    serve(app, "127.0.0.1", 5209)
    assert calls[0]["host"] == "127.0.0.1" and calls[0]["port"] == 5209
    for host in ("0.0.0.0", "localhost", ""):
        with pytest.raises(ValueError, match="127.0.0.1"):
            serve(app, host, 5209)
    assert len(calls) == 1


def test_a_bad_report_is_an_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{}", encoding="utf-8")
    with pytest.raises(ReportError):
        make_app(bad, tmp_path / "l.jsonl")
    with pytest.raises(OSError):
        make_app(tmp_path / "missing.json", tmp_path / "l.jsonl")


# --- review round 1: calls under their own turn, BLOCKED, no stray files -----

TWO_TURNS = case(
    "t",
    "FAIL",
    "laptop",
    "exact-match",
    "a student",
    turns=[
        {"text": "TURN-ONE-TEXT", "tools": ["get_product"]},
        {"text": "TURN-TWO-TEXT", "tools": ["search_products"]},
        {"text": "FINAL-TEXT", "tools": []},
    ],
    tools=[
        {"name": "get_product", "arguments": {"id": "P-555"}, "results": [], "error": True},
        {
            "name": "search_products",
            "arguments": {"category": "laptop", "max_price": 700},
            "results": [
                {"id": "P-808", "name": "Pelagic Go", "price_eur": 649.0, "in_stock": True}
            ],
            "error": False,
        },
    ],
    guardrails=[
        {"stage": "input", "allowed": False, "reason": "blocked-because-xyz"},
        {"stage": "output", "allowed": True, "reason": ""},
    ],
)


def two_turn_page(tmp_path):
    report = tmp_path / "t.json"
    report.write_text(json.dumps({"cases": [TWO_TURNS]}), encoding="utf-8")
    return TestClient(make_app(report, tmp_path / "l.jsonl", lambda: NOW)).get("/c/t").text


def test_each_tool_call_renders_under_its_own_turn(tmp_path):
    html = two_turn_page(tmp_path)
    one, two, final = (html.index(x) for x in ("TURN-ONE-TEXT", "TURN-TWO-TEXT", "FINAL-TEXT"))
    assert one < two < final
    unknown = html.index("get_product")
    search = html.index("search_products")
    assert one < unknown < two  # the unknown tool belongs to turn 1
    assert two < search < final  # the search belongs to turn 2
    assert '{"id": "P-555"}' in html and unknown < html.index("P-555") < two
    assert 'max_price": 700' in html and two < html.index('max_price": 700') < final
    assert two < html.index("P-808") < html.index("Pelagic Go") < final
    assert "the tool call was an error" in html


def test_a_blocked_guardrail_shows_as_blocked_with_its_reason(tmp_path):
    html = two_turn_page(tmp_path)
    assert "input: BLOCKED (blocked-because-xyz)" in html
    assert "output: allowed" in html


def test_make_app_writes_no_file_in_the_working_directory(paths, tmp_path, monkeypatch):
    elsewhere = tmp_path / "cwd"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    app = make_app(*paths)
    TestClient(app).get("/c/a")
    assert list(elsewhere.iterdir()) == []
