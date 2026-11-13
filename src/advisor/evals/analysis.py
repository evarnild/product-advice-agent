"""The `advisor-analysis` command: generate | view | taxonomy | counts (§9).

Files, the model client, the clock and stdout live here. The pure parts are in
`generate`, `coverage`, `labels`, `taxonomy` and `counts`; the viewer (the only
FastHTML code) is imported only by the `view` subcommand.

Exit codes: 0 done, 1 the work could not be done (model unreachable, nothing
kept, a draft that does not validate), 2 bad arguments or files.
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
from advisor.evals.cases import CaseFileError, parse_cases
from advisor.evals.counts import counts_markdown
from advisor.evals.coverage import sample_cells
from advisor.evals.generate import case_lines, dumps_cases, generate, summary
from advisor.evals.labels import LabelFileError, parse_labels
from advisor.evals.report import ReportError, parse_report
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


if __name__ == "__main__":
    sys.exit(main())
