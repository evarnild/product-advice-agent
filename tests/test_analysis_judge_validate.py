"""§16: `advisor-analysis judge-validate` over fixture labels and a fake model (B7, AC5)."""

import json

from tests.judge_world import (
    LABELS_FILE,
    RoutedClient,
    question,
    run,
    verdict,
    write_world,
)


def validate_argv(w, *extra):
    return [
        "judge-validate",
        "--split",
        str(w["split"]),
        "--labels-dir",
        str(w["labels_dir"]),
        "--runs-dir",
        str(w["runs_dir"]),
        "--out",
        str(w["validation"]),
        *extra,
    ]


def test_the_report_has_the_table_both_rates_and_the_disagreements(tmp_path):
    w = write_world(tmp_path)
    client = RoutedClient(
        {
            "h1": verdict(True, "says none"),  # owner pass, judge pass
            "h2": "no idea",  # owner fail, judge error
            "h3": verdict(True, "looks fine"),  # owner fail, judge pass
        }
    )
    code, out, err, _ = run(validate_argv(w), client=client)
    assert code == 0, err
    text = w["validation"].read_text(encoding="utf-8")
    assert "**Verdict: not trusted.**" in text
    assert "| owner pass | 1 | 0 |" in text
    assert "| owner fail | 1 | 0 |" in text
    assert "1.00 (1/1)" in text  # true-positive rate
    assert "0.00 (0/1)" in text  # true-negative rate
    assert "1 judge errors" in text
    assert f"- {LABELS_FILE}#h3: owner fail, judge pass" in text
    assert "owner: Proposes another kind." in text
    assert "judge: looks fine" in text
    assert f"- {LABELS_FILE}#h2: owner fail, judge ERROR" in text
    assert f"{LABELS_FILE}#h1" not in text.split("## Disagreements")[1]
    assert "- Model: claude-haiku-5-5" in text
    assert "not trusted: wrote" in out


def test_it_judges_only_held_out_conversations_with_the_few_shot_prompt(tmp_path):
    w = write_world(tmp_path)
    client = RoutedClient({"h1": verdict(True), "h2": verdict(False), "h3": verdict(False)})
    code, _, err, _ = run(validate_argv(w), client=client)
    assert code == 0, err
    assert len(client.prompts) == 3
    for prompt in client.prompts:
        examples = prompt.split("Now judge this conversation.")[0]
        assert question("f1") in examples and question("p1") in examples
        for held_out in ("h1", "h2", "h3"):
            assert question(held_out) not in examples  # B6: no held-out text in the prompt
    judged = [p.split("Now judge this conversation.")[1] for p in client.prompts]
    assert [question(c) in j for c, j in zip(("h1", "h2", "h3"), judged, strict=True)] == [True] * 3


def test_a_missing_report_or_an_out_of_scope_case_is_a_reported_skip(tmp_path):
    split = {
        "few_shot": [f"{LABELS_FILE}#f1", f"{LABELS_FILE}#p1"],
        "held_out": [f"{LABELS_FILE}#h1", f"{LABELS_FILE}#x1", f"{LABELS_FILE}#h2"],
    }
    w = write_world(tmp_path, split=split)
    client = RoutedClient({"h1": verdict(True), "h2": verdict(False)})
    code, out, err, _ = run(validate_argv(w), client=client)
    assert code == 0, err
    assert len(client.prompts) == 2
    assert f"skipped {LABELS_FILE}#x1: not in scope" in out
    assert "## Skipped" in w["validation"].read_text(encoding="utf-8")


def test_a_held_out_conversation_without_its_run_report_is_skipped_not_judged(tmp_path):
    w = write_world(tmp_path)
    # a second labels file with no run report next to it
    (w["labels_dir"] / "M.jsonl").write_text(
        (w["labels_dir"] / LABELS_FILE).read_text(encoding="utf-8"), encoding="utf-8"
    )
    split = {
        "few_shot": [f"{LABELS_FILE}#f1", f"{LABELS_FILE}#p1"],
        "held_out": ["M.jsonl#h1", f"{LABELS_FILE}#h2"],
    }
    w["split"].write_text(json.dumps(split), encoding="utf-8")
    client = RoutedClient({"h2": verdict(False)})
    code, out, err, _ = run(validate_argv(w), client=client)
    assert code == 0, err
    assert "skipped M.jsonl#h1: no report M.json" in out
    assert len(client.prompts) == 1


def test_without_the_key_it_exits_2_with_no_call_and_no_file(tmp_path):
    w = write_world(tmp_path)
    code, _, err, factory = run(validate_argv(w), env={})
    assert code == 2
    assert "Missing ANTHROPIC_API_KEY" in err
    assert factory.calls == []
    assert not w["validation"].exists()


def test_a_split_that_names_an_unlabelled_conversation_exits_2(tmp_path):
    split = {
        "few_shot": [f"{LABELS_FILE}#f1", f"{LABELS_FILE}#p1"],
        "held_out": [f"{LABELS_FILE}#ghost"],
    }
    w = write_world(tmp_path, split=split)
    code, _, err, _ = run(validate_argv(w), client=RoutedClient({}))
    assert code == 2
    assert "no current owner label" in err


def test_labels_are_untouched(tmp_path):
    w = write_world(tmp_path)
    before = (w["labels_dir"] / LABELS_FILE).read_bytes()
    client = RoutedClient({"h1": verdict(True), "h2": verdict(False), "h3": verdict(False)})
    run(validate_argv(w), client=client)
    assert (w["labels_dir"] / LABELS_FILE).read_bytes() == before


# --- the trusted rule end to end, at the 0.8 / 30 / 10 boundary -----------------


def big_world(tmp_path, *, wrong_pass, wrong_fail, passes=20, fails=10):
    cases = {"f0": ("no-match", "fail", "bad"), "p0": ("no-match", "pass", "")}
    answers = {}
    held = []
    for i in range(passes):
        cases[f"hp{i}"] = ("no-match", "pass", "")
        answers[f"hp{i}"] = verdict(i >= wrong_pass)  # the first `wrong_pass` judged fail
        held.append(f"{LABELS_FILE}#hp{i}")
    for i in range(fails):
        cases[f"hf{i}"] = ("budget-too-low", "fail", f"critique {i}")
        answers[f"hf{i}"] = verdict(i < wrong_fail)  # the first `wrong_fail` judged pass
        held.append(f"{LABELS_FILE}#hf{i}")
    split = {"few_shot": [f"{LABELS_FILE}#f0", f"{LABELS_FILE}#p0"], "held_out": held}
    return write_world(tmp_path, split=split, cases=cases), answers


def test_trusted_at_exactly_0_8_30_and_10(tmp_path):
    w, answers = big_world(tmp_path, wrong_pass=4, wrong_fail=2)  # 16/20 and 8/10
    code, out, err, _ = run(validate_argv(w), client=RoutedClient(answers))
    assert code == 0, err
    text = w["validation"].read_text(encoding="utf-8")
    assert "**Verdict: trusted.**" in text
    assert "0.80 (4/5)" in text
    assert out.splitlines()[-1].startswith("trusted:")


def test_not_trusted_one_conversation_below_the_rate(tmp_path):
    w, answers = big_world(tmp_path, wrong_pass=5, wrong_fail=2)  # 15/20 = 0.75
    code, _, err, _ = run(validate_argv(w), client=RoutedClient(answers))
    assert code == 0, err
    text = w["validation"].read_text(encoding="utf-8")
    assert "**Verdict: not trusted.** true-positive rate 0.75 is below 0.80" in text


def test_not_trusted_with_29_conversations_or_9_fails(tmp_path):
    for sub, passes, fails, needle in (
        ("a", 19, 10, "29 judged conversations"),
        ("b", 21, 9, "9 owner fails"),
    ):
        root = tmp_path / sub
        root.mkdir()
        w, answers = big_world(root, wrong_pass=0, wrong_fail=0, passes=passes, fails=fails)
        code, _, err, _ = run(validate_argv(w), client=RoutedClient(answers))
        assert code == 0, err
        text = w["validation"].read_text(encoding="utf-8")
        assert "**Verdict: not trusted.**" in text and needle in text
