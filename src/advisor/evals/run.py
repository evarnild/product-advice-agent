"""The `advisor-eval` runner: files, the model client, the clock and stdout.

Runs each case once through `answer_question`, scores the answer with the
pure scorers, prints a line per case and a total, and writes a JSON report.
It uses its own recording tracer and never imports `advisor.tracing`, so an
eval run does not reach Langfuse.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import traceback
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

from advisor.agent import SYSTEM_PROMPT_PATH, Tool, answer_question, search_tool
from advisor.catalogue import CatalogueError, load_catalogue
from advisor.config import DEFAULT_MODELS, ConfigError, load_env, load_settings
from advisor.evals.cases import Case, CaseFileError, parse_cases
from advisor.evals.score import Check, score
from advisor.models import KNOWN_PROVIDERS, make_client
from advisor.models.base import (
    ModelClient,
    ModelError,
    ModelNotAvailableError,
    ModelUnreachableError,
    Usage,
)

DEFAULT_CASES = Path("evals") / "cases.jsonl"
DEFAULT_REPORT_DIR = Path("evals") / "runs"


class RecordingTracer:
    """A `Tracer` that keeps what a run did: tool arguments, model turns, guardrail checks.

    `searches` holds the `search_products` arguments (what the scorers read);
    `turns` and `guardrails` are kept for the report (§9 B5).
    """

    def __init__(self) -> None:
        self.searches: list[dict[str, object]] = []
        self.turns: list[dict[str, Any]] = []
        self.guardrails: list[dict[str, Any]] = []

    def begin(self, question: str) -> None:
        pass

    def check(self, stage: str, allowed: bool, reason: str) -> None:
        self.guardrails.append({"stage": stage, "allowed": allowed, "reason": reason})

    def generation(self, model: str, usage: Usage, text: str | None, tool_names: list[str]) -> None:
        self.turns.append({"text": text, "tools": list(tool_names)})

    def tool(self, name: str, arguments: dict[str, object], result_count: int, error: bool) -> None:
        if name == "search_products":
            self.searches.append(dict(arguments))

    def finish(self, answer: str) -> None:
        pass

    def fail(self, error: str) -> None:
        pass


def _recording_tool(tool: Tool, sink: list[dict[str, Any]]) -> Tool:
    """`tool` with the same behaviour, appending each call and its results to `sink` (§9 B6).

    It returns exactly what the tool returned and re-raises what it raised, so
    the agent cannot tell the difference.
    """

    def run(args: dict[str, Any]) -> list[dict[str, Any]]:
        entry: dict[str, Any] = {
            "name": tool.spec.name,
            "arguments": dict(args),
            "results": [],
            "error": True,
        }
        sink.append(entry)
        results = tool.run(args)
        entry["results"] = results
        entry["error"] = False
        return results

    return Tool(tool.spec, run)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="advisor-eval", description="Score the advisor against a fixed question set."
    )
    p.add_argument("--cases", type=Path, default=DEFAULT_CASES, help="the JSON-lines case file")
    p.add_argument("--only", default="", help="comma-separated case ids to run")
    p.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    p.add_argument(
        "--provider",
        choices=KNOWN_PROVIDERS,
        help="model provider for this run (overrides ADVISOR_MODEL_PROVIDER)",
    )
    p.add_argument("--model", help="model name (overrides ADVISOR_MODEL)")
    p.add_argument("--debug", action="store_true", help="show tracebacks")
    return p


def _result_line(status: str, case_id: str, detail: str) -> str:
    return f"{status} {case_id}: {detail}" if detail else f"{status} {case_id}"


def main(
    argv: Sequence[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    client_factory: Callable[..., ModelClient] = make_client,
    out: TextIO | None = None,
    err: TextIO | None = None,
    now: Callable[[], datetime] = _utc_now,
) -> int:
    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err

    def fail(message: str, code: int) -> int:
        print(message, file=err)
        return code

    try:
        args = _parser().parse_args(list(sys.argv[1:] if argv is None else argv))
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 2
    reconfigure = getattr(out, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8", errors="replace")

    try:
        catalogue = load_catalogue()
    except CatalogueError as e:
        return fail(f"Catalogue error: {e}", 2)
    try:
        raw = args.cases.read_bytes()
        cases = parse_cases(raw.decode("utf-8"), catalogue)
    except OSError as e:
        return fail(f"Case file error: cannot read {args.cases}: {e.strerror or e}", 2)
    except (UnicodeDecodeError, CaseFileError) as e:
        return fail(f"Case file error: {e}", 2)
    if args.only:
        wanted = [i.strip() for i in args.only.split(",") if i.strip()]
        unknown = [i for i in wanted if i not in {c.id for c in cases}]
        if unknown or not wanted:
            return fail(f"--only names unknown case id(s): {', '.join(unknown) or '(none)'}", 2)
        cases = [c for c in cases if c.id in wanted]

    settings = load_settings(load_env(env))
    if args.provider:
        settings = replace(
            settings, provider=args.provider, model=DEFAULT_MODELS.get(args.provider, "")
        )
    if args.model:
        settings = replace(settings, model=args.model)
    if settings.provider not in KNOWN_PROVIDERS:
        return fail(
            f"Unknown model provider '{settings.provider}'. "
            f"Known providers: {', '.join(KNOWN_PROVIDERS)}.",
            2,
        )
    api_key: str | None = None
    if settings.api_key_variable is not None:
        api_key = settings.api_key()
        if not api_key:
            return fail(
                f"Missing {settings.api_key_variable}: set it in the environment or in .env.", 2
            )
    base_url: str | None = None
    if settings.provider == "ollama":
        try:
            base_url = settings.ollama_url()
        except ConfigError as e:
            return fail(str(e), 2)
    client = client_factory(settings.provider, settings.model, api_key=api_key, base_url=base_url)

    started = now()
    tool = search_tool(catalogue)
    results: list[dict[str, Any]] = []
    for index, case in enumerate(cases):
        began = now()
        tracer = RecordingTracer()
        tool_calls: list[dict[str, Any]] = []
        answer = ""
        checks: list[Check] = []
        error: str | None = None
        try:
            answer = answer_question(
                case.question, client, [_recording_tool(tool, tool_calls)], tracer
            )
            checks = score(case, answer, tracer.searches, catalogue)
        except (ModelUnreachableError, ModelNotAvailableError) as e:
            if args.debug:
                traceback.print_exc(file=err)
            if index == 0:
                return fail(str(e), 1)
            error = str(e)
        except ModelError as e:
            if args.debug:
                traceback.print_exc(file=err)
            error = str(e)
        except Exception as e:  # one broken case must not end the run
            if args.debug:
                traceback.print_exc(file=err)
            error = f"unexpected {type(e).__name__}"
        results.append(
            _record(case, answer, tracer.searches, checks, error, now() - began, tracer, tool_calls)
        )
        if error is not None:
            print(_result_line("ERROR", case.id, error), file=out)
        else:
            failed = [c.reason for c in checks if not c.ok]
            status = "FAIL" if failed else "PASS"
            print(_result_line(status, case.id, "; ".join(failed)), file=out)

    passed = sum(1 for r in results if r["status"] == "PASS")
    print(f"{passed}/{len(results)} passed ({settings.provider}, {settings.model})", file=out)

    report = {
        "provider": settings.provider,
        "model": settings.model,
        "cases_sha256": hashlib.sha256(raw).hexdigest(),
        "prompt_sha256": hashlib.sha256(SYSTEM_PROMPT_PATH.read_bytes()).hexdigest(),
        "started": started.isoformat(),
        "cases": results,
        "totals": {
            "total": len(results),
            "passed": passed,
            "failed": sum(1 for r in results if r["status"] == "FAIL"),
            "errors": sum(1 for r in results if r["status"] == "ERROR"),
        },
    }
    try:
        args.report_dir.mkdir(parents=True, exist_ok=True)
        stamp = started.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
        path = args.report_dir / f"{stamp}-{settings.provider}.json"
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as e:
        return fail(f"Could not write the report: {e.strerror or e}", 1)
    print(f"report: {path}", file=out)
    return 0 if passed == len(results) else 1


def _record(
    case: Case,
    answer: str,
    searches: list[dict[str, object]],
    checks: list[Check],
    error: str | None,
    duration: Any,
    tracer: RecordingTracer | None = None,
    tool_calls: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if error is not None:
        status = "ERROR"
    else:
        status = "PASS" if all(c.ok for c in checks) else "FAIL"
    record: dict[str, Any] = {
        "id": case.id,
        "question": case.question,
        "status": status,
        "answer": answer,
        "error": error,
        "searches": searches,
        "checks": [{"name": c.name, "ok": c.ok, "reason": c.reason} for c in checks],
        "duration_s": round(duration.total_seconds(), 3),
    }
    if case.dimensions is not None:
        record["dimensions"] = dict(case.dimensions)
    record["turns"] = tracer.turns if tracer is not None else []
    record["tools"] = tool_calls if tool_calls is not None else []
    record["guardrails"] = tracer.guardrails if tracer is not None else []
    return record


if __name__ == "__main__":
    sys.exit(main())
