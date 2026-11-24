import hashlib
import io
import json
import subprocess

import pytest

from advisor.evals import run as runner
from advisor.evals.analysis import main
from advisor.evals.baseline import content_sha256


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


# --- hashes and baseline --rehash (§29) ------------------------------------


CASES_LF = b'{"id": "a"}\n{"id": "b"}\n'
PROMPT_LF = b"You advise.\nBe brief.\n"
CATALOGUE_LF = b'{\n  "products": []\n}\n'


def crlf(data):
    return data.replace(b"\n", b"\r\n")


def working_files(tmp_path, monkeypatch, form=lambda d: d, cases=CASES_LF, prompt=PROMPT_LF,
                  catalogue=CATALOGUE_LF):  # fmt: skip
    cases_path = tmp_path / "cases.jsonl"
    prompt_path = tmp_path / "system.md"
    catalogue_path = tmp_path / "catalogue.json"
    cases_path.write_bytes(form(cases))
    prompt_path.write_bytes(form(prompt))
    catalogue_path.write_bytes(form(catalogue))
    monkeypatch.setattr(runner, "SYSTEM_PROMPT_PATH", prompt_path)
    monkeypatch.setattr(runner, "DEFAULT_CATALOGUE_PATH", catalogue_path)
    return cases_path


def lf_hashes():
    return {
        "cases_sha256": content_sha256(CASES_LF),
        "prompt_sha256": content_sha256(PROMPT_LF),
        "catalogue_sha256": content_sha256(CATALOGUE_LF),
    }


def test_hashes_without_a_file_prints_the_three_lf_hashes(tmp_path, monkeypatch):
    cases = working_files(tmp_path, monkeypatch, crlf)
    code, said, _ = run(["hashes", "--cases", str(cases)])
    assert code == 0
    for key, value in lf_hashes().items():
        assert f"{key} {value}" in said


def test_hashes_matches_a_report_made_on_lf_files_from_crlf_files(tmp_path, monkeypatch):
    cases = working_files(tmp_path, monkeypatch, crlf)
    rep = write(tmp_path / "r.json", report([("a", "PASS")], hash_form="lf", **lf_hashes()))
    code, said, _ = run(["hashes", str(rep), "--cases", str(cases)])
    assert code == 0
    assert said.count("matches") == 3 and "differs" not in said


def test_hashes_names_the_field_that_differs(tmp_path, monkeypatch):
    cases = working_files(tmp_path, monkeypatch, catalogue=CATALOGUE_LF + b" ")
    rep = write(tmp_path / "r.json", report([("a", "PASS")], hash_form="lf", **lf_hashes()))
    code, said, _ = run(["hashes", str(rep), "--cases", str(cases)])
    assert code == 1
    assert "catalogue_sha256 differs" in said
    assert "cases_sha256 matches" in said and "prompt_sha256 matches" in said


def test_hashes_checks_an_old_report_against_raw_bytes(tmp_path, monkeypatch):
    cases = working_files(tmp_path, monkeypatch, crlf)
    raw = {
        "cases_sha256": hashlib.sha256(crlf(CASES_LF)).hexdigest(),
        "prompt_sha256": hashlib.sha256(crlf(PROMPT_LF)).hexdigest(),
        "catalogue_sha256": hashlib.sha256(crlf(CATALOGUE_LF)).hexdigest(),
    }
    rep = write(tmp_path / "r.json", report([("a", "PASS")], **raw))
    code, said, _ = run(["hashes", str(rep), "--cases", str(cases)])
    assert code == 0 and "before §29" in said
    # the same report against LF files: the raw bytes now differ
    cases = working_files(tmp_path, monkeypatch)
    code, said, _ = run(["hashes", str(rep), "--cases", str(cases)])
    assert code == 1 and "before §29" in said


def test_hashes_accepts_a_baseline_file(tmp_path, monkeypatch):
    cases = working_files(tmp_path, monkeypatch)
    base = write(
        tmp_path / "baseline.json",
        {"source": "r.json", "hash_form": "lf", "cases": {"a": "PASS"}, **lf_hashes()},
    )
    assert run(["hashes", str(base), "--cases", str(cases)])[0] == 0


def test_hashes_reports_a_field_not_recorded(tmp_path, monkeypatch):
    cases = working_files(tmp_path, monkeypatch)
    hashes = lf_hashes()
    del hashes["catalogue_sha256"]
    rep = write(tmp_path / "r.json", report([("a", "PASS")], hash_form="lf", **hashes))
    rep_data = json.loads(rep.read_text(encoding="utf-8"))
    del rep_data["catalogue_sha256"]
    write(rep, rep_data)
    code, said, _ = run(["hashes", str(rep), "--cases", str(cases)])
    assert code == 1 and "catalogue_sha256 not recorded" in said


def test_hashes_unreadable_or_invalid_file_exits_2(tmp_path, monkeypatch):
    cases = working_files(tmp_path, monkeypatch)
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    arr = write(tmp_path / "arr.json", [1])
    for target in (bad, arr, tmp_path / "none.json"):
        code, _, err = run(["hashes", str(target), "--cases", str(cases)])
        assert code == 2 and "Traceback" not in err and err
    code, _, err = run(["hashes", "--cases", str(tmp_path / "nocases.jsonl")])
    assert code == 2 and err


def raw_report(tmp_path, form, **over):
    raw = {
        "cases_sha256": hashlib.sha256(form(CASES_LF)).hexdigest(),
        "prompt_sha256": hashlib.sha256(form(PROMPT_LF)).hexdigest(),
        "catalogue_sha256": hashlib.sha256(form(CATALOGUE_LF)).hexdigest(),
    }
    raw.update(over)
    return write(tmp_path / "run.json", report([("a", "PASS"), ("b", "FAIL")], **raw))


@pytest.mark.parametrize("report_form", [lambda d: d, crlf])
@pytest.mark.parametrize("disk_form", [lambda d: d, crlf])
def test_rehash_writes_lf_hashes_when_the_report_saw_these_files(
    tmp_path, monkeypatch, report_form, disk_form
):
    cases = working_files(tmp_path, monkeypatch, disk_form)
    src = raw_report(tmp_path, report_form)
    out = tmp_path / "baseline.json"
    code, _, err = run(["baseline", str(src), "--rehash", "--cases", str(cases), "--out", str(out)])
    assert code == 0, err
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["hash_form"] == "lf"
    for key, value in lf_hashes().items():
        assert data[key] == value
    assert data["cases"] == {"a": "PASS", "b": "FAIL"} and data["source"] == "run.json"
    assert run(["hashes", str(out), "--cases", str(cases)])[0] == 0


def test_rehash_refuses_a_report_of_other_content(tmp_path, monkeypatch):
    cases = working_files(tmp_path, monkeypatch)
    mixed = hashlib.sha256(b'{"id": "a"}\r\n{"id": "b"}\n').hexdigest()
    src = raw_report(tmp_path, lambda d: d, cases_sha256=mixed)
    out = tmp_path / "baseline.json"
    code, _, err = run(["baseline", str(src), "--rehash", "--cases", str(cases), "--out", str(out)])
    assert code == 2 and "cases_sha256" in err
    assert not out.exists()


def test_rehash_refuses_an_lf_report(tmp_path, monkeypatch):
    cases = working_files(tmp_path, monkeypatch)
    src = raw_report(tmp_path, lambda d: d, hash_form="lf")
    out = tmp_path / "baseline.json"
    code, _, err = run(["baseline", str(src), "--rehash", "--cases", str(cases), "--out", str(out)])
    assert code == 2 and "already line-ending free" in err
    assert not out.exists()
