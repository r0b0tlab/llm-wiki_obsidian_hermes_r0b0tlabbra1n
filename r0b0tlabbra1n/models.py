"""Data models for r0b0tlabbra1n memory system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PageType(str, Enum):
    PROJECT = "project"
    SESSION = "session"
    DECISION = "decision"
    FAILURE = "failure"
    SUCCESS = "success"
    ENTITY = "entity"
    CONCEPT = "concept"
    PROCEDURE = "procedure"
    QUERY = "query"
    DASHBOARD = "dashboard"
    SCHEMA = "schema"
    RAW = "raw"


class PageStatus(str, Enum):
    ACTIVE = "active"
    DRAFT = "draft"
    STALE = "stale"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


class MemoryTier(str, Enum):
    L1_HOT = "hot"       # Hermes built-in MEMORY.md (~2KB)
    L2_WARM = "warm"     # dashboards, project status
    L3_COLD = "cold"     # session summaries, detailed pages
    L4_ARCHIVE = "archive"  # immutable raw, old logs


class MemoryType(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PageFrontmatter:
    """Structured frontmatter for a vault page."""
    title: str
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    updated: str = field(default_factory=lambda: datetime.now().isoformat())
    type: PageType | None = None
    status: PageStatus = PageStatus.DRAFT
    memory_type: MemoryType | None = None
    tier: MemoryTier | None = None
    confidence: Confidence | None = None
    scope: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    superseded_by: list[str] = field(default_factory=list)
    review_status: str = "unreviewed"
    provenance: str = ""       # How this page was created (manual/agent/cron/ingest)
    source_hash: str = ""      # SHA of raw source if derived
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = {
            "title": self.title,
            "created": self.created,
            "updated": self.updated,
        }
        if self.type:
            d["type"] = self.type.value
        if self.status != PageStatus.DRAFT:
            d["status"] = self.status.value
        if self.memory_type:
            d["memory_type"] = self.memory_type.value
        if self.tier:
            d["tier"] = self.tier.value
        if self.confidence:
            d["confidence"] = self.confidence.value
        if self.scope:
            d["scope"] = self.scope
        if self.tags:
            d["tags"] = self.tags
        if self.sources:
            d["sources"] = self.sources
        if self.superseded_by:
            d["superseded_by"] = self.superseded_by
        if self.review_status:
            d["review_status"] = self.review_status
        if self.provenance:
            d["provenance"] = self.provenance
        if self.source_hash:
            d["source_hash"] = self.source_hash
        if self.extra:
            d.update(self.extra)
        return d


@dataclass
class MemoryItem:
    """A discrete memory item for promotion/demotion between tiers."""
    content: str
    memory_type: MemoryType
    tier: MemoryTier
    confidence: Confidence = Confidence.MEDIUM
    source_page: str = ""
    scope: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RetrievalResult:
    """A result from a memory retrieval query."""
    path: str
    snippet: str
    score: float = 0.0
    page_type: PageType | None = None
    memory_type: MemoryType | None = None
    tier: MemoryTier | None = None
    confidence: Confidence | None = None


@dataclass
class ContextPacket:
    """A bounded context packet for injection into an agent prompt."""
    results: list[RetrievalResult]
    token_budget: int
    tokens_used: int
    query: str = ""
