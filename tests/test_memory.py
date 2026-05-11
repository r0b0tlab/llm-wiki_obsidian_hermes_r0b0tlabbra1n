"""Tests for memory extraction and promotion policies."""

from r0b0tlabbra1n.memory.extract import (
    archive_item,
    demote_to_cold,
    extract_facts,
    promote_to_warm,
)
from r0b0tlabbra1n.models import Confidence, MemoryItem, MemoryTier, MemoryType


def test_extract_facts():
    content = """
    Fix the bug in the deploy script.
    User prefers concise responses.
    Always use pytest for testing.
    The error in the benchmark results was caused by GPU OOM.
    """
    items = extract_facts(content, source="test-session")
    assert len(items) > 0
    # Should find some fact types
    types = {i.memory_type for i in items}
    assert MemoryType.PROCEDURAL in types or MemoryType.SEMANTIC in types


def test_extract_facts_empty():
    items = extract_facts("")
    assert items == []


def test_promote_to_warm():
    item = MemoryItem(
        content="Always use pytest",
        memory_type=MemoryType.PROCEDURAL,
        tier=MemoryTier.L3_COLD,
        confidence=Confidence.MEDIUM,
    )

    # Not enough occurrences
    result = promote_to_warm(item, occurrence_count=1)
    assert result is None

    # 2 occurrences bumps confidence
    item2 = MemoryItem(
        content="Always use pytest",
        memory_type=MemoryType.PROCEDURAL,
        tier=MemoryTier.L3_COLD,
        confidence=Confidence.MEDIUM,
    )
    result = promote_to_warm(item2, occurrence_count=2)
    assert result is not None
    assert result.confidence == Confidence.MEDIUM

    # 3+ occurrences promotes
    item3 = MemoryItem(
        content="Always use pytest",
        memory_type=MemoryType.PROCEDURAL,
        tier=MemoryTier.L3_COLD,
        confidence=Confidence.MEDIUM,
    )
    result = promote_to_warm(item3, occurrence_count=3)
    assert result is not None
    assert result.tier == MemoryTier.L2_WARM
    assert result.confidence == Confidence.HIGH

    # Low confidence items don't promote
    item4 = MemoryItem(
        content="Always use pytest",
        memory_type=MemoryType.PROCEDURAL,
        tier=MemoryTier.L3_COLD,
        confidence=Confidence.LOW,
    )
    result = promote_to_warm(item4, occurrence_count=3)
    assert result is None


def test_demote_to_cold():
    item = MemoryItem(
        content="Outdated fact",
        memory_type=MemoryType.SEMANTIC,
        tier=MemoryTier.L2_WARM,
        confidence=Confidence.HIGH,
    )

    # Recent enough
    result = demote_to_cold(item, days_since_update=10)
    assert result is None

    # Stale
    result = demote_to_cold(item, days_since_update=31)
    assert result is not None
    assert result.tier == MemoryTier.L3_COLD


def test_archive_item():
    item = MemoryItem(
        content="Very old fact",
        memory_type=MemoryType.SEMANTIC,
        tier=MemoryTier.L3_COLD,
    )

    # Not old enough
    result = archive_item(item, days_since_update=60)
    assert result is None

    # Old enough
    result = archive_item(item, days_since_update=91)
    assert result is not None
    assert result.tier == MemoryTier.L4_ARCHIVE
