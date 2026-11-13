"""Seeded generator for the synthetic catalogue (§14).

Pure: no file I/O in `build_products`, no model, no randomness outside one
seeded `random.Random`. Not imported by the advisor at runtime. The committed
`data/catalogue.json` is this module's output over its own first 32 products;
`python -m advisor.catalogue_build` rewrites it, `--check` compares without
writing. Brands and product lines are invented.
"""

from __future__ import annotations

import json
import random
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

SEED = 14
HAND_WRITTEN = 32
TARGET_COUNTS: dict[str, int] = {
    "laptop": 63,
    "phone": 63,
    "headphones": 63,
    "monitor": 63,
    "tablet": 62,
    "smartwatch": 62,
    "camera": 62,
    "speaker": 62,
}
# Round-robin order of the new ids across categories.
CATEGORY_ORDER = tuple(TARGET_COUNTS)
PRICE_BANDS: dict[str, tuple[int, int]] = {
    "headphones": (19, 449),
    "laptop": (249, 2999),
    "monitor": (89, 1499),
    "phone": (99, 1799),
    "smartwatch": (29, 799),
    "tablet": (99, 1499),
    "camera": (149, 2999),
    "speaker": (19, 699),
}
SPEC_KEYS: dict[str, tuple[str, ...]] = {
    "headphones": ("type", "noise_cancelling", "battery"),
    "laptop": ("cpu", "ram", "storage", "screen"),
    "monitor": ("size", "resolution", "refresh"),
    "phone": ("screen", "storage", "camera"),
    "smartwatch": ("screen", "battery", "gps"),
    "tablet": ("screen", "storage", "stylus"),
    "camera": ("sensor", "video", "waterproof"),
    "speaker": ("type", "battery", "waterproof"),
}
OLD_BRANDS = ("Auralis", "Kestrel", "Sonavo", "Norvik", "Pelagic", "Tolvane", "Lumino", "Zephra")
NEW_BRANDS = ("Quillon", "Verdane", "Halcyra", "Ostrel")
BRANDS = OLD_BRANDS + NEW_BRANDS
OUT_OF_STOCK_SHARE = 0.15

LINES: dict[str, tuple[str, ...]] = {
    "headphones": ("Calm", "Drift", "Echo", "Hush", "Tempo", "Wave", "Pulse", "Aria", "Muse"),
    "laptop": ("Slate", "Forge", "Atlas", "Ridge", "Orbit", "Vertex", "Studio", "Edge"),
    "monitor": ("View", "Vista", "Prism", "Horizon", "Pane", "Lumen", "Arc", "Frame"),
    "phone": ("Nova", "Spark", "Ember", "Quest", "Pebble", "Zenith", "Flux", "Glint"),
    "smartwatch": ("Tick", "Pace", "Loop", "Stride", "Beacon", "Tempo", "Dial", "Orbit"),
    "tablet": ("Tab", "Canvas", "Pad", "Slate", "Sketch", "Page", "Glide", "Note"),
    "camera": ("Shot", "Lens", "Frame", "Capture", "Aperture", "Trail", "Focus", "Snap"),
    "speaker": ("Boom", "Bar", "Cube", "Echo", "Beat", "Hum", "Stage", "Roam"),
}

Spec = dict[str, str]
Made = tuple[Spec, Callable[[str], str]]


def _pick(values: Sequence[str], tier: float, rng: random.Random) -> str:
    """A value from a ladder that rises with `tier` (0..1), with some jitter."""
    index = int(tier * len(values) + rng.uniform(-0.6, 0.6))
    return values[max(0, min(len(values) - 1, index))]


def _flag(rng: random.Random, low: float, high: float, tier: float) -> bool:
    return rng.random() < low + (high - low) * tier


def _adjective(tier: float) -> str:
    if tier < 0.25:
        return "Budget"
    if tier < 0.5:
        return "Everyday"
    if tier < 0.75:
        return "Capable"
    return "Premium"


def _inch(value: str) -> str:
    return value.replace(" in", " inch")


def _headphones(tier: float, rng: random.Random) -> Made:
    kind = rng.choice(("over-ear", "on-ear", "in-ear"))
    anc = "active" if _flag(rng, 0.05, 0.9, tier) else "none"
    hours = rng.randint(5, 12) if kind == "in-ear" else rng.randint(20, 45)
    spec = {"type": kind, "noise_cancelling": anc, "battery": f"{hours} h"}
    feature = "active noise cancelling" if anc == "active" else "a clear, balanced sound"

    def describe(adj: str) -> str:
        return f"{adj} wireless {kind} headphones with {feature} and {hours} h of battery life."

    return spec, describe


def _laptop(tier: float, rng: random.Random) -> Made:
    spec = {
        "cpu": _pick(("4-core", "6-core", "8-core", "12-core"), tier, rng),
        "ram": _pick(("8 GB", "16 GB", "32 GB", "64 GB"), tier, rng),
        "storage": _pick(("256 GB", "512 GB", "1 TB", "2 TB"), tier, rng),
        "screen": _pick(("11 in", "13 in", "14 in", "15 in", "16 in"), tier, rng),
    }

    def describe(adj: str) -> str:
        return (
            f"{adj} {_inch(spec['screen'])} laptop with a {spec['cpu']} processor, "
            f"{spec['ram']} of memory and {spec['storage']} of storage."
        )

    return spec, describe


def _monitor(tier: float, rng: random.Random) -> Made:
    spec = {
        "size": _pick(("22 in", "24 in", "27 in", "32 in", "34 in"), tier, rng),
        "resolution": _pick(("full HD", "QHD", "4K"), tier, rng),
        "refresh": _pick(("60 Hz", "75 Hz", "144 Hz", "165 Hz"), tier, rng),
    }

    def describe(adj: str) -> str:
        return (
            f"{adj} {_inch(spec['size'])} monitor with {spec['resolution']} resolution "
            f"and a {spec['refresh']} refresh rate."
        )

    return spec, describe


def _phone(tier: float, rng: random.Random) -> Made:
    spec = {
        "screen": _pick(("5.8 in", "6.1 in", "6.4 in", "6.7 in"), tier, rng),
        "storage": _pick(("64 GB", "128 GB", "256 GB", "512 GB", "1 TB"), tier, rng),
        "camera": _pick(("12 MP", "48 MP", "50 MP", "108 MP"), tier, rng),
    }

    def describe(adj: str) -> str:
        return (
            f"{adj} phone with a {_inch(spec['screen'])} screen, {spec['storage']} of storage "
            f"and a {spec['camera']} camera."
        )

    return spec, describe


def _smartwatch(tier: float, rng: random.Random) -> Made:
    gps = "yes" if _flag(rng, 0.1, 0.9, tier) else "no"
    spec = {
        "screen": _pick(("1.2 in", "1.4 in", "1.8 in"), tier, rng),
        "battery": _pick(("1 day", "2 days", "5 days", "10 days", "14 days"), 1 - tier, rng),
        "gps": gps,
    }
    extra = "built-in GPS" if gps == "yes" else "heart-rate tracking"

    def describe(adj: str) -> str:
        return (
            f"{adj} smartwatch with a {_inch(spec['screen'])} display, "
            f"{spec['battery']} of battery life and {extra}."
        )

    return spec, describe


def _tablet(tier: float, rng: random.Random) -> Made:
    stylus = "yes" if _flag(rng, 0.1, 0.8, tier) else "no"
    spec = {
        "screen": _pick(("8 in", "10 in", "11 in", "13 in"), tier, rng),
        "storage": _pick(("64 GB", "128 GB", "256 GB", "512 GB"), tier, rng),
        "stylus": stylus,
    }
    extra = "with stylus support" if stylus == "yes" else "for reading and video"

    def describe(adj: str) -> str:
        return f"{adj} {_inch(spec['screen'])} tablet {extra} and {spec['storage']} of storage."

    return spec, describe


def _camera(tier: float, rng: random.Random) -> Made:
    waterproof = "yes" if _flag(rng, 0.5, 0.1, tier) else "no"
    spec = {
        "sensor": _pick(("1/2.3 in", "1 in", "APS-C", "full frame"), tier, rng),
        "video": _pick(("1080p", "4K", "4K 60", "6K"), tier, rng),
        "waterproof": waterproof,
    }
    extra = ", waterproof without a case" if waterproof == "yes" else ""

    def describe(adj: str) -> str:
        return f"{adj} camera with a {spec['sensor']} sensor and {spec['video']} video{extra}."

    return spec, describe


def _speaker(tier: float, rng: random.Random) -> Made:
    kind = _pick(("pocket", "portable", "party", "bookshelf", "soundbar"), tier, rng)
    mains = kind in ("bookshelf", "soundbar")
    battery = "mains" if mains else f"{rng.randint(8, 30)} h"
    waterproof = "yes" if not mains and rng.random() < 0.6 else "no"
    spec = {"type": kind, "battery": battery, "waterproof": waterproof}
    power = "mains powered" if mains else f"{battery} of battery life"
    extra = ", waterproof for the pool and the beach" if waterproof == "yes" else ""

    def describe(adj: str) -> str:
        return f"{adj} {kind} speaker, {power}{extra}."

    return spec, describe


_MAKERS: dict[str, Callable[[float, random.Random], Made]] = {
    "headphones": _headphones,
    "laptop": _laptop,
    "monitor": _monitor,
    "phone": _phone,
    "smartwatch": _smartwatch,
    "tablet": _tablet,
    "camera": _camera,
    "speaker": _speaker,
}


def _price(category: str, tier: float) -> float:
    lo, hi = PRICE_BANDS[category]
    return float(lo + round(tier * (hi - lo) / 10) * 10)


def _category_products(
    category: str, count: int, taken_names: set[str], rng: random.Random
) -> list[dict[str, Any]]:
    # Stratified tiers, shuffled: every part of the band is used, order is random.
    tiers = [(i + rng.random()) / count for i in range(count)]
    rng.shuffle(tiers)
    out_of_stock = set(rng.sample(range(count), round(count * OUT_OF_STOCK_SHARE)))
    products: list[dict[str, Any]] = []
    for i, tier in enumerate(tiers):
        brand = rng.choice(BRANDS)
        while True:
            name = f"{brand} {rng.choice(LINES[category])} {rng.randint(1, 99)}"
            if name not in taken_names:
                taken_names.add(name)
                break
        spec, describe = _MAKERS[category](tier, rng)
        products.append(
            {
                "name": name,
                "brand": brand,
                "category": category,
                "price_eur": _price(category, tier),
                "in_stock": i not in out_of_stock,
                "specs": spec,
                "description": describe(_adjective(tier)),
            }
        )
    return products


def build_products(existing: Sequence[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    """The hand-written products unchanged, then generated ones up to TARGET_COUNTS.

    New ids continue after the existing ones, handed out round-robin across
    categories. Same input and seed give the same output.
    """
    rng = random.Random(seed)
    have = {c: sum(1 for p in existing if p["category"] == c) for c in CATEGORY_ORDER}
    taken_names = {p["name"] for p in existing}
    pending = {
        c: _category_products(c, TARGET_COUNTS[c] - have[c], taken_names, rng)
        for c in CATEGORY_ORDER
    }
    result: list[dict[str, Any]] = [dict(p) for p in existing]
    next_id = len(result) + 1
    for n in range(max(len(v) for v in pending.values())):
        for c in CATEGORY_ORDER:
            if n < len(pending[c]):
                result.append({"id": f"P-{next_id:03d}", **pending[c][n]})
                next_id += 1
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    check = "--check" in args
    path = Path(__file__).parent / "data" / "catalogue.json"
    current = json.loads(path.read_text(encoding="utf-8"))
    built = build_products(current[:HAND_WRITTEN], SEED)
    if check:
        if built != current:
            print(f"{path} differs from a rebuild; run python -m advisor.catalogue_build")
            return 1
        print(f"{path} matches a rebuild ({len(built)} products)")
        return 0
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(built, indent=2, ensure_ascii=False))
    print(f"wrote {len(built)} products to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
