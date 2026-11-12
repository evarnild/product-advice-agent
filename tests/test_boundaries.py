"""Provider and tracing SDKs are imported in exactly one module each (spec AC6)."""

import ast
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src" / "advisor"


def _importers(package: str) -> set[str]:
    found = set()
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            if any(n == package or n.startswith(package + ".") for n in names):
                found.add(path.relative_to(SRC).as_posix())
    return found


def test_only_the_anthropic_adapter_imports_anthropic():
    assert _importers("anthropic") == {"models/anthropic_model.py"}


def test_only_tracing_imports_langfuse():
    assert _importers("langfuse") <= {"tracing.py"}


def test_pure_modules_load_no_tracing_sdk():
    # A fresh interpreter: the pytest process has already imported langfuse.
    code = (
        "import sys\n"
        "import advisor.agent, advisor.catalogue, advisor.guardrails, advisor.models\n"
        "bad = sorted(m for m in sys.modules\n"
        "             if m.split('.')[0] in ('langfuse', 'opentelemetry'))\n"
        "print(bad)\n"
        "sys.exit(1 if bad else 0)\n"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[:500] + result.stderr[-500:]


def test_only_the_ollama_adapter_imports_httpx():
    assert _importers("httpx") == {"models/ollama_model.py"}


def test_cli_imports_no_http_library_or_provider_module():
    tree = ast.parse((SRC / "cli.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert not {i for i in imported if i.split(".")[0] in {"httpx", "anthropic", "langfuse"}}
    assert not {i for i in imported if i.endswith(("ollama_model", "anthropic_model"))}


def test_eval_runner_loads_no_sdk():
    # A fresh interpreter; adapters are imported lazily by make_client, and the
    # suite never imports advisor.tracing.
    code = (
        "import sys\n"
        "import advisor.evals.run\n"
        "bad = sorted(m for m in sys.modules\n"
        "             if m.split('.')[0] in ('langfuse', 'opentelemetry', 'anthropic', 'httpx')\n"
        "             or m == 'advisor.tracing')\n"
        "print(bad)\n"
        "sys.exit(1 if bad else 0)\n"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[:500] + result.stderr[-500:]


def test_an_untraced_eval_run_loads_neither_tracing_nor_langfuse(tmp_path):
    # A fresh interpreter runs one case with the scripted fake and no LANGFUSE_*.
    code = (
        "import io, json, sys\n"
        "from pathlib import Path\n"
        "from advisor.evals.run import main\n"
        "from advisor.models.base import ModelTurn\n"
        "from advisor.models.fake import ScriptedModelClient\n"
        "tmp = Path(sys.argv[1])\n"
        "cases = tmp / 'cases.jsonl'\n"
        "case = {'id': 'lap', 'question': 'a laptop?', 'expect_ids': ['P-009']}\n"
        "cases.write_text(json.dumps(case), encoding='utf-8')\n"
        "text = 'The Pelagic Go 13 (P-009) costs 649 euros.'\n"
        "client = ScriptedModelClient([ModelTurn(text=text)])\n"
        "out = io.StringIO()\n"
        "rc = main(['--cases', str(cases), '--report-dir', str(tmp / 'runs')],\n"
        "          env={'ADVISOR_MODEL_PROVIDER': 'ollama', 'ADVISOR_MODEL': 'm'},\n"
        "          client_factory=lambda *a, **k: client, out=out, err=io.StringIO())\n"
        "assert rc == 0, out.getvalue()\n"
        "bad = sorted(m for m in sys.modules\n"
        "             if m.split('.')[0] in ('langfuse', 'opentelemetry')\n"
        "             or m == 'advisor.tracing')\n"
        "print(bad)\n"
        "sys.exit(1 if bad else 0)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout[:500] + result.stderr[-500:]


def test_eval_runner_langfuse_variables_match_the_tracing_module():
    from advisor.evals.run import _LANGFUSE_ENV
    from advisor.tracing import REQUIRED_ENV

    assert set(_LANGFUSE_ENV) == set(REQUIRED_ENV)
    assert tuple(_LANGFUSE_ENV) == tuple(REQUIRED_ENV)


# --- §9: the web framework lives in the viewer only -------------------------


def test_only_the_viewer_imports_the_web_framework():
    for package in ("fasthtml", "starlette", "uvicorn"):
        assert _importers(package) == {"evals/view.py"}, package


_WEB = ("fasthtml", "starlette", "uvicorn")
_SDKS = ("langfuse", "opentelemetry", "anthropic", "httpx")


def _loads_none_of(modules: str, banned: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    code = (
        "import sys\n"
        f"for name in {modules!r}.split(','):\n"
        "    __import__(name)\n"
        f"bad = sorted(m for m in sys.modules if m.split('.')[0] in {banned!r})\n"
        "print(bad)\n"
        "sys.exit(1 if bad else 0)\n"
    )
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)


def test_pure_analysis_modules_load_no_web_framework_and_no_sdk():
    pure = "cases,coverage,labels,taxonomy,counts,report,modeljson,generate"
    modules = ",".join(f"advisor.evals.{m}" for m in pure.split(","))
    result = _loads_none_of(modules, _WEB + _SDKS)
    assert result.returncode == 0, result.stdout[:500] + result.stderr[-500:]


def test_the_command_and_the_runner_load_no_web_framework_until_view_runs():
    result = _loads_none_of("advisor.evals.analysis,advisor.evals.run", _WEB + _SDKS)
    assert result.returncode == 0, result.stdout[:500] + result.stderr[-500:]


def test_the_checker_catches_a_banned_import():
    # Guards the guard: a module that does load the framework is reported.
    result = _loads_none_of("advisor.evals.view", _WEB)
    assert result.returncode == 1
