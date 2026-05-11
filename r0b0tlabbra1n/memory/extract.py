"""Memory extraction and promotion — identify durable facts for promotion between tiers."""

from __future__ import annotations

from r0b0tlabbra1n.models import Confidence, MemoryItem, MemoryTier, MemoryType


def extract_facts(
    content: str,
    source: str = "",
    min_confidence: Confidence = Confidence.MEDIUM,
) -> list[MemoryItem]:
    """Extract potential memory items from content.

    This is a lightweight heuristic extractor. For production use,
    this would call an LLM for semantic extraction.

    Returns list of MemoryItem candidates.
    """
    items = []

    # Simple keyword-based extraction as placeholder
    # In production, this calls an LLM with structured output
    indicators = {
        "error": MemoryType.EPISODIC,
        "fix": MemoryType.PROCEDURAL,
        "prefers": MemoryType.SEMANTIC,
        "always": MemoryType.PROCEDURAL,
        "never": MemoryType.PROCEDURAL,
        "should": MemoryType.PROCEDURAL,
        "must": MemoryType.PROCEDURAL,
        "command": MemoryType.PROCEDURAL,
        "config": MemoryType.SEMANTIC,
        "version": MemoryType.SEMANTIC,
        "deploy": MemoryType.PROCEDURAL,
        "benchmark": MemoryType.EPISODIC,
    }

    for line in content.split("\n"):
        line = line.strip()
        if not line or len(line) < 10:
            continue

        for keyword, mem_type in indicators.items():
            if keyword in line.lower():
                items.append(MemoryItem(
                    content=line[:200],
                    memory_type=mem_type,
                    tier=MemoryTier.L3_COLD,
                    confidence=Confidence.LOW,
                    source_page=source,
                    tags=[keyword],
                ))
                break

    return items


def promote_to_warm(item: MemoryItem, occurrence_count: int) -> MemoryItem | None:
    """Check if an item qualifies for promotion to L2 WARM tier.

    Requires at least 3 corroborating occurrences.
    Low-confidence items require higher threshold (5 occurrences).
    """
    if item.confidence == Confidence.LOW:
        if occurrence_count >= 5:
            item.confidence = Confidence.MEDIUM
            return item
        return None

    if occurrence_count >= 3:
        item.tier = MemoryTier.L2_WARM
        item.confidence = Confidence.HIGH
        return item
    elif occurrence_count >= 2:
        item.confidence = Confidence.MEDIUM
        return item
    return None


def demote_to_cold(item: MemoryItem, days_since_update: int) -> MemoryItem | None:
    """Check if an item should be demoted from L2 WARM to L3 COLD."""
    if days_since_update > 30 and item.tier == MemoryTier.L2_WARM:
        item.tier = MemoryTier.L3_COLD
        item.confidence = Confidence.MEDIUM
        return item
    return None


def archive_item(item: MemoryItem, days_since_update: int) -> MemoryItem | None:
    """Check if an item should be archived to L4 ARCHIVE."""
    if days_since_update > 90 and item.tier in (MemoryTier.L3_COLD, MemoryTier.L2_WARM):
        item.tier = MemoryTier.L4_ARCHIVE
        return item
    return None
