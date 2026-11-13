"""Reading an `advisor-eval` report (§9). Pure: the caller reads the file.

Reports written before §9 lack `turns`, `tools`, `guardrails` and
`dimensions`; those are optional here.
"""

from __future__ import annotations

import json
from typing import Any

STATUSES = ("PASS", "FAIL", "ERROR")


class ReportError(ValueError):
    """The report file is not a usable `advisor-eval` report."""


def parse_report(text: str) -> dict[str, Any]:
    """The report as a dict, checked for the parts the viewer and the counts rely on."""
    try:
        report = json.loads(text)
    except json.JSONDecodeError as e:
        raise ReportError(f"not valid JSON ({e.msg})") from e
    if not isinstance(report, dict) or not isinstance(report.get("cases"), list):
        raise ReportError("not an advisor-eval report (no 'cases' list)")
    seen: set[str] = set()
    for index, case in enumerate(report["cases"], start=1):
        if not isinstance(case, dict):
            raise ReportError(f"case {index}: expected an object")
        for key in ("id", "question", "answer"):
            if not isinstance(case.get(key), str):
                raise ReportError(f"case {index}: field '{key}' must be a string")
        if case["id"] in seen:
            raise ReportError(f"case {index}: duplicate id '{case['id']}'")
        seen.add(case["id"])
        if case.get("status") not in STATUSES:
            raise ReportError(
                f"case '{case['id']}': field 'status' must be one of PASS, FAIL, ERROR"
            )
    return report
