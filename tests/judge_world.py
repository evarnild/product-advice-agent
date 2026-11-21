"""A tiny world for the §16 tests: labels, a run report, a split, a routed fake model."""

import io
import json
from pathlib import Path

from advisor.evals.analysis import main
from advisor.models.base import Message, ModelTurn, ToolSpec

STAMP = "20261113T072503Z"
ENV = {"ANTHROPIC_API_KEY": "sk-ant-test-key", "ADVISOR_MODEL_PROVIDER": "ollama"}
LANGFUSE_ENV = {
    "LANGFUSE_HOST": "http://langfuse.invalid",
    "LANGFUSE_PUBLIC_KEY": "pk-secret-public",
    "LANGFUSE_SECRET_KEY": "sk-secret-private",
}
LABELS_FILE = "L.jsonl"

# case id -> (scenario, owner label, critique)
CASES = {
    "f1": ("no-match", "fail", "Smartwatches are not headphones."),
    "p1": ("budget-too-low", "pass", ""),
    "h1": ("no-match", "pass", ""),
    "h2": ("budget-too-low", "fail", "It implies a fit."),
    "h3": ("no-match", "fail", "Proposes another kind."),
    "x1": ("exact-match", "pass", ""),
}


def question(cid):
    return f"Q-{cid} question"


def answer(cid):
    return f"A-{cid} answer"


def write_world(root: Path, *, report=True, split=None, cases=CASES) -> dict[str, Path]:
    labels_dir, runs_dir = root / "labels", root / "runs"
    labels_dir.mkdir()
    runs_dir.mkdir()
    lines = []
    for cid, (_scenario, label, critique) in cases.items():
        record = {
            "case_id": cid,
            "label": label,
            "critique": critique,
            "labelled_at": "2026-11-13T10:00:00Z",
            "question": question(cid),
            "answer": answer(cid),
        }
        lines.append(json.dumps(record))
    (labels_dir / LABELS_FILE).write_text("\n".join(lines) + "\n", encoding="utf-8")
    report_path = runs_dir / "L.json"
    if report:
        body = {
            "started": "2026-11-13T07:25:03.632117+00:00",
            "cases": [
                {
                    "id": cid,
                    "question": question(cid),
                    "answer": answer(cid),
                    "status": "PASS",
                    "dimensions": {"feature": "phone", "scenario": scenario, "persona": "p"},
                    "tools": [
                        {
                            "name": "search_products",
                            "arguments": {"category": f"cat-{cid}"},
                            "results": [{"id": f"P-{cid}", "name": f"Name-{cid}"}],
                            "error": False,
                        }
                    ],
                }
                for cid, (scenario, _l, _c) in cases.items()
            ],
        }
        report_path.write_text(json.dumps(body), encoding="utf-8")
    split_path = root / "split.json"
    default_split = {
        "few_shot": [f"{LABELS_FILE}#f1", f"{LABELS_FILE}#p1"],
        "held_out": [f"{LABELS_FILE}#h1", f"{LABELS_FILE}#h2", f"{LABELS_FILE}#h3"],
    }
    split_path.write_text(json.dumps(split or default_split), encoding="utf-8")
    return {
        "labels_dir": labels_dir,
        "runs_dir": runs_dir,
        "report": report_path,
        "split": split_path,
        "judgements": root / "judgements",
        "validation": root / "validation.md",
    }


class RoutedClient:
    """Answers by the conversation being judged (the part after the examples)."""

    def __init__(self, answers):
        self.answers = answers  # case id -> model text, or an Exception
        self.prompts: list[str] = []

    def complete(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> ModelTurn:
        prompt = messages[0].text
        self.prompts.append(prompt)
        judged = prompt.split("Now judge this conversation.")[1]
        for cid, reply in self.answers.items():
            if question(cid) in judged:
                if isinstance(reply, Exception):
                    raise reply
                return ModelTurn(text=reply)
        raise AssertionError("no scripted answer for " + judged[:200])


def verdict(passed, reason="because"):
    return json.dumps({"pass": passed, "reason": reason})


class Factory:
    def __init__(self, client):
        self.client = client
        self.calls = []

    def __call__(self, provider, model, *, api_key, base_url):
        self.calls.append((provider, model, api_key, base_url))
        return self.client


def run(argv, *, env=ENV, client=None, annotations=None):
    out, err = io.StringIO(), io.StringIO()
    factory = Factory(client or RoutedClient({}))
    annotations_factory = None
    if annotations is not None:

        def annotations_factory(e):
            annotations.envs.append(dict(e))
            return annotations

    code = main(
        list(argv),
        env=env,
        client_factory=factory,
        out=out,
        err=err,
        annotations_factory=annotations_factory,
    )
    return code, out.getvalue(), err.getvalue(), factory
