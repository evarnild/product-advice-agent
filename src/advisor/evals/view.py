"""The label viewer (§9 B8-B12): a local FastHTML app, one conversation per screen.

The only module that imports FastHTML, Starlette or uvicorn. It binds to
127.0.0.1 only, has no CDN or external asset, and saves every label change at
once to a JSON-lines file (`advisor.evals.labels`). Pages are plain forms with
a few lines of inline script for the hotkeys, so they work without JavaScript.
"""

from __future__ import annotations

import json
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar, cast
from urllib.parse import quote, urlencode

import uvicorn
from fasthtml.common import (
    H1,
    H2,
    A,
    Body,
    Button,
    Code,
    Div,
    FastHTML,
    Form,
    Head,
    Header,
    Html,
    Input,
    Label,
    Meta,
    Nav,
    Option,
    P,
    Pre,
    Script,
    Select,
    Span,
    Strong,
    Style,
    Table,
    Td,
    Textarea,
    Th,
    Title,
    Tr,
    to_xml,
)
from starlette.responses import HTMLResponse, RedirectResponse, Response

from advisor.evals.labels import LABELS, check_label, label_line, parse_labels
from advisor.evals.report import STATUSES, parse_report

_F = TypeVar("_F", bound=Callable[..., Any])
LOCAL_HOST = "127.0.0.1"
DEFAULT_PORT = 5209
_LABEL_FILTERS = ("unlabelled", *LABELS)
_DIMENSIONS = ("feature", "scenario", "persona")

_CSS = """
body { font: 15px/1.45 system-ui, sans-serif; margin: 0 auto; max-width: 62rem;
  padding: 0 1rem 4rem; }
header { position: sticky; top: 0; background: #fff; border-bottom: 1px solid #ccc;
  padding: .5rem 0; }
pre, code { white-space: pre-wrap; overflow-wrap: anywhere;
  font: 13px/1.4 ui-monospace, monospace; }
pre { background: #f4f4f4; padding: .5rem; margin: .25rem 0; }
table { border-collapse: collapse; width: 100%; table-layout: fixed; }
td, th { border: 1px solid #ddd; padding: 2px 6px; text-align: left; overflow-wrap: anywhere; }
.turn { border-left: 3px solid #88a; padding-left: .75rem; margin: .75rem 0; }
.tool { background: #f9f9ff; padding: .25rem .5rem; margin: .25rem 0; }
.ok { color: #176f2c; } .bad { color: #b00020; } .muted { color: #666; }
.label-pass { color: #176f2c; font-weight: bold; }
.label-fail { color: #b00020; font-weight: bold; }
.error { background: #fde7e9; border: 1px solid #b00020; padding: .5rem; }
.saved { background: #e6f4ea; padding: .25rem .5rem; }
textarea { width: 100%; box-sizing: border-box; min-height: 5rem; }
form.filters label { margin-right: .75rem; }
nav a, button { margin-right: .5rem; }
"""

_SCRIPT = """
(function () {
  var form = document.getElementById('label-form');
  var critique = document.getElementById('critique');
  var pending = document.getElementById('pending-label');
  function submitWith(action) {
    var i = document.createElement('input');
    i.type = 'hidden'; i.name = 'action'; i.value = action;
    form.appendChild(i); form.submit();
  }
  function go(id) { var a = document.getElementById(id); if (a) { window.location = a.href; } }
  document.addEventListener('keydown', function (e) {
    if (e.ctrlKey || e.metaKey || e.altKey) { return; }
    var t = e.target;
    if (t && t.id === 'critique') {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitWith('save'); }
      else if (e.key === 'Escape') { t.blur(); }
      return;
    }
    var tag = t ? t.tagName : '';
    if (tag === 'TEXTAREA' || tag === 'INPUT' || tag === 'SELECT') { return; }
    if (!form) { return; }
    if (e.key === 'p') { e.preventDefault(); submitWith('pass'); }
    else if (e.key === 'f') {
      e.preventDefault(); pending.value = 'fail';
      document.getElementById('pending-note').textContent = 'fail: write the critique, Enter saves';
      critique.focus();
    }
    else if (e.key === 'j') { go('next'); }
    else if (e.key === 'k') { go('prev'); }
  });
})();
"""


@dataclass(frozen=True)
class Filters:
    feature: str = ""
    scenario: str = ""
    persona: str = ""
    label: str = ""
    status: str = ""

    def query(self, **extra: str) -> str:
        pairs = {
            "f_feature": self.feature,
            "f_scenario": self.scenario,
            "f_persona": self.persona,
            "f_label": self.label,
            "f_status": self.status,
            **extra,
        }
        return urlencode({k: v for k, v in pairs.items() if v})

    def hidden(self) -> list[Any]:
        return [
            Input(type="hidden", name=name, value=value)
            for name, value in (
                ("f_feature", self.feature),
                ("f_scenario", self.scenario),
                ("f_persona", self.persona),
                ("f_label", self.label),
                ("f_status", self.status),
            )
            if value
        ]


def _matches(case: dict[str, Any], current: Any, f: Filters) -> bool:
    """All given filters must hold (AND)."""
    dims = case.get("dimensions") or {}
    for key in _DIMENSIONS:
        wanted = getattr(f, key)
        if wanted and dims.get(key) != wanted:
            return False
    if f.label:
        have = "unlabelled" if current is None else current.label
        if have != f.label:
            return False
    return not (f.status and case["status"] != f.status)


def _money(v: Any) -> str:
    return f"{v:.2f}" if isinstance(v, int | float) else str(v)


def _products(results: list[dict[str, Any]]) -> Any:
    if not results:
        return P("no products returned", cls="muted")
    rows = [Tr(Th("id"), Th("name"), Th("price (EUR)"), Th("stock"))]
    for p in results:
        stock = "in stock" if p.get("in_stock") else "OUT OF STOCK"
        rows.append(
            Tr(
                Td(str(p.get("id"))),
                Td(str(p.get("name"))),
                Td(_money(p.get("price_eur"))),
                Td(stock),
            )
        )
    return Table(*rows)


def _tool_call(call: dict[str, Any]) -> Any:
    head = Div(
        Strong(str(call.get("name"))),
        " ",
        Code(json.dumps(call.get("arguments", {}), ensure_ascii=False)),
    )
    if call.get("error"):
        return Div(head, P("the tool call was an error", cls="bad"), cls="tool")
    return Div(head, _products(call.get("results", [])), cls="tool")


def _turns(case: dict[str, Any]) -> list[Any]:
    turns = case.get("turns")
    if turns is None:
        return [P("model turns were not recorded in this report", cls="muted")]
    tools = list(case.get("tools") or [])
    out: list[Any] = []
    for number, turn in enumerate(turns, start=1):
        names = list(turn.get("tools") or [])
        mine, tools = tools[: len(names)], tools[len(names) :]
        parts: list[Any] = [Strong(f"Model turn {number}")]
        if turn.get("text"):
            parts.append(Pre(turn["text"]))
        parts.extend(_tool_call(c) for c in mine)
        out.append(Div(*parts, cls="turn"))
    return out


def _checks(case: dict[str, Any]) -> list[Any]:
    rows: list[Any] = []
    status_cls = "ok" if case["status"] == "PASS" else "bad"
    rows.append(P("Automatic status: ", Span(case["status"], cls=status_cls)))
    if case.get("error"):
        rows.append(P(f"error: {case['error']}", cls="bad"))
    for c in case.get("checks") or []:
        mark = "ok" if c.get("ok") else "FAILED"
        rows.append(
            P(
                Span(f"{c.get('name')}: {mark}", cls="ok" if c.get("ok") else "bad"),
                f" {c.get('reason', '')}" if c.get("reason") else "",
            )
        )
    return rows


def _guardrails(case: dict[str, Any]) -> list[Any]:
    rows = case.get("guardrails")
    if rows is None:
        return [P("guardrail checks were not recorded in this report", cls="muted")]
    return [
        P(
            f"{g.get('stage')}: {'allowed' if g.get('allowed') else 'BLOCKED'}"
            + (f" ({g['reason']})" if g.get("reason") else "")
        )
        for g in rows
    ]


def _page(*body: Any, title: str = "Conversation labels") -> str:
    return str(
        to_xml(
            Html(
                Head(Meta(charset="utf-8"), Title(title), Style(_CSS)),
                Body(*body, Script(_SCRIPT)),
            )
        )
    )


def _route(app: FastHTML, method: str, path: str) -> Callable[[_F], _F]:
    """`app.get(path)` / `app.post(path)` with the handler's type kept (FastHTML is untyped)."""
    return cast("Callable[[_F], _F]", getattr(app, method)(path))


def make_app(
    report_path: Path,
    labels_path: Path,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> FastHTML:
    """The viewer for one report. Raises OSError / ReportError / LabelFileError on bad files."""
    report = parse_report(report_path.read_text(encoding="utf-8"))
    cases: list[dict[str, Any]] = report["cases"]
    by_id = {c["id"]: c for c in cases}
    labels = parse_labels(labels_path.read_text(encoding="utf-8")) if labels_path.exists() else {}
    values = {
        key: sorted({(c.get("dimensions") or {}).get(key, "") for c in cases} - {""})
        for key in _DIMENSIONS
    }
    app = FastHTML(default_hdrs=False, pico=False, live=False, secret_key=secrets.token_hex(32))

    def filtered(f: Filters) -> list[dict[str, Any]]:
        return [c for c in cases if _matches(c, labels.get(c["id"]), f)]

    def neighbour(case_id: str, f: Filters, step: int) -> dict[str, Any] | None:
        """The nearest filtered case after (+1) or before (-1) `case_id` in report order."""
        here = [c["id"] for c in cases].index(case_id)
        order = cases[here + 1 :] if step > 0 else cases[:here][::-1]
        return next((c for c in order if _matches(c, labels.get(c["id"]), f)), None)

    def counts() -> tuple[int, int, int]:
        mine = [labels[i] for i in by_id if i in labels]
        return len(mine), sum(x.label == "pass" for x in mine), sum(x.label == "fail" for x in mine)

    def select(name: str, current: str, options: list[str], text: str) -> Any:
        return Label(
            text + " ",
            Select(
                Option("any", value="", selected=not current),
                *[Option(o, value=o, selected=(o == current)) for o in options],
                name=name,
            ),
        )

    def filter_form(f: Filters) -> Any:
        return Form(
            select("f_feature", f.feature, values["feature"], "feature"),
            select("f_scenario", f.scenario, values["scenario"], "scenario"),
            select("f_persona", f.persona, values["persona"], "persona"),
            select("f_label", f.label, list(_LABEL_FILTERS), "label"),
            select("f_status", f.status, list(STATUSES), "status"),
            Button("Filter", type="submit"),
            method="get",
            action="/",
            cls="filters",
        )

    def header(f: Filters, position: str) -> Any:
        done, passed, failed = counts()
        return Header(
            H1(
                f"{position}", Span(f"  labelled {done}, pass {passed}, fail {failed}", cls="muted")
            ),
            filter_form(f),
        )

    def render(
        case: dict[str, Any],
        f: Filters,
        *,
        saved: bool = False,
        error: str = "",
        draft: str | None = None,
        pending: str = "",
        status_code: int = 200,
    ) -> Response:
        in_list = filtered(f)
        ids = [c["id"] for c in in_list]
        position = (
            f"{ids.index(case['id']) + 1} / {len(ids)}"
            if case["id"] in ids
            else f"not in this filter / {len(ids)}"
        )
        current = labels.get(case["id"])
        prev_case, next_case = neighbour(case["id"], f, -1), neighbour(case["id"], f, +1)

        def link(target: dict[str, Any] | None, ident: str, text: str) -> Any:
            if target is None:
                return Span(text, cls="muted")
            return A(text, href=f"/c/{quote(target['id'])}?{f.query()}", id=ident)

        dims = case.get("dimensions")
        dim_line = (
            " · ".join(f"{k}: {dims[k]}" for k in _DIMENSIONS if k in dims)
            if dims
            else "no dimensions"
        )
        label_text = (
            Span(f"{current.label}", cls=f"label-{current.label}")
            if current
            else Span("unlabelled")
        )
        shown_critique = draft if draft is not None else (current.critique if current else "")
        form = Form(
            *f.hidden(),
            Input(
                type="hidden",
                name="label",
                value=pending or (current.label if current else ""),
                id="pending-label",
            ),
            Textarea(
                shown_critique,
                name="critique",
                id="critique",
                placeholder="critique (required for a fail)",
            ),
            Div(
                Button("Pass (p)", type="submit", name="action", value="pass"),
                Button("Fail (f)", type="submit", name="action", value="fail"),
                Button("Save and next (Enter)", type="submit", name="action", value="save"),
                Span("", id="pending-note", cls="muted"),
            ),
            method="post",
            action=f"/c/{quote(case['id'])}/label",
            id="label-form",
        )
        body = [
            header(f, position),
            Nav(link(prev_case, "prev", "Previous (k)"), link(next_case, "next", "Next (j)")),
            *([Div(error, cls="error")] if error else []),
            *([Div("Saved", cls="saved")] if saved else []),
            H2(case["id"]),
            P(Strong("Question: "), case["question"]),
            P(Strong("Dimensions: "), dim_line),
            H2("Checks"),
            *_checks(case),
            H2("Conversation"),
            *_turns(case),
            H2("Answer"),
            Pre(case["answer"]),
            H2("Guardrails"),
            *_guardrails(case),
            H2("Label"),
            P("Current label: ", label_text),
            form,
        ]
        return HTMLResponse(_page(*body, title=case["id"]), status_code=status_code)

    def filters_from(
        f_feature: str, f_scenario: str, f_persona: str, f_label: str, f_status: str
    ) -> Filters:
        return Filters(f_feature, f_scenario, f_persona, f_label, f_status)

    @_route(app, "get", "/")
    def index(
        f_feature: str = "",
        f_scenario: str = "",
        f_persona: str = "",
        f_label: str = "",
        f_status: str = "",
    ) -> Response:
        f = filters_from(f_feature, f_scenario, f_persona, f_label, f_status)
        matching = filtered(f)
        if not matching:
            return HTMLResponse(
                _page(
                    header(f, "0 / 0"),
                    P("No conversation matches these filters."),
                )
            )
        return RedirectResponse(f"/c/{quote(matching[0]['id'])}?{f.query()}", status_code=303)

    @_route(app, "get", "/c/{case_id}")
    def conversation(
        case_id: str,
        f_feature: str = "",
        f_scenario: str = "",
        f_persona: str = "",
        f_label: str = "",
        f_status: str = "",
        saved: str = "",
    ) -> Response:
        case = by_id.get(case_id)
        if case is None:
            return HTMLResponse(_page(P(f"No conversation '{case_id}'.")), status_code=404)
        f = filters_from(f_feature, f_scenario, f_persona, f_label, f_status)
        return render(case, f, saved=bool(saved))

    @_route(app, "post", "/c/{case_id}/label")
    def save_label(
        case_id: str,
        action: str = "",
        label: str = "",
        critique: str = "",
        f_feature: str = "",
        f_scenario: str = "",
        f_persona: str = "",
        f_label: str = "",
        f_status: str = "",
    ) -> Response:
        case = by_id.get(case_id)
        if case is None:
            return HTMLResponse(_page(P(f"No conversation '{case_id}'.")), status_code=404)
        f = filters_from(f_feature, f_scenario, f_persona, f_label, f_status)
        chosen = {"pass": "pass", "fail": "fail", "save": label}.get(action, "")
        problem = check_label(chosen, critique) if chosen else "choose pass or fail first"
        if problem is not None:
            return render(
                case,
                f,
                error=problem.capitalize() + ".",
                draft=critique,
                pending=label,
                status_code=422,
            )
        line = label_line(case_id, chosen, critique, now(), case["question"], case["answer"])
        labels_path.parent.mkdir(parents=True, exist_ok=True)
        with labels_path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(line)
            fh.flush()
        labels.update(parse_labels(line))
        target = neighbour(case_id, f, +1) if action == "save" else None
        if target is None:
            return RedirectResponse(f"/c/{quote(case_id)}?{f.query(saved='1')}", status_code=303)
        return RedirectResponse(f"/c/{quote(target['id'])}?{f.query()}", status_code=303)

    return app


def serve(app: FastHTML, host: str, port: int) -> None:
    """Run the app; refuses anything but the loopback address."""
    if host != LOCAL_HOST:
        raise ValueError(f"the viewer binds to {LOCAL_HOST} only, not {host}")
    uvicorn.run(app, host=host, port=port, log_level="warning")
