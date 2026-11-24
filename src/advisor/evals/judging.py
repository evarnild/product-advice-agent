"""`advisor-analysis judge` and `judge-validate` (§16): the I/O around `judge.py`.

Files, the model client, the clock and Langfuse (through `Annotations`) are
here; the prompt, the verdict and the agreement maths are in `judge`.
`analysis.main` calls these two functions. The judge is pinned to Anthropic
(`claude-haiku-5-5`): `--model` may change the model, never the provider, and
the advisor's own `ADVISOR_MODEL_PROVIDER` / `ADVISOR_MODEL` are not read.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO

from advisor.config import DEFAULT_MODELS, load_env
from advisor.evals import judge as jg
from advisor.evals.annotate import (
    JUDGE_SCORE_NAME,
    AnnotationError,
    Annotations,
    JudgeScore,
    case_traces,
    report_stamp,
)
from advisor.evals.labels import Label, LabelFileError, parse_labels
from advisor.evals.report import ReportError, parse_report
from advisor.models import PROVIDER_KEY_ENV
from advisor.models.base import Message, ModelClient, ModelError

PROVIDER = "anthropic"
DEFAULT_SPLIT = Path("evals") / "judge" / "split.json"
DEFAULT_VALIDATION = Path("evals") / "judge" / "validation.md"
DEFAULT_JUDGEMENTS_DIR = Path("evals") / "judgements"
DEFAULT_LABELS_DIR = Path("evals") / "labels"
DEFAULT_RUNS_DIR = Path("evals") / "runs"
LANGFUSE_ENV = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST")

ClientFactory = Callable[..., ModelClient]
AnnotationsFactory = Callable[[Mapping[str, str]], Annotations]


class InputError(Exception):
    """A file or setting the command needs is missing or invalid (exit 2)."""


@dataclass(frozen=True)
class Paths:
    split: Path
    labels_dir: Path
    runs_dir: Path


def _client(
    env: Mapping[str, str] | None, model: str | None, factory: ClientFactory
) -> tuple[ModelClient, str]:
    """B5: Anthropic only; the key is checked before the client is built."""
    full_env = load_env(env)
    variable = PROVIDER_KEY_ENV[PROVIDER]
    key = full_env.get(variable)
    if not key:
        raise InputError(f"Missing {variable}: set it in the environment or in .env.")
    name = model or DEFAULT_MODELS[PROVIDER]
    return factory(PROVIDER, name, api_key=key, base_url=None), name


def _load_split(paths: Paths) -> tuple[jg.Split, dict[str, Label]]:
    """The split, checked against the current labels; returns each ref's label."""
    try:
        value = json.loads(paths.split.read_text(encoding="utf-8"))
    except OSError as e:
        raise InputError(f"Cannot read {paths.split}: {e.strerror or e}") from e
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise InputError(f"{paths.split} is not valid JSON: {e}") from e
    try:
        raw = jg.parse_split(value)  # shape first, so the files named are known
        files: dict[str, dict[str, Label]] = {}
        by_ref: dict[str, Label] = {}
        for ref in (*raw.few_shot, *raw.held_out):
            file, case_id = jg.parse_ref(ref)
            if file not in files:
                files[file] = parse_labels((paths.labels_dir / file).read_text(encoding="utf-8"))
            if case_id in files[file]:
                by_ref[ref] = files[file][case_id]
        split = jg.parse_split(value, {r: x.label for r, x in by_ref.items()})
    except OSError as e:
        raise InputError(f"Cannot read {e.filename}: {e.strerror or e}") from e
    except (UnicodeDecodeError, LabelFileError, jg.SplitError) as e:
        raise InputError(f"Split error: {e}") from e
    return split, by_ref


def _report_case(paths: Paths, ref: str) -> dict[str, Any] | None:
    """The run report's case for a split entry, or None when the report or case is missing."""
    file, case_id = jg.parse_ref(ref)
    report_path = paths.runs_dir / f"{Path(file).stem}.json"
    try:
        text = report_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except (OSError, UnicodeDecodeError) as e:
        raise InputError(f"Cannot read {report_path}: {getattr(e, 'strerror', None) or e}") from e
    try:
        report = parse_report(text)
    except ReportError as e:
        raise InputError(f"{report_path}: {e}") from e
    for case in report["cases"]:
        if case["id"] == case_id:
            return dict(case)
    return None


def _text_of(label: Label, case: Mapping[str, Any]) -> str:
    # The label line's question and answer are what the owner judged; the
    # report only adds the tool calls.
    return jg.conversation(label.question, case.get("tools"), label.answer)


def _examples(split: jg.Split, by_ref: Mapping[str, Label], paths: Paths) -> list[jg.Example]:
    examples: list[jg.Example] = []
    for ref in split.few_shot:
        case = _report_case(paths, ref)
        if case is None:
            file, case_id = jg.parse_ref(ref)
            raise InputError(
                f"few-shot example {ref} needs case '{case_id}' in "
                f"{paths.runs_dir / (Path(file).stem + '.json')} (its tool calls)"
            )
        if not jg.in_scope(case):  # B6: only in-scope conversations are used
            raise InputError(
                f"few-shot example {ref} is not in scope "
                "(its scenario is not no-match or budget-too-low)"
            )
        label = by_ref[ref]
        examples.append(jg.Example(ref, label.label, label.critique, _text_of(label, case)))
    return examples


def _ask(client: ModelClient, prompt: str) -> jg.Verdict | jg.JudgeError:
    try:
        reply = client.complete("", [Message("user", prompt)], [], schema=jg.VERDICT_SCHEMA)
    except ModelError as e:
        return jg.JudgeError(str(e))
    return jg.parse_verdict(reply.text or "")


def _prompt_hash(examples: list[jg.Example]) -> str:
    # Of the template with its examples filled in and the conversation slot
    # left open, so one hash names the instructions and examples of a run.
    return hashlib.sha256(jg.build_prompt(None, "[[conversation]]", examples).encode()).hexdigest()


def _verdict_line(verdict: jg.Verdict | jg.JudgeError, name: str) -> str:
    if isinstance(verdict, jg.JudgeError):
        return f"ERROR {name}: {verdict.reason}"
    return f"{'PASS' if verdict.passed else 'FAIL'} {name}: {verdict.reason}"


def run_judge(
    *,
    report_path: Path,
    paths: Paths,
    judgements_dir: Path,
    model: str | None,
    env: Mapping[str, str] | None,
    client_factory: ClientFactory,
    annotations_factory: AnnotationsFactory,
    now: Callable[[], datetime],
    say: Callable[[str], None],
    err: TextIO,
) -> int:
    """B5, B8-B11. Exit 0 when it ran, 2 on bad input, a missing key or a Langfuse error."""
    try:
        return _run_judge(
            report_path=report_path,
            paths=paths,
            judgements_dir=judgements_dir,
            model=model,
            env=env,
            client_factory=client_factory,
            annotations_factory=annotations_factory,
            now=now,
            say=say,
            err=err,
        )
    except (InputError, AnnotationError) as e:
        print(e, file=err)
        return 2


def _run_judge(
    *,
    report_path: Path,
    paths: Paths,
    judgements_dir: Path,
    model: str | None,
    env: Mapping[str, str] | None,
    client_factory: ClientFactory,
    annotations_factory: AnnotationsFactory,
    now: Callable[[], datetime],
    say: Callable[[str], None],
    err: TextIO,
) -> int:
    client, model_name = _client(env, model, client_factory)  # no call before this passes
    try:
        report = parse_report(report_path.read_text(encoding="utf-8"))
    except OSError as e:
        raise InputError(f"Cannot read {report_path}: {e.strerror or e}") from e
    except (UnicodeDecodeError, ReportError) as e:
        raise InputError(f"Input error: {e}") from e
    cases = [c for c in report["cases"] if jg.in_scope(c)]
    if not cases:
        raise InputError("No in-scope case (no-match or budget-too-low) in the report.")
    split, by_ref = _load_split(paths)
    examples = _examples(split, by_ref, paths)
    sha = _prompt_hash(examples)

    results: list[tuple[str, jg.Verdict | jg.JudgeError, datetime]] = []
    for case in cases:
        text = jg.conversation(case["question"], case.get("tools"), case["answer"])
        verdict = _ask(client, jg.build_prompt(None, text, examples))
        results.append((case["id"], verdict, now()))
        say(_verdict_line(verdict, case["id"]))
    passed = sum(1 for _, v, _ in results if isinstance(v, jg.Verdict) and v.passed)
    failed = sum(1 for _, v, _ in results if isinstance(v, jg.Verdict) and not v.passed)
    errors = len(results) - passed - failed
    say(f"judged {len(results)}: {passed} pass, {failed} fail, {errors} error")

    lines = [
        json.dumps(
            {
                "case_id": case_id,
                "pass": verdict.passed if isinstance(verdict, jg.Verdict) else None,
                "reason": verdict.reason,
                "model": model_name,
                "prompt_sha256": sha,
                "judged_at": when.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            ensure_ascii=False,
        )
        for case_id, verdict, when in results
    ]
    target = judgements_dir / f"{report_path.stem}.jsonl"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        # B9: rewritten whole, so a rerun replaces the file.
        target.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    except OSError as e:
        print(f"Could not write {target}: {e.strerror or e}", file=err)
        return 1
    say(f"wrote {len(results)} verdicts to {target}")

    full_env = load_env(env)
    if not all(full_env.get(k) for k in LANGFUSE_ENV):
        say(f"Langfuse is not configured: only {target} was written, no score.")
        return 0
    try:
        stamp = report_stamp(report)
    except ValueError as e:
        raise InputError(f"Input error: {e}") from e
    # B8, B11: Langfuse only through `Annotations`. A judge error gets no score.
    annotations = annotations_factory(full_env)
    config_id = annotations.ensure_judge_config()
    by_case, _ = case_traces(annotations.run_traces(stamp))
    scores: list[JudgeScore] = []
    no_trace = 0
    for case_id, verdict, _ in results:
        if not isinstance(verdict, jg.Verdict):
            continue
        trace_id = by_case.get(case_id)
        if trace_id is None:
            no_trace += 1
            continue
        scores.append(
            JudgeScore(jg.score_id(stamp, case_id), trace_id, verdict.passed, verdict.reason)
        )
    annotations.write_scores(scores, config_id)
    say(f"{JUDGE_SCORE_NAME}: {len(scores)} scored, {no_trace} no trace")
    return 0


def run_validate(
    *,
    paths: Paths,
    out_path: Path,
    model: str | None,
    env: Mapping[str, str] | None,
    client_factory: ClientFactory,
    say: Callable[[str], None],
    err: TextIO,
) -> int:
    """B7: judge the held-out conversations and write `validation.md`."""
    try:
        client, model_name = _client(env, model, client_factory)
        split, by_ref = _load_split(paths)
        examples = _examples(split, by_ref, paths)
        rows: list[jg.ValidationRow] = []
        skipped: list[str] = []
        for ref in split.held_out:
            label = by_ref[ref]
            case = _report_case(paths, ref)
            if case is None:
                file, _ = jg.parse_ref(ref)
                skipped.append(f"{ref}: no report {Path(file).stem}.json or no such case in it")
                continue
            if not jg.in_scope(case):
                skipped.append(f"{ref}: not in scope (scenario is not no-match or budget-too-low)")
                continue
            verdict = _ask(client, jg.build_prompt(None, _text_of(label, case), examples))
            say(_verdict_line(verdict, ref))
            rows.append(
                jg.ValidationRow(
                    ref,
                    label.label == "pass",
                    label.critique,
                    verdict.passed if isinstance(verdict, jg.Verdict) else None,
                    verdict.reason,
                )
            )
    except InputError as e:
        print(e, file=err)
        return 2
    for line in skipped:
        say(f"skipped {line}")
    text = jg.validation_markdown(
        rows,
        model=model_name,
        prompt_sha256=_prompt_hash(examples),
        few_shot=split.few_shot,
        skipped=skipped,
    )
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8", newline="\n")
    except OSError as e:
        print(f"Could not write {out_path}: {e.strerror or e}", file=err)
        return 1
    a = jg.agreement([(r.owner_pass, r.judge_pass) for r in rows])
    say(f"{'trusted' if a.trusted else 'not trusted'}: wrote {out_path}")
    return 0
