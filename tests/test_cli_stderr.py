"""What a run prints on stderr, in a fresh interpreter.

In-process the test would pass whatever the code does: pytest installs its own
log handlers, so `logging.lastResort` never fires. A subprocess has none.
"""

import subprocess
import sys

PROBE = """
import logging
import sys

from advisor import cli
from advisor.models.base import ModelTurn
from advisor.models.fake import ScriptedModelClient
from advisor.tracing import NoopTracer


class ExportFailingTracer(NoopTracer):
    def finish(self, answer):
        logging.getLogger("opentelemetry.exporter.otlp.common.http").error(
            "Failed to export span batch due to timeout, max retries or shutdown."
        )
        logging.getLogger("langfuse").warning("Langfuse host unreachable.")


cli.make_tracer = lambda env, tags=(): ExportFailingTracer()
if "--root-handler" in sys.argv:
    sys.argv.remove("--root-handler")
    logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
client = ScriptedModelClient([ModelTurn(text="Fine answer.")])
env = {"ADVISOR_MODEL_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "placeholder-key"}
code = cli.main(sys.argv[1:], env=env,
                client_factory=lambda provider, model, *, api_key=None, base_url=None: client)
sys.exit(code)
"""


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", PROBE, *args], capture_output=True, text=True, timeout=60
    )


def test_library_log_lines_are_silent_without_debug():
    result = _run("q")
    assert result.returncode == 0
    assert "Fine answer." in result.stdout
    assert "Failed to export" not in result.stderr
    assert "Langfuse host unreachable" not in result.stderr


def test_library_log_lines_show_with_debug():
    result = _run("--debug", "q")
    assert result.returncode == 0
    assert "Fine answer." in result.stdout
    assert "Failed to export" in result.stderr
    assert "Langfuse host unreachable" in result.stderr


def test_an_existing_logging_setup_is_left_alone():
    # Whoever installed a root handler asked for log lines; the CLI keeps out.
    result = _run("--root-handler", "q")
    assert result.returncode == 0
    assert "Fine answer." in result.stdout
    assert "Failed to export" in result.stderr
