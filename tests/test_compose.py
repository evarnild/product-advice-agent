"""Guard for infra/langfuse/docker-compose.yml: plain text, no YAML, no Docker.

Keeps the exact image pins, the localhost-only ports and the "no AI gateway"
choice in place (intent 4). A reformat that breaks a pattern means updating
this test, not loosening the pinning.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

COMPOSE = Path(__file__).resolve().parent.parent / "infra" / "langfuse" / "docker-compose.yml"

LOW_MEMORY = COMPOSE.parent / "clickhouse" / "low-memory.xml"
LOG_TABLES = (
    "trace_log text_log metric_log asynchronous_metric_log part_log "
    "processors_profile_log opentelemetry_span_log query_thread_log query_views_log"
).split()

SERVICES = {"langfuse-worker", "langfuse-web", "clickhouse", "minio", "redis", "postgres"}
MIN_LANGFUSE = (4, 59, 0)

DIGEST = re.compile(r"@sha256:[0-9a-f]{64}$")
TAG = re.compile(r":(\d+\.\d+(?:\.\d+)*)$")


def _lines() -> list[str]:
    return COMPOSE.read_text(encoding="utf-8").splitlines()


def _images() -> list[str]:
    found = []
    for line in _lines():
        m = re.match(r"^\s+image:\s*(\S+)\s*(?:#.*)?$", line)
        if m:
            found.append(m.group(1))
    return found


def _services() -> list[str]:
    names = []
    in_services = False
    for line in _lines():
        if re.match(r"^\S", line):
            in_services = line.startswith("services:")
            continue
        m = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
        if in_services and m:
            names.append(m.group(1))
    return names


def _ports() -> list[str]:
    items = []
    lines = _lines()
    for i, line in enumerate(lines):
        m = re.match(r"^(\s+)ports:\s*$", line)
        if not m:
            continue
        for nxt in lines[i + 1 :]:
            item = re.match(r"^\s+- (.*\S)\s*$", nxt)
            if not item or len(nxt) - len(nxt.lstrip()) <= len(m.group(1)):
                if nxt.strip() and not nxt.lstrip().startswith("#"):
                    break
                continue
            items.append(item.group(1).strip("\"'"))
    return items


def _tag(image: str) -> tuple[int, ...] | None:
    m = TAG.search(image)
    return tuple(int(p) for p in m.group(1).split(".")) if m else None


def test_collects_what_it_guards() -> None:
    assert len(_images()) == 6
    assert len(_ports()) == 8


def test_every_image_is_exact() -> None:
    for image in _images():
        assert DIGEST.search(image) or _tag(image) is not None, f"not exact: {image}"
        assert not image.endswith(":latest"), image


def test_langfuse_web_and_worker_share_a_v4_tag() -> None:
    tags = {}
    for image in _images():
        m = re.search(r"/langfuse/(langfuse|langfuse-worker):(.+)$", image)
        if m:
            tags[m.group(1)] = m.group(2)
    assert set(tags) == {"langfuse", "langfuse-worker"}
    assert tags["langfuse"] == tags["langfuse-worker"]
    version = _tag(f"x:{tags['langfuse']}")
    assert version is not None and len(version) == 3
    assert version[0] == 4, f"Langfuse must be on major 4, got {version}"
    assert version >= MIN_LANGFUSE


def test_ports_are_localhost_only() -> None:
    for port in _ports():
        assert port.startswith("127.0.0.1:"), port


def test_exactly_the_six_services_and_no_gateway() -> None:
    names = _services()
    assert "langfuse-ai-gateway" not in names
    assert sorted(names) == sorted(SERVICES)


def test_clickhouse_is_capped_and_mounts_the_low_memory_config() -> None:
    lines = _lines()
    start = lines.index("  clickhouse:")
    block = lines[start + 1 : lines.index("  minio:")]
    assert "    mem_limit: 1500m" in block
    mount = "      - ./clickhouse/low-memory.xml:/etc/clickhouse-server/config.d/low-memory.xml:ro"
    assert mount in block


def test_low_memory_config_trims_logs_and_caps_memory() -> None:
    root = ET.parse(LOW_MEMORY).getroot()
    for table in LOG_TABLES:
        node = root.find(table)
        assert node is not None and node.get("remove") == "1", table
    assert root.find("query_log") is None
    memory = root.find("max_server_memory_usage")
    assert memory is not None and memory.text == "1073741824"
    assert root.find("background_pool_size") is None  # owner's decision (21 F1)


def test_langfuse_web_and_worker_are_capped_per_service() -> None:
    lines = _lines()
    worker = lines[lines.index("  langfuse-worker:") + 1 : lines.index("  langfuse-web:")]
    web = lines[lines.index("  langfuse-web:") + 1 : lines.index("  clickhouse:")]
    shared = lines[lines.index("x-langfuse-env: &langfuse-env") + 1 : lines.index("services:")]
    for block in (worker, web):
        assert "    mem_limit: 1g" in block
        assert "      NODE_OPTIONS: --max-old-space-size=512" in block
    assert not any("NODE_OPTIONS" in line for line in shared)
