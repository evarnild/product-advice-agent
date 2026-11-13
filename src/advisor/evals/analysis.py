"""The `advisor-analysis` command: generate | view | taxonomy | counts (§9), queue | import (§10).

Files, the model client, the clock and stdout live here. The pure parts are in
`generate`, `coverage`, `labels`, `taxonomy` and `counts`; the viewer (the only
FastHTML code) is imported only by the `view` subcommand. `queue` and `import` reach
Langfuse through `annotate.Annotations`; `advisor.tracing` is imported only when one runs.

Exit codes: 0 done, 1 the work could not be done (model unreachable, nothing
kept, a draft that does not validate), 2 bad arguments or files, and for `queue` and
`import` also a missing `LANGFUSE_*` variable, filters that match no case, a queue
that does not exist or conflicts, and a Langfuse error.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

from advisor.catalogue import CatalogueError, load_catalogue
from advisor.config import ConfigError, load_env, load_settings
from advisor.evals import taxonomy as tax
from advisor.evals.annotate import (
    AnnotationError,
    Annotations,
    case_traces,
    default_queue_name,
    labels_from_scores,
    plan_additions,
    report_stamp,
    select_cases,
)
from advisor.evals.cases import CaseFileError, parse_cases
from advisor.evals.counts import counts_markdown
from advisor.evals.coverage import sample_cells
from advisor.evals.generate import case_lines, dumps_cases, generate, summary
from advisor.evals.labels import LabelFileError, parse_labels
from advisor.evals.report import STATUSES, ReportError, parse_report
from advisor.models import KNOWN_PROVIDERS, make_client
from advisor.models.base import (
    Message,
    ModelClient,
    ModelError,
    ModelNotAvailableError,
    ModelUnreachableError,
)

DEFAULT_GENERATED = Path("evals") / "generated.jsonl"
DEFAULT_LABELS_DIR = Path("evals") / "labels"
DEFAULT_TAXONOMY = Path("evals") / "taxonomy.json"
DEFAULT_DRAFT = Path("evals") / "taxonomy.draft.json"
LOCAL_HOST = "127.0.0.1"
DEFAULT_PORT = 5209

ServeFn = Callable[[Any, str, int], None]
AnnotationsFactory = Callable[[Mapping[str, str]], Annotations]

# The same three names as `advisor.tracing.REQUIRED_ENV` (a test compares them).
# Importing that constant would load `langfuse`, which only `queue` and `import` may do.
_LANGFUSE_ENV = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST")


def _default_annotations_factory(env: Mapping[str, str]) -> Annotations:
    # Lazy on purpose: importing `advisor.tracing` loads langfuse (§10 B19).
    from advisor.tracing import make_annotations

    return make_annotations(env)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="advisor-analysis",
        description="Error analysis on top of the eval suite: questions, labels, failure modes.",
    )
    p.add_argument("--debug", action="store_true", help="show tracebacks")
    sub = p.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate", help="write synthetic questions by dimension")
    g.add_argument("--out", type=Path, default=DEFAULT_GENERATED)
    g.add_argument("--count", type=int, default=60, help="questions to ask for (default 60)")
    g.add_argument("--seed", type=int, default=9, help="seed of the cell sample (default 9)")
    g.add_argument("--force", action="store_true", help="overwrite an existing file")

    v = sub.add_parser("view", help="label the conversations of a report in a local viewer")
    v.add_argument("report", type=Path)
    v.add_argument("--port", type=int, default=DEFAULT_PORT)
    v.add_argument("--labels", type=Path, default=None, help="default evals/labels/<report>.jsonl")

    t = sub.add_parser("taxonomy", help="draft failure modes from the critiques of the fails")
    t.add_argument("labels", type=Path)
    t.add_argument("--out", type=Path, default=DEFAULT_DRAFT)

    c = sub.add_parser("counts", help="count failure modes and compare with the automatic checks")
    c.add_argument("report", type=Path)
    c.add_argument("--labels", type=Path, default=None, help="default evals/labels/<report>.jsonl")
    c.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    c.add_argument("--out", type=Path, default=None, help="also write the tables to this file")

    q = sub.add_parser("queue", help="put a run's traces in a Langfuse annotation queue")
    q.add_argument("report", type=Path)
    q.add_argument("--queue", default=None, help="queue name (default advisor-eval <run stamp>)")
    q.add_argument("--feature", default=None, help="only cases with this feature")
    q.add_argument("--scenario", default=None, help="only cases with this scenario")
    q.add_argument("--persona", default=None, help="only cases with this persona")
    q.add_argument("--status", choices=STATUSES, default=None, help="only cases with this status")

    i = sub.add_parser("import", help="turn a queue's Langfuse scores into label lines")
    i.add_argument("report", type=Path)
    i.add_argument("--queue", default=None, help="queue name (default advisor-eval <run stamp>)")
    i.add_argument("--labels", type=Path, default=None, help="default evals/labels/<report>.jsonl")
    return p


def labels_path_for(report: Path) -> Path:
    return DEFAULT_LABELS_DIR / f"{report.stem}.jsonl"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def main(
    argv: Sequence[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    client_factory: Callable[..., ModelClient] = make_client,
    out: TextIO | None = None,
    err: TextIO | None = None,
    now: Callable[[], datetime] = _utc_now,
    serve: ServeFn | None = None,
    annotations_factory: AnnotationsFactory | None = None,
) -> int:
    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err

    def say(message: str) -> None:
        print(message, file=out)

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

    def model_client() -> ModelClient | int:
        settings = load_settings(load_env(env))
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
                    f"Missing {settings.api_key_variable}: set it in the environment or in .env.",
                    2,
                )
        base_url: str | None = None
        if settings.provider == "ollama":
            try:
                base_url = settings.ollama_url()
            except ConfigError as e:
                return fail(str(e), 2)
        return client_factory(settings.provider, settings.model, api_key=api_key, base_url=base_url)

    if args.command == "generate":
        if args.count < 1:
            return fail("--count must be at least 1", 2)
        if args.out.exists() and not args.force:
            return fail(f"{args.out} exists; use --force to overwrite it", 2)
        try:
            catalogue = load_catalogue()
        except CatalogueError as e:
            return fail(f"Catalogue error: {e}", 2)
        client = model_client()
        if isinstance(client, int):
            return client
        cells = sample_cells(args.count, args.seed)
        try:
            result = generate(cells, client, catalogue)
        except (ModelUnreachableError, ModelNotAvailableError) as e:
            return fail(str(e), 1)
        for line in summary(result):
            say(line)
        lines = case_lines(result)
        if not lines:
            return fail("No question was kept; nothing written.", 1)
        text = dumps_cases(lines)
        try:
            parse_cases(text, catalogue)  # what is written must be a valid case file
        except CaseFileError as e:  # a bug here, not the owner's input
            return fail(f"Internal error: the generated cases are invalid: {e}", 1)
        try:
            _write(args.out, text)
        except OSError as e:
            return fail(f"Could not write {args.out}: {e.strerror or e}", 1)
        say(f"wrote {len(lines)} questions to {args.out}")
        return 0

    if args.command == "view":
        labels = args.labels or labels_path_for(args.report)
        from advisor.evals.view import make_app
        from advisor.evals.view import serve as run_server

        try:
            app = make_app(args.report, labels, now)
        except OSError as e:
            return fail(f"Cannot read {e.filename or args.report}: {e.strerror or e}", 2)
        except (UnicodeDecodeError, ReportError, LabelFileError) as e:
            return fail(f"Cannot use {args.report} or {labels}: {e}", 2)
        say(f"serving http://{LOCAL_HOST}:{args.port} (labels: {labels}); Ctrl+C stops it")
        (serve or run_server)(app, LOCAL_HOST, args.port)
        return 0

    if args.command == "taxonomy":
        try:
            labels = parse_labels(args.labels.read_text(encoding="utf-8"))
        except OSError as e:
            return fail(f"Cannot read {args.labels}: {e.strerror or e}", 2)
        except (UnicodeDecodeError, LabelFileError) as e:
            return fail(f"Labels file error: {e}", 2)
        if not tax.failed(labels):
            return fail(f"No failed conversation in {args.labels}; nothing to draft.", 2)
        client = model_client()
        if isinstance(client, int):
            return client
        prompt = tax.build_prompt(labels)
        try:
            reply = client.complete("", [Message("user", prompt)], [])
        except (ModelUnreachableError, ModelNotAvailableError, ModelError) as e:
            return fail(str(e), 1)
        taxonomy, errors = tax.parse_draft(reply.text or "", labels, str(args.labels))
        if taxonomy is None:
            for error in errors:
                print(f"Draft rejected: {error}", file=err)
            return fail("The model's draft does not validate; nothing written.", 1)
        try:
            _write(args.out, tax.dumps(taxonomy))
        except OSError as e:
            return fail(f"Could not write {args.out}: {e.strerror or e}", 1)
        say(f"wrote {len(taxonomy.modes)} failure modes to {args.out}; edit it, then save it as")
        say(f"{DEFAULT_TAXONOMY} (it is committed; the draft is not)")
        return 0

    if args.command in ("queue", "import"):
        return _annotation_command(
            args, env, annotations_factory or _default_annotations_factory, say, fail, err
        )

    # counts
    labels_file = args.labels or labels_path_for(args.report)
    try:
        report = parse_report(args.report.read_text(encoding="utf-8"))
        labels = parse_labels(labels_file.read_text(encoding="utf-8"))
        raw = json.loads(args.taxonomy.read_text(encoding="utf-8"))
    except OSError as e:
        return fail(f"Cannot read {e.filename or args.report}: {e.strerror or e}", 2)
    except (UnicodeDecodeError, ReportError, LabelFileError, json.JSONDecodeError) as e:
        return fail(f"Input error: {e}", 2)
    taxonomy, errors = tax.parse_taxonomy(raw)
    if taxonomy is not None:
        errors = tax.validate(taxonomy, labels)
        if Path(taxonomy.labels).resolve() != labels_file.resolve():
            errors.append(f"the taxonomy maps {taxonomy.labels}, not {labels_file}")
    if taxonomy is None or errors:
        for error in errors:
            print(f"Taxonomy error: {error}", file=err)
        return 2
    text = counts_markdown(report, labels, taxonomy)
    say(text.rstrip("\n"))
    if args.out is not None:
        try:
            _write(args.out, text)
        except OSError as e:
            return fail(f"Could not write {args.out}: {e.strerror or e}", 1)
    return 0


def _annotation_command(
    args: argparse.Namespace,
    env: Mapping[str, str] | None,
    factory: AnnotationsFactory,
    say: Callable[[str], None],
    fail: Callable[[str, int], int],
    err: TextIO,
) -> int:
    """`queue` and `import` (§10): the report, the labels file, and Langfuse through `factory`."""
    full_env = load_env(env)
    missing = [k for k in _LANGFUSE_ENV if not full_env.get(k)]
    if missing:
        return fail(
            f"{args.command} needs {', '.join(missing)}: set it in the environment or in .env.", 2
        )
    try:
        report = parse_report(args.report.read_text(encoding="utf-8"))
        stamp = report_stamp(report)
    except OSError as e:
        return fail(f"Cannot read {e.filename or args.report}: {e.strerror or e}", 2)
    except (UnicodeDecodeError, ReportError, ValueError) as e:
        return fail(f"Input error: {e}", 2)
    name = args.queue or default_queue_name(stamp)

    if args.command == "queue":
        selected = select_cases(
            report,
            feature=args.feature,
            scenario=args.scenario,
            persona=args.persona,
            status=args.status,
        )
        if not selected:
            return fail("No case in the report matches the filters; nothing queued.", 2)
        added = 0
        try:
            annotations = factory(full_env)
            config_id = annotations.ensure_score_config()
            queue_id = annotations.ensure_queue(name, config_id)
            by_case, duplicates = case_traces(annotations.run_traces(stamp))
            plan = plan_additions(selected, by_case, annotations.queued_trace_ids(queue_id))
            for _case_id, trace_id in plan.to_add:
                annotations.add_trace(queue_id, trace_id)
                added += 1
        except AnnotationError as e:
            if added:
                print(f"queue {name}: {added} added before the error", file=err)
            return fail(str(e), 2)
        if duplicates:
            say(f"{duplicates} duplicate trace(s) for a case tag; the latest start was used")
        say(
            f"queue {name}: {added} added, {plan.already_queued} already queued, "
            f"{plan.no_trace} no trace"
        )
        return 0

    # import
    labels_file = args.labels or labels_path_for(args.report)
    try:
        existing_text = labels_file.read_text(encoding="utf-8") if labels_file.exists() else ""
        current = parse_labels(existing_text)
    except OSError as e:
        return fail(f"Cannot read {labels_file}: {e.strerror or e}", 2)
    except (UnicodeDecodeError, LabelFileError) as e:
        return fail(f"Labels file error: {e}", 2)
    try:
        annotations = factory(full_env)
        found_id = annotations.find_queue(name)
        if found_id is None:
            return fail(f"Queue '{name}' does not exist; run `advisor-analysis queue` first.", 2)
        by_case, duplicates = case_traces(annotations.run_traces(stamp))
        scores = annotations.annotation_scores(found_id)
    except AnnotationError as e:
        return fail(str(e), 2)
    result = labels_from_scores(report, scores, by_case, current)
    if result.lines:
        prefix = "\n" if existing_text and not existing_text.endswith("\n") else ""
        try:
            labels_file.parent.mkdir(parents=True, exist_ok=True)
            with labels_file.open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(prefix + "".join(result.lines))
        except OSError as e:
            return fail(f"Could not write {labels_file}: {e.strerror or e}", 1)
    if duplicates:
        say(f"{duplicates} duplicate trace(s) for a case tag; the latest start was used")
    if result.fail_without_critique:
        say(
            "fail without a critique, not written: "
            + ", ".join(result.fail_without_critique)
            + " (add a comment to the score in Langfuse, then import again)"
        )
    say(
        f"import: {len(result.lines)} labels written, {result.unchanged} unchanged, "
        f"{len(result.fail_without_critique)} fail without critique, "
        f"{result.outside_run} outside the run"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
