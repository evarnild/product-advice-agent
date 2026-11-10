"""Provider and tracing SDKs are imported in exactly one module each (spec AC6)."""

import ast
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
