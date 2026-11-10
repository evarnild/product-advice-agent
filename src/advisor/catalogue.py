"""The synthetic product catalogue: loading, validation and search.

Pure logic over data; the only I/O is reading the catalogue file.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CATEGORIES: tuple[str, ...] = (
    "laptop",
    "phone",
    "headphones",
    "monitor",
    "tablet",
    "smartwatch",
    "camera",
    "speaker",
)
DEFAULT_CATALOGUE_PATH = Path(__file__).parent / "data" / "catalogue.json"
MIN_LIMIT = 1
MAX_LIMIT = 10
_ID_RE = re.compile(r"^P-\d{3}$")
_FIELDS = ("id", "name", "brand", "category", "price_eur", "in_stock", "specs", "description")
_TEXT_FIELDS = ("id", "name", "brand", "category", "description")


class CatalogueError(Exception):
    """The catalogue file is missing or malformed."""


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    brand: str
    category: str
    price_eur: float
    in_stock: bool
    specs: dict[str, str]
    description: str


def _is_number(v: Any) -> bool:
    return isinstance(v, int | float) and not isinstance(v, bool)


def _parse_product(raw: Any, index: int, seen: set[str]) -> Product:
    if not isinstance(raw, dict):
        raise CatalogueError(f"entry {index}: expected an object, got {type(raw).__name__}")
    label = raw["id"] if isinstance(raw.get("id"), str) else f"entry {index}"

    def fail(field: str, why: str) -> CatalogueError:
        return CatalogueError(f"product {label}: field '{field}' {why}")

    for field in _FIELDS:
        if field not in raw:
            raise fail(field, "is missing")
    for field in _TEXT_FIELDS:
        if not isinstance(raw[field], str) or not raw[field].strip():
            raise fail(field, "must be a non-empty string")
    if not _ID_RE.match(raw["id"]):
        raise fail("id", "must look like P-001")
    if raw["id"] in seen:
        raise fail("id", "is a duplicate")
    if raw["category"] not in CATEGORIES:
        raise fail("category", f"must be one of {', '.join(CATEGORIES)}")
    if not _is_number(raw["price_eur"]) or raw["price_eur"] <= 0:
        raise fail("price_eur", "must be a number greater than 0")
    if not isinstance(raw["in_stock"], bool):
        raise fail("in_stock", "must be true or false")
    specs = raw["specs"]
    if not isinstance(specs, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in specs.items()
    ):
        raise fail("specs", "must be a map of strings to strings")
    seen.add(raw["id"])
    return Product(
        id=raw["id"],
        name=raw["name"],
        brand=raw["brand"],
        category=raw["category"],
        price_eur=float(raw["price_eur"]),
        in_stock=raw["in_stock"],
        specs=dict(specs),
        description=raw["description"],
    )


def load_catalogue(path: Path | str = DEFAULT_CATALOGUE_PATH) -> list[Product]:
    """Load and validate the catalogue; raise CatalogueError naming product and field."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as e:
        raise CatalogueError(f"cannot read catalogue {path}: {e}") from e
    except json.JSONDecodeError as e:
        raise CatalogueError(f"catalogue {path} is not valid JSON: {e}") from e
    if not isinstance(data, list):
        raise CatalogueError("catalogue must be a JSON list of products")
    seen: set[str] = set()
    return [_parse_product(raw, i, seen) for i, raw in enumerate(data)]


def _norm(text: str) -> str:
    return text.lower().replace("-", " ")


def search_products(
    catalogue: Sequence[Product],
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    keywords: Sequence[str] | None = None,
    in_stock_only: bool = False,
    limit: int = 5,
) -> list[Product]:
    """Products matching every given filter, cheapest first (ties by id), at most `limit`.

    `limit` is clamped to 1..10. Keywords all have to appear, case-insensitively,
    in the name, brand or description. A hyphen counts as a space, in keywords and
    product text alike, so 'noise-cancelling' finds 'noise cancelling' (§7).
    """
    limit = max(MIN_LIMIT, min(MAX_LIMIT, limit))
    words = [_norm(k) for k in keywords or [] if _norm(k).strip()]

    def matches(p: Product) -> bool:
        if category is not None and p.category != category:
            return False
        if min_price is not None and p.price_eur < min_price:
            return False
        if max_price is not None and p.price_eur > max_price:
            return False
        if in_stock_only and not p.in_stock:
            return False
        haystack = _norm(f"{p.name} {p.brand} {p.description}")
        return all(w in haystack for w in words)

    return sorted((p for p in catalogue if matches(p)), key=lambda p: (p.price_eur, p.id))[:limit]
