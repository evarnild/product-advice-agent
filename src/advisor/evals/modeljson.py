"""Lenient JSON extraction from model output (§9). Pure."""

from __future__ import annotations

import json
import re
from typing import Any

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def extract_json(text: str) -> Any | None:
    """The first JSON array or object in `text`, or None.

    `<think>…</think>` blocks are dropped first, and prose or code fences
    around the JSON are ignored.
    """
    cleaned = _THINK.sub("", text)
    decoder = json.JSONDecoder()
    for match in re.finditer(r"[\[{]", cleaned):
        try:
            value, _ = decoder.raw_decode(cleaned, match.start())
        except json.JSONDecodeError:
            continue
        return value
    return None
