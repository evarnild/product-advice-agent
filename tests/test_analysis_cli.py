import io
import json
from datetime import UTC, datetime

import pytest
from starlette.testclient import TestClient

from advisor.catalogue import load_catalogue
from advisor.evals.analysis import labels_path_for, main
from advisor.evals.cases import parse_cases
from advisor.evals.coverage import sample_cells
from advisor.evals.labels import label_line
from advisor.models.base import ModelError, ModelTurn, ModelUnreachableError
from advisor.models.fake import ScriptedModelClient

ENV = {"ADVISOR_MODEL_PROVIDER": "ollama", "ADVISOR_MODEL": "test-model"}
NOW = datetime(2026, 11, 11, 9, 30, 5, tzinfo=UTC)


class Factory:
    def __init__(self, script, repeat_last=False):
        self.client = ScriptedModelClient(script, repeat_last=repeat_last)
        self.calls = []

    def __call__(self, provider, model, *, api_key=None, base_url=None):
        self.calls.append((provider, model, api_key, base_url))
        return self.client


def run(argv, script=(), *, env=ENV, repeat_last=False, serve=None):
    out, err = io.StringIO(), io.StringIO()
    factory = Factory(list(script), repeat_last)
    code = main(
        argv, env=env, client_factory=factory, out=out, err=err, now=lambda: NOW, serve=serve
    )
    return code, out.getvalue(), err.getvalue(), factory


def off_topic_reply():
    return ModelTurn(
        text=json.dumps([{"question": "What is the weather?"}, {"question": "Tell me a joke."}])
    )


# --- generate -------------------------------------------------------------


def prompts(factory):
    return [r.messages[0].text for r in factory.client.requests]


def test_generate_asks_for_the_seeded_cells_in_order_and_writes_cases(tmp_path):
    out = tmp_path / "gen.jsonl"
    cells = sample_cells(4, 9)
    script = [ModelTurn(text="not json")] * len(cells)
    code, stdout, _, factory = run(["generate", "--count", "4", "--out", str(out)], script)
    assert code == 1  # none kept: the answers are not JSON
    assert len(prompts(factory)) == 2
    for prompt, (feature, scenario, persona) in zip(prompts(factory), cells, strict=True):
        assert f"Feature: {feature}" in prompt
        assert f"Scenario: {scenario}" in prompt
        assert persona in prompt
    assert factory.calls == [("ollama", "test-model", None, "http://localhost:11434")]
    assert not out.exists()
    assert "asked 2, kept 0, dropped 2 (2 x unparsable model answer)" in stdout


def test_generate_writes_valid_cases_and_prints_the_summary(tmp_path):
    out = tmp_path / "gen.jsonl"
    # the first sampled cell with count 2 is the off-topic-free one; give every call an
    # answer that fits only the off-topic scenario, so only the off-topic cells are kept.
    cells = sample_cells(120, 9)
    off = [c for c in cells if c[1] == "off-topic"]
    assert off, "the seed must sample at least one off-topic cell"
    script = [off_topic_reply() if c[1] == "off-topic" else ModelTurn(text="no") for c in cells]
    code, stdout, _, _ = run(["generate", "--count", "120", "--out", str(out)], script)
    assert code == 0
    cases = parse_cases(out.read_text(encoding="utf-8"), load_catalogue())
    assert len(cases) == 2 * len(off)
    assert {c.dimensions["scenario"] for c in cases} == {"off-topic"}
    assert all(c.must_decline for c in cases)
    assert len({c.id for c in cases}) == len(cases)
    assert "off-topic: asked" in stdout and f"kept {2 * len(off)}" in stdout
    assert f"wrote {2 * len(off)} questions to {out}" in stdout


def test_generate_default_is_sixty_questions_from_thirty_cells(tmp_path):
    code, _, _, factory = run(
        ["generate", "--out", str(tmp_path / "g.jsonl")],
        [ModelTurn(text="no")],
        repeat_last=True,
    )
    assert code == 1
    assert len(factory.client.requests) == 30


def test_generate_count_is_respected(tmp_path):
    _, _, _, factory = run(
        ["generate", "--count", "7", "--out", str(tmp_path / "g.jsonl")],
        [ModelTurn(text="no")],
        repeat_last=True,
    )
    assert len(factory.client.requests) == 4


def test_the_same_seed_asks_for_the_same_cells_and_another_seed_does_not(tmp_path):
    def asked(*extra):
        _, _, _, f = run(
            ["generate", "--count", "10", "--out", str(tmp_path / "g.jsonl"), *extra],
            [ModelTurn(text="no")],
            repeat_last=True,
        )
        return prompts(f)

    assert asked() == asked("--seed", "9")
    assert asked() != asked("--seed", "10")


def test_generate_refuses_to_overwrite_without_force(tmp_path):
    out = tmp_path / "gen.jsonl"
    out.write_text("keep me\n", encoding="utf-8")
    code, _, err, factory = run(["generate", "--out", str(out)], [])
    assert code == 2
    assert "--force" in err
    assert out.read_text(encoding="utf-8") == "keep me\n"
    assert factory.client.requests == []  # refused before any model call


def test_generate_force_overwrites(tmp_path):
    out = tmp_path / "gen.jsonl"
    out.write_text("old\n", encoding="utf-8")
    cells = sample_cells(2, 9)
    script = [off_topic_reply()] * len(cells)
    # one cell: its answer fits only if it is off-topic; make it so with a different seed search
    seed = next(s for s in range(200) if sample_cells(2, s)[0][1] == "off-topic")
    code, _, _, _ = run(
        ["generate", "--count", "2", "--seed", str(seed), "--out", str(out), "--force"], script
    )
    assert code == 0
    assert "old" not in out.read_text(encoding="utf-8")


def test_generate_model_unreachable_exits_1_and_writes_nothing(tmp_path):
    out = tmp_path / "gen.jsonl"
    code, stdout, err, _ = run(
        ["generate", "--out", str(out)], [ModelUnreachableError("server is down")]
    )
    assert code == 1
    assert "server is down" in err
    assert not out.exists()


def test_generate_bad_arguments_and_config_exit_2(tmp_path):
    assert run(["generate", "--count", "0"])[0] == 2
    assert run(["generate", "--count", "x"])[0] == 2
    assert run(["nonsense"])[0] == 2
    assert run([])[0] == 2
    code, _, err, _ = run(
        ["generate", "--out", str(tmp_path / "g.jsonl")], env={"ADVISOR_MODEL_PROVIDER": "nope"}
    )
    assert code == 2 and "Unknown model provider" in err
    code, _, err, _ = run(
        ["generate", "--out", str(tmp_path / "g.jsonl")],
        env={"ADVISOR_MODEL_PROVIDER": "anthropic"},
    )
    assert code == 2 and "Missing ANTHROPIC_API_KEY" in err


# --- view -----------------------------------------------------------------

REPORT = {
    "cases": [
        {"id": "a", "question": "qa", "answer": "aa", "status": "PASS"},
        {"id": "b", "question": "qb", "answer": "ab", "status": "FAIL"},
    ]
}


def write_report(tmp_path, name="run.json"):
    path = tmp_path / name
    path.write_text(json.dumps(REPORT), encoding="utf-8")
    return path


def test_view_serves_on_loopback_and_the_default_port(tmp_path):
    calls = []
    report = write_report(tmp_path)
    code, stdout, _, _ = run(
        ["view", str(report), "--labels", str(tmp_path / "l.jsonl")],
        serve=lambda app, host, port: calls.append((host, port)),
    )
    assert code == 0
    assert calls == [("127.0.0.1", 5209)]
    assert "http://127.0.0.1:5209" in stdout


def test_view_port_option(tmp_path):
    calls = []
    run(
        ["view", str(write_report(tmp_path)), "--port", "6123", "--labels", str(tmp_path / "l")],
        serve=lambda app, host, port: calls.append((host, port)),
    )
    assert calls == [("127.0.0.1", 6123)]


def test_view_labels_default_to_evals_labels_by_report_stem(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    report = write_report(tmp_path, "20261111T093005Z-ollama.json")
    assert labels_path_for(report).as_posix() == "evals/labels/20261111T093005Z-ollama.jsonl"

    def serve(app, host, port):
        TestClient(app).post("/c/a/label", data={"action": "pass"})

    run(["view", str(report)], serve=serve)
    saved = tmp_path / "evals" / "labels" / "20261111T093005Z-ollama.jsonl"
    assert json.loads(saved.read_text(encoding="utf-8"))["case_id"] == "a"


def test_view_missing_or_bad_report_exits_2_with_one_line(tmp_path):
    served = []
    code, _, err, _ = run(["view", str(tmp_path / "none.json")], serve=lambda *a: served.append(a))
    assert code == 2 and len(err.strip().splitlines()) == 1
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    code, _, err, _ = run(["view", str(bad)], serve=lambda *a: served.append(a))
    assert code == 2 and len(err.strip().splitlines()) == 1
    badlabels = tmp_path / "labels.jsonl"
    badlabels.write_text("{oops", encoding="utf-8")
    code, _, err, _ = run(
        ["view", str(write_report(tmp_path)), "--labels", str(badlabels)],
        serve=lambda *a: served.append(a),
    )
    assert code == 2
    assert served == []


# --- taxonomy -------------------------------------------------------------


def write_labels(
    tmp_path,
    rows=(("a", "fail", "invented a price"), ("b", "pass", ""), ("c", "fail", "no budget")),
):
    path = tmp_path / "labels" / "run.jsonl"
    path.parent.mkdir(exist_ok=True)
    path.write_text(
        "".join(label_line(cid, lab, crit, NOW, f"q-{cid}", f"a-{cid}") for cid, lab, crit in rows),
        encoding="utf-8",
    )
    return path


GOOD_DRAFT = {
    "modes": [
        {"id": "price", "name": "Price", "description": "d"},
        {"id": "budget", "name": "Budget", "description": "d"},
    ],
    "mapping": {"a": ["price"], "c": ["budget"]},
}


def test_taxonomy_writes_the_draft_and_sends_the_critiques(tmp_path):
    labels = write_labels(tmp_path)
    out = tmp_path / "draft.json"
    reply = ModelTurn(text="Sure:\n" + json.dumps(GOOD_DRAFT))
    code, stdout, _, factory = run(["taxonomy", str(labels), "--out", str(out)], [reply])
    assert code == 0
    assert len(factory.client.requests) == 1  # one call
    sent = factory.client.requests[0].messages[0].text
    assert "invented a price" in sent and "no budget" in sent and "q-a" in sent and "a-c" in sent
    assert "case id: b" not in sent  # the pass is not sent
    draft = json.loads(out.read_text(encoding="utf-8"))
    assert draft["labels"] == str(labels)
    assert draft["mapping"] == {"a": ["price"], "c": ["budget"]}
    assert [m["id"] for m in draft["modes"]] == ["price", "budget"]
    assert "taxonomy.json" in stdout


def test_taxonomy_default_output_is_the_draft_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    labels = write_labels(tmp_path)
    code, _, _, _ = run(["taxonomy", str(labels)], [ModelTurn(text=json.dumps(GOOD_DRAFT))])
    assert code == 0
    assert (tmp_path / "evals" / "taxonomy.draft.json").exists()


@pytest.mark.parametrize(
    "text",
    [
        "no json",
        json.dumps({**GOOD_DRAFT, "mapping": {"a": ["price"]}}),  # c not mapped
        json.dumps({**GOOD_DRAFT, "mapping": {"a": ["price"], "c": ["ghost"]}}),
        json.dumps({**GOOD_DRAFT, "mapping": {"a": ["price"], "b": ["price"], "c": ["budget"]}}),
    ],
)
def test_an_invalid_draft_writes_nothing_and_exits_1(tmp_path, text):
    out = tmp_path / "draft.json"
    code, _, err, _ = run(
        ["taxonomy", str(write_labels(tmp_path)), "--out", str(out)], [ModelTurn(text=text)]
    )
    assert code == 1
    assert "Draft rejected" in err and "does not validate" in err
    assert not out.exists()


def test_taxonomy_model_unreachable_exits_1(tmp_path):
    out = tmp_path / "draft.json"
    code, _, err, _ = run(
        ["taxonomy", str(write_labels(tmp_path)), "--out", str(out)],
        [ModelUnreachableError("server is down")],
    )
    assert code == 1 and "server is down" in err and not out.exists()
    code, _, err, _ = run(
        ["taxonomy", str(write_labels(tmp_path)), "--out", str(out)], [ModelError("boom")]
    )
    assert code == 1 and not out.exists()


def test_taxonomy_input_errors_exit_2(tmp_path):
    assert run(["taxonomy", str(tmp_path / "none.jsonl")])[0] == 2
    passes = write_labels(tmp_path, rows=(("a", "pass", ""),))
    code, _, err, factory = run(["taxonomy", str(passes)])
    assert code == 2 and "No failed conversation" in err
    assert factory.client.requests == []
    bad = tmp_path / "bad.jsonl"
    bad.write_text("{oops", encoding="utf-8")
    assert run(["taxonomy", str(bad)])[0] == 2


# --- counts ---------------------------------------------------------------

COUNT_REPORT = {
    "cases": [
        {"id": "a", "question": "qa", "answer": "aa", "status": "PASS"},
        {"id": "b", "question": "qb", "answer": "ab", "status": "FAIL"},
        {"id": "c", "question": "qc", "answer": "ac", "status": "FAIL"},
    ]
}


def counts_files(tmp_path, taxonomy=None):
    report = tmp_path / "run.json"
    report.write_text(json.dumps(COUNT_REPORT), encoding="utf-8")
    labels = write_labels(
        tmp_path, rows=(("a", "fail", "x"), ("b", "pass", ""), ("c", "fail", "y"))
    )
    tax_path = tmp_path / "taxonomy.json"
    tax_path.write_text(
        json.dumps(
            taxonomy
            or {
                "labels": str(labels),
                "modes": [
                    {"id": "m1", "name": "One", "description": "d"},
                    {"id": "m2", "name": "Two", "description": "d"},
                ],
                "mapping": {"a": ["m1"], "c": ["m1", "m2"]},
            }
        ),
        encoding="utf-8",
    )
    return report, labels, tax_path


def test_counts_prints_the_tables_and_writes_them_with_out(tmp_path):
    report, labels, tax_path = counts_files(tmp_path)
    out = tmp_path / "counts.md"
    code, stdout, err, _ = run(
        [
            "counts",
            str(report),
            "--labels",
            str(labels),
            "--taxonomy",
            str(tax_path),
            "--out",
            str(out),
        ]
    )
    assert code == 0, err
    assert "| m1 | One | 2 |" in stdout and "| m2 | Two | 1 |" in stdout
    assert "| owner fail, status PASS (a check misses it) | 1 | a |" in stdout
    assert "| owner pass, status FAIL (a check is too strict) | 1 | b |" in stdout
    assert out.read_text(encoding="utf-8").rstrip("\n") == stdout.rstrip("\n")


def test_counts_without_out_writes_no_file(tmp_path):
    report, labels, tax_path = counts_files(tmp_path)
    before = sorted(p.name for p in tmp_path.iterdir())
    run(["counts", str(report), "--labels", str(labels), "--taxonomy", str(tax_path)])
    assert sorted(p.name for p in tmp_path.iterdir()) == before


def test_counts_default_labels_path_is_by_report_stem(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    report, labels, tax_path = counts_files(tmp_path)  # labels at labels/run.jsonl
    (tmp_path / "evals" / "labels").mkdir(parents=True)
    default = tmp_path / "evals" / "labels" / "run.jsonl"
    default.write_text(labels.read_text(encoding="utf-8"), encoding="utf-8")
    data = json.loads(tax_path.read_text(encoding="utf-8"))
    data["labels"] = "evals/labels/run.jsonl"
    tax_path.write_text(json.dumps(data), encoding="utf-8")
    code, _, err, _ = run(["counts", str(report), "--taxonomy", str(tax_path)])
    assert code == 0, err


def test_counts_rejects_an_invalid_taxonomy_with_exit_2(tmp_path):
    report, labels, _ = counts_files(tmp_path)
    bad = tmp_path / "bad.json"
    bad.write_text(
        json.dumps(
            {
                "labels": str(labels),
                "modes": [{"id": "m1", "name": "One", "description": "d"}],
                "mapping": {"a": ["m1"]},  # c is a fail and unmapped
            }
        ),
        encoding="utf-8",
    )
    code, stdout, err, _ = run(
        ["counts", str(report), "--labels", str(labels), "--taxonomy", str(bad)]
    )
    assert code == 2
    assert "failed case 'c'" in err
    assert stdout == ""


def test_counts_checks_that_the_taxonomy_names_this_labels_file(tmp_path):
    report, labels, tax_path = counts_files(tmp_path)
    data = json.loads(tax_path.read_text(encoding="utf-8"))
    data["labels"] = str(tmp_path / "other.jsonl")
    tax_path.write_text(json.dumps(data), encoding="utf-8")
    code, _, err, _ = run(
        ["counts", str(report), "--labels", str(labels), "--taxonomy", str(tax_path)]
    )
    assert code == 2 and "other.jsonl" in err


def test_counts_missing_files_exit_2(tmp_path):
    report, labels, tax_path = counts_files(tmp_path)
    for argv in (
        [
            "counts",
            str(tmp_path / "none.json"),
            "--labels",
            str(labels),
            "--taxonomy",
            str(tax_path),
        ],
        ["counts", str(report), "--labels", str(tmp_path / "none"), "--taxonomy", str(tax_path)],
        ["counts", str(report), "--labels", str(labels), "--taxonomy", str(tmp_path / "none")],
    ):
        assert run(argv)[0] == 2


def test_counts_and_view_accept_a_report_without_catalogue_sha256(tmp_path):
    # §13 B6: old reports carry no catalogue hash and stay readable.
    assert "catalogue_sha256" not in COUNT_REPORT and "catalogue_sha256" not in REPORT
    report, labels, tax_path = counts_files(tmp_path)
    code, _, err, _ = run(
        ["counts", str(report), "--labels", str(labels), "--taxonomy", str(tax_path)]
    )
    assert code == 0, err
    code, _, err, _ = run(
        ["view", str(write_report(tmp_path)), "--labels", str(tmp_path / "l.jsonl")],
        serve=lambda app, host, port: None,
    )
    assert code == 0, err
