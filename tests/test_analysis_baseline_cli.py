import io
import json
import subprocess

from advisor.evals.analysis import main


def report(statuses, **extra):
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


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    code = main(argv, out=out, err=err)
    return code, out.getvalue(), err.getvalue()


def write(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_baseline_writes_fields(tmp_path):
    src = write(tmp_path / "run.json", report([("a", "PASS"), ("b", "FAIL")]))
    out = tmp_path / "sub" / "baseline.json"
    code, said, _ = run(["baseline", str(src), "--out", str(out)])
    assert code == 0 and "2 cases" in said
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["source"] == "run.json"
    assert data["catalogue_sha256"] == "k"
    assert data["cases"] == {"a": "PASS", "b": "FAIL"}


def test_baseline_without_catalogue_hash_writes_none(tmp_path):
    r = report([("a", "PASS")])
    del r["catalogue_sha256"]
    src = write(tmp_path / "run.json", r)
    out = tmp_path / "b.json"
    assert run(["baseline", str(src), "--out", str(out)])[0] == 0
    assert "catalogue_sha256" not in json.loads(out.read_text(encoding="utf-8"))


def test_baseline_invalid_or_missing_report_exits_2(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    out = tmp_path / "b.json"
    assert run(["baseline", str(bad), "--out", str(out)])[0] == 2
    assert run(["baseline", str(tmp_path / "none.json"), "--out", str(out)])[0] == 2
    assert not out.exists()


def test_compare_prints_flips_and_exits_0(tmp_path):
    base = tmp_path / "baseline.json"
    run(["baseline", str(write(tmp_path / "old.json", report([("a", "PASS"), ("b", "FAIL")]))),
         "--out", str(base)])  # fmt: skip
    new = write(tmp_path / "new.json", report([("a", "FAIL"), ("b", "PASS")], model="other"))
    code, said, err = run(["compare", str(new), "--baseline", str(base)])
    assert code == 0 and err == ""
    assert "regressed (1)" in said and "a: PASS -> FAIL" in said
    assert "fixed (1)" in said and "b: FAIL -> PASS" in said
    assert "warning: model differs" in said


def test_compare_missing_or_invalid_file_exits_2_naming_it(tmp_path):
    new = write(tmp_path / "new.json", report([("a", "PASS")]))
    missing = tmp_path / "nobaseline.json"
    code, said, err = run(["compare", str(new), "--baseline", str(missing)])
    assert code == 2 and said == "" and "nobaseline.json" in err
    broken = write(tmp_path / "broken.json", {"cases": []})
    assert run(["compare", str(new), "--baseline", str(broken)])[0] == 2
    assert run(["compare", str(tmp_path / "gone.json"), "--baseline", str(broken)])[0] == 2


def git(repo, *args):
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def make_repo(repo, changed):
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    (repo / "README.md").write_text("x", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    git(repo, "checkout", "-q", "-b", "work")
    for name in changed:
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("y", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "work", "--allow-empty")


def test_owes_run_owed_lists_matching_paths(tmp_path, monkeypatch):
    repo = tmp_path / "r1"
    make_repo(repo, ["src/advisor/agent.py", "README.md", "docs/a.md"])
    monkeypatch.chdir(repo)
    code, said, _ = run(["owes-run", "--base", "main"])
    assert code == 0 and said.startswith("owed") and "src/advisor/agent.py" in said
    assert "README.md" not in said


def test_owes_run_not_owed(tmp_path, monkeypatch):
    repo = tmp_path / "r2"
    make_repo(repo, ["README.md", "scripts/x.mjs"])
    monkeypatch.chdir(repo)
    code, said, _ = run(["owes-run"])
    assert code == 0 and said.startswith("not owed")


def test_owes_run_unknown_base_exits_2(tmp_path, monkeypatch):
    repo = tmp_path / "r3"
    make_repo(repo, ["README.md"])
    monkeypatch.chdir(repo)
    assert run(["owes-run", "--base", "nope"])[0] == 2


def test_owes_run_ignores_changes_main_made_after_branching(tmp_path, monkeypatch):
    repo = tmp_path / "r4"
    make_repo(repo, ["README.md"])
    git(repo, "checkout", "-q", "main")
    (repo / "src" / "advisor").mkdir(parents=True)
    (repo / "src" / "advisor" / "agent.py").write_text("z", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "main moves")
    git(repo, "checkout", "-q", "work")
    monkeypatch.chdir(repo)
    code, said, _ = run(["owes-run", "--base", "main"])
    assert code == 0 and said.startswith("not owed")


def test_owes_run_owed_when_a_file_moves_out_of_a_listed_path(tmp_path, monkeypatch):
    repo = tmp_path / "r5"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    (repo / "src" / "advisor" / "prompts").mkdir(parents=True)
    (repo / "src" / "advisor" / "prompts" / "system.md").write_text("p" * 200, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    git(repo, "checkout", "-q", "-b", "work")
    (repo / "docs").mkdir()
    git(repo, "mv", "src/advisor/prompts/system.md", "docs/old-prompt.md")
    git(repo, "commit", "-qm", "move")
    monkeypatch.chdir(repo)
    code, said, _ = run(["owes-run", "--base", "main"])
    assert code == 0 and said.startswith("owed") and "prompts/system.md" in said


def test_baseline_cli_copies_hash_form_and_compare_names_mixed_forms(tmp_path):
    base = tmp_path / "baseline.json"
    old = write(tmp_path / "old.json", report([("a", "PASS")]))
    run(["baseline", str(old), "--out", str(base)])
    assert "hash_form" not in json.loads(base.read_text(encoding="utf-8"))
    new = write(
        tmp_path / "new.json",
        report([("a", "PASS")], hash_form="lf", cases_sha256="x", prompt_sha256="y"),
    )
    code, said, _ = run(["compare", str(new), "--baseline", str(base)])
    assert code == 0
    assert said.count("hashed differently") == 2
    lf_base = tmp_path / "lf.json"
    run(["baseline", str(new), "--out", str(lf_base)])
    assert json.loads(lf_base.read_text(encoding="utf-8"))["hash_form"] == "lf"
