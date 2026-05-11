"""Memory extraction and promotion — identify durable facts for promotion between tiers."""

from __future__ import annotations

import re

from r0b0tlabbra1n.models import Confidence, MemoryItem, MemoryTier, MemoryType

_PATTERNS: list[tuple[re.Pattern[str], MemoryType, Confidence, str]] = [
    (
        re.compile(r"^(?:[-*]\s*)?(?:Decision|Chose|We decided):\s*(.+)", re.I),
        MemoryType.SEMANTIC,
        Confidence.HIGH,
        "decision",
    ),
    (
        re.compile(r"^(?:[-*]\s*)?(?:Failure|Error|Bug):\s*(.+)", re.I),
        MemoryType.EPISODIC,
        Confidence.HIGH,
        "failure",
    ),
    (
        re.compile(r"^(?:[-*]\s*)?(?:Fix|Solution|Workaround):\s*(.+)", re.I),
        MemoryType.PROCEDURAL,
        Confidence.HIGH,
        "fix",
    ),
    (
        re.compile(r"^(?:[-*]\s*)?(?:Command):\s*(`?[^`].+`?)", re.I),
        MemoryType.PROCEDURAL,
        Confidence.MEDIUM,
        "command",
    ),
    (re.compile(r"(User prefers .+)", re.I), MemoryType.SEMANTIC, Confidence.HIGH, "preference"),
    (
        re.compile(r"^(?:[-*]\s*)?(?:Environment|Config):\s*(.+)", re.I),
        MemoryType.SEMANTIC,
        Confidence.MEDIUM,
        "environment",
    ),
]


def extract_facts(
    content: str,
    source: str = "",
    min_confidence: Confidence = Confidence.MEDIUM,
) -> list[MemoryItem]:
    """Extract potential memory items from structured Markdown/session text."""
    threshold = {Confidence.LOW: 0, Confidence.MEDIUM: 1, Confidence.HIGH: 2}[min_confidence]
    items: list[MemoryItem] = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if len(line) < 8:
            continue
        for pattern, mem_type, confidence, tag in _PATTERNS:
            match = pattern.search(line)
            if not match:
                continue
            if {Confidence.LOW: 0, Confidence.MEDIUM: 1, Confidence.HIGH: 2}[
                confidence
            ] < threshold:
                continue
            text = match.group(1).strip() if match.groups() else line
            items.append(
                MemoryItem(
                    content=text[:300],
                    memory_type=mem_type,
                    tier=MemoryTier.L3_COLD,
                    confidence=confidence,
                    source_page=source,
                    tags=[tag],
                )
            )
            break
    return items


def promote_to_warm(item: MemoryItem, occurrence_count: int) -> MemoryItem | None:
    if item.confidence == Confidence.LOW:
        if occurrence_count >= 5:
            item.confidence = Confidence.MEDIUM
            return item
        return None
    if occurrence_count >= 3:
        item.tier = MemoryTier.L2_WARM
        item.confidence = Confidence.HIGH
        return item
    if occurrence_count >= 2:
        item.confidence = Confidence.MEDIUM
        return item
    return None


def demote_to_cold(item: MemoryItem, days_since_update: int) -> MemoryItem | None:
    if days_since_update > 30 and item.tier == MemoryTier.L2_WARM:
        item.tier = MemoryTier.L3_COLD
        item.confidence = Confidence.MEDIUM
        return item
    return None


def archive_item(item: MemoryItem, days_since_update: int) -> MemoryItem | None:
    if days_since_update > 90 and item.tier in (MemoryTier.L3_COLD, MemoryTier.L2_WARM):
        item.tier = MemoryTier.L4_ARCHIVE
        return item
    return None
