import hashlib

import pytest

from advisor.evals.baseline import (
    EVAL_PATHS,
    BaselineError,
    baseline_from,
    check_baseline,
    compare,
    content_sha256,
    format_comparison,
    owes_run,
)


@pytest.mark.parametrize("path", EVAL_PATHS)
def test_each_listed_path_owes_a_run(path):
    assert owes_run([path]) == [path]


@pytest.mark.parametrize(
    "path",
    [
        "src/advisor/prompts/system.md",
        "src/advisor/data/x.json",
        "src/advisor/models/fake.py",
        "src\\advisor\\agent.py",
    ],
)
def test_files_under_listed_directories_owe(path):
    assert owes_run([path]) == [path.replace("\\", "/")]


@pytest.mark.parametrize(
    "path",
    [
        "src/advisor/tracing.py",
        "README.md",
        "scripts/x.mjs",
        "src/advisor/database.py",
        "src/advisor/agent.pyc",
        "src/advisor/models.py",
        "evals/cases.jsonl.bak",
        "src/advisor/evals/run.py",
        "",
    ],
)
def test_near_misses_do_not_owe(path):
    assert owes_run([path]) == []


def test_empty_list_owes_nothing_and_only_matches_are_returned():
    assert owes_run([]) == []
    assert owes_run(["README.md", "src/advisor/agent.py"]) == ["src/advisor/agent.py"]


def rep(statuses, **extra):
    r = {
        "provider": "ollama",
        "model": "m",
        "cases_sha256": "c",
        "prompt_sha256": "p",
        "catalogue_sha256": "k",
        "cases": [{"id": i, "question": "q", "answer": "a", "status": s} for i, s in statuses],
    }
    r.update(extra)
    return r


def test_baseline_copies_fields():
    b = baseline_from(rep([("a", "PASS"), ("b", "FAIL")]), "run.json")
    assert b == {
        "source": "run.json",
        "provider": "ollama",
        "model": "m",
        "cases_sha256": "c",
        "prompt_sha256": "p",
        "catalogue_sha256": "k",
        "cases": {"a": "PASS", "b": "FAIL"},
    }


def test_baseline_without_catalogue_hash_has_none():
    r = rep([("a", "PASS")])
    del r["catalogue_sha256"]
    assert "catalogue_sha256" not in baseline_from(r, "x")


def test_check_baseline_rejects_bad_shapes():
    for bad in ([], {"cases": []}, {"cases": {"a": "MAYBE"}}):
        with pytest.raises(BaselineError):
            check_baseline(bad)


def test_compare_categories_rates_and_no_warnings():
    old = rep([("a", "PASS"), ("b", "PASS"), ("c", "FAIL"), ("d", "ERROR"), ("gone", "PASS")])
    base = baseline_from(old, "b.json")
    new = rep(
        [
            ("a", "FAIL"),
            ("b", "ERROR"),
            ("c", "PASS"),
            ("d", "PASS"),
            ("new", "PASS"),
            ("newfail", "FAIL"),
        ]
    )
    c = compare(new, base)
    assert c.regressed == [("a", "PASS", "FAIL"), ("b", "PASS", "ERROR")]
    assert c.fixed == [("c", "FAIL", "PASS"), ("d", "ERROR", "PASS")]
    assert c.added == ["new", "newfail"] and c.removed == ["gone"]
    assert "newfail" not in [r[0] for r in c.regressed]
    assert (c.old_passed, c.old_total, c.new_passed, c.new_total) == (3, 5, 3, 6)
    assert c.warnings == []
    text = format_comparison(c)
    assert "3/5 passed" in text and "a: PASS -> FAIL" in text and "removed (1)" in text


def test_compare_warns_once_per_differing_field():
    base = baseline_from(rep([("a", "PASS")]), "b.json")
    new = rep(
        [("a", "PASS")],
        provider="anthropic",
        model="n",
        cases_sha256="x",
        prompt_sha256="y",
        catalogue_sha256="z",
    )
    assert len(compare(new, base).warnings) == 5
    gone = rep([("a", "PASS")])
    del gone["catalogue_sha256"]
    assert len(compare(gone, base).warnings) == 1


def test_identical_run_has_no_flips():
    r = rep([("a", "PASS"), ("b", "FAIL")])
    c = compare(r, baseline_from(r, "r.json"))
    assert not (c.regressed or c.fixed or c.added or c.removed or c.warnings)


def test_policy_path_list_equals_eval_paths():
    import re
    from pathlib import Path

    policy = (Path(__file__).resolve().parents[1] / "REVIEW-POLICY.md").read_text(encoding="utf-8")
    section = policy.split("## Eval runs", 1)[1].split("\n## ", 1)[0]
    listed = re.findall(r"^  - `([^`]+)`\s*$", section, flags=re.MULTILINE)
    assert tuple(listed) == EVAL_PATHS


def test_report_format_has_eval_run_after_live_check():
    from pathlib import Path

    policy = (Path(__file__).resolve().parents[1] / "REVIEW-POLICY.md").read_text(encoding="utf-8")
    assert policy.index("\n## Live check\n") < policy.index("\n## Eval run\n")


def test_content_sha256_is_the_same_for_lf_crlf_and_mixed():
    want = hashlib.sha256(b"a\nb\nc\n").hexdigest()
    for data in (b"a\nb\nc\n", b"a\r\nb\r\nc\r\n", b"a\r\nb\nc\r\n"):
        assert content_sha256(data) == want


def test_content_sha256_still_sees_other_whitespace():
    base = content_sha256(b"a\nb\n")
    for other in (b"a \nb\n", b"a\n\nb\n", b"a\nb", b"a\rb\n", b"a\nb\n\n"):
        assert content_sha256(other) != base
