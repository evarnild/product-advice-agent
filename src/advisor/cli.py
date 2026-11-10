"""Command-line entry point: wires config, catalogue, model, tracing and the agent.

I/O and wiring only; the logic worth testing lives in `agent`, `catalogue`
and `guardrails`.
"""

from __future__ import annotations

import logging
import sys
import traceback
from collections.abc import Callable, Mapping, Sequence

from advisor.agent import answer_question, search_tool
from advisor.catalogue import CatalogueError, load_catalogue
from advisor.config import load_env, load_settings
from advisor.models import KNOWN_PROVIDERS, make_client
from advisor.models.base import ModelClient
from advisor.tracing import make_tracer

USAGE = 'usage: advisor [--debug] "<question>"'
UNAVAILABLE = "The advisor is unavailable right now."

ClientFactory = Callable[[str, str, str], ModelClient]


def _fail(message: str, code: int = 1) -> int:
    print(message, file=sys.stderr)
    return code


def main(
    argv: Sequence[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    client_factory: ClientFactory = make_client,
) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    debug = "--debug" in args
    words = [a for a in args if a != "--debug"]
    question = " ".join(words).strip()
    if not question or question.startswith("-"):
        return _fail(USAGE, 2)
    if debug:
        logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
        logging.getLogger("advisor").setLevel(logging.DEBUG)
    else:
        # Spec B17: a tracing failure never shows as a run error. Without
        # --debug, OpenTelemetry's own log lines (e.g. "Failed to export span
        # batch") must not reach stderr via logging.lastResort.
        otel = logging.getLogger("opentelemetry")
        otel.addHandler(logging.NullHandler())
        otel.propagate = False
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8", errors="replace")

    full_env = load_env(env)
    settings = load_settings(full_env)
    if settings.provider not in KNOWN_PROVIDERS:
        return _fail(
            f"Unknown model provider '{settings.provider}'. "
            f"Known providers: {', '.join(KNOWN_PROVIDERS)}."
        )
    api_key = settings.api_key()
    if not api_key:
        return _fail(f"Missing {settings.key_variable}: set it in the environment or in .env.")
    try:
        catalogue = load_catalogue()
    except CatalogueError as e:
        return _fail(f"Catalogue error: {e}")

    try:
        client = client_factory(settings.provider, settings.model, api_key)
        tracer = make_tracer(full_env)
        answer = answer_question(question, client, [search_tool(catalogue)], tracer)
    except Exception:
        if debug:
            traceback.print_exc()
        return _fail(UNAVAILABLE)
    print(answer)
    return 0
