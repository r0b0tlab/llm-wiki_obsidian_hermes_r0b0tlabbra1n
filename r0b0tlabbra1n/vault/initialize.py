"""Vault initialization — create the canonical brain vault from templates."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from r0b0tlabbra1n.models import (
    MemoryTier,
    MemoryType,
    PageFrontmatter,
    PageStatus,
    PageType,
)
from r0b0tlabbra1n.paths import ensure_vault_dirs
from r0b0tlabbra1n.vault.frontmatter import write_frontmatter


def init_vault(vault_path: Path, force: bool = False) -> Path:
    """Initialize a brain vault at vault_path. Raises FileExistsError if vault exists
    and force is False."""
    if vault_path.exists() and not force:
        raise FileExistsError(f"Vault already exists at {vault_path}. Use --force to overwrite.")

    vault_path.mkdir(parents=True, exist_ok=True)
    ensure_vault_dirs(vault_path)

    now = datetime.now().isoformat()

    # START_HERE.md
    write_frontmatter(
        vault_path / "START_HERE.md",
        PageFrontmatter(
            title="START HERE",
            type=PageType.DASHBOARD,
            status=PageStatus.ACTIVE,
            tier=MemoryTier.L2_WARM,
            provenance="init",
        ),
        _START_HERE_BODY,
    )

    # SCHEMA.md
    write_frontmatter(
        vault_path / "SCHEMA.md",
        PageFrontmatter(
            title="Vault Schema",
            type=PageType.SCHEMA,
            status=PageStatus.ACTIVE,
            tier=MemoryTier.L2_WARM,
            provenance="init",
        ),
        _SCHEMA_BODY,
    )

    # index.md
    write_frontmatter(
        vault_path / "index.md",
        PageFrontmatter(
            title="Vault Index",
            type=PageType.DASHBOARD,
            status=PageStatus.ACTIVE,
            tier=MemoryTier.L2_WARM,
            provenance="init",
        ),
        _INDEX_BODY,
    )

    # log.md
    write_frontmatter(
        vault_path / "log.md",
        PageFrontmatter(
            title="Vault Log",
            type=PageType.DASHBOARD,
            status=PageStatus.ACTIVE,
            tier=MemoryTier.L2_WARM,
            provenance="init",
        ),
        _LOG_BODY,
    )

    # Agent pages
    _write_agent_pages(vault_path)

    # Dashboards
    _write_dashboards(vault_path)

    # Metadata
    _write_meta(vault_path, now)

    return vault_path


def _write_agent_pages(vault_path: Path):
    """Create _agent/ section pages."""
    base = vault_path / "_agent"

    pages = {
        "START_HERE.md": (
            PageFrontmatter(title="Agent START HERE", type=PageType.DASHBOARD,
                            tier=MemoryTier.L2_WARM, status=PageStatus.ACTIVE, provenance="init"),
            _AGENT_START_BODY,
        ),
        "operating-rules.md": (
            PageFrontmatter(title="Operating Rules", type=PageType.PROCEDURE,
                            memory_type=MemoryType.PROCEDURAL, tier=MemoryTier.L2_WARM,
                            status=PageStatus.ACTIVE, provenance="init"),
            "Operating rules are automatically promoted from patterns observed across multiple "
            "sessions. "
            "No rule here should exist without at least 3 corroborating sessions.\n",
        ),
        "memory-policy.md": (
            PageFrontmatter(title="Memory Policy", type=PageType.PROCEDURE,
                            memory_type=MemoryType.SEMANTIC, tier=MemoryTier.L2_WARM,
                            status=PageStatus.ACTIVE, provenance="init"),
            "# Memory Policy\n\n"
            "## Tiers\n"
            "- **L1 HOT**: Hermes built-in MEMORY.md (<= 2,200 chars) — compact pointers only\n"
            "- **L2 WARM**: dashboards, project status, operating rules — auto-loaded\n"
            "- **L3 COLD**: session summaries, detailed pages — retrieved on demand\n"
            "- **L4 ARCHIVE**: raw captures, superseded pages — never auto-loaded\n\n"
            "## Promotion Rules\n"
            "- A fact observed in 3+ sessions may be promoted to L2 WARM\n"
            "- A fact used in 5+ retrievals may be promoted to L1 HOT as a compact pointer\n"
            "- Any page stale > 30 days is demoted to L3 COLD\n"
            "- Any page stale > 90 days is demoted to L4 ARCHIVE\n\n"
            "## Secrets Policy\n"
            "- **NEVER** store secrets, API keys, tokens, or passwords in the vault\n"
            "- Store key names and config paths only\n"
            "- The secret scanner runs on every write\n",
        ),
    }

    for filename, (fm, body) in pages.items():
        write_frontmatter(base / filename, fm, body)

    # Semantic pages
    semantic = base / "semantic"
    semantic_pages = [
        ("project-status.md", "Project Status", "Current status of all known projects."),
        (
            "user-preferences.md",
            "User Preferences",
            "User communication style, tool preferences, and pet peeves.",
        ),
        ("environment-facts.md", "Environment Facts", "System, OS, hardware, and network facts."),
        ("tool-quirks.md", "Tool Quirks", "Known quirks, pitfalls, and workarounds for tools."),
        ("failure-patterns.md", "Failure Patterns", "Recurring failure patterns across sessions."),
        ("success-patterns.md", "Success Patterns", "Recurring success patterns across sessions."),
        (
            "decision-principles.md",
            "Decision Principles",
            "Principles derived from past decisions.",
        ),
        (
            "open-loops.md",
            "Open Loops",
            "Unresolved questions, incomplete tasks, pending decisions.",
        ),
    ]
    for filename, title, description in semantic_pages:
        write_frontmatter(
            semantic / filename,
            PageFrontmatter(
                title=title, type=PageType.CONCEPT, memory_type=MemoryType.SEMANTIC,
                tier=MemoryTier.L3_COLD, status=PageStatus.ACTIVE, provenance="init",
            ),
            f"# {title}\n\n{description}\n",
        )


def _write_dashboards(vault_path: Path):
    """Create dashboard pages."""
    base = vault_path / "dashboards"
    dashboards = [
        ("agent-dashboard.md", "Agent Dashboard",
         "Overview of agent state: memory health, recent sessions, open loops, stale items."),
        ("project-dashboard.md", "Project Dashboard",
         "Status of all tracked projects with links to detailed pages."),
        ("stale-items.md", "Stale Items",
         "Items that have not been updated within their freshness window."),
        ("open-questions.md", "Open Questions",
         "Questions that have been asked but not resolved."),
        ("memory-health.md", "Memory Health",
         "Metrics: memory item count by tier/type, storage usage, retrieval stats."),
        ("retrieval-quality.md", "Retrieval Quality",
         "Evaluation results, retrieval benchmarks, recall/precision metrics."),
    ]
    for filename, title, description in dashboards:
        write_frontmatter(
            base / filename,
            PageFrontmatter(
                title=title, type=PageType.DASHBOARD, tier=MemoryTier.L2_WARM,
                status=PageStatus.ACTIVE, provenance="init",
            ),
            f"# {title}\n\n{description}\n",
        )


def _write_meta(vault_path: Path, now: str):
    """Write metadata files."""
    meta = vault_path / "_meta"
    meta.mkdir(parents=True, exist_ok=True)

    # Creation manifest
    import json
    (meta / "vault-state.json").write_text(json.dumps({
        "created": now,
        "version": "0.1.0",
        "schema_version": 1,
    }, indent=2))

    # Initial ingestion manifest header
    (meta / "ingestion-manifest.jsonl").write_text("")

    # Source hashes placeholder
    (meta / "source-hashes.json").write_text(json.dumps({}))


# Template bodies
_START_HERE_BODY = """\
# Welcome to your Brain Vault

This is your LLM-Wiki + Obsidian agent memory system.

## Quick Navigation

- [[SCHEMA]] — vault structure and conventions
- [[index]] — full page index
- [[log]] — chronological log of all changes
- [[_agent/START_HERE]] — agent-specific instructions
- [[dashboards/agent-dashboard]] — memory health dashboard

## How Agents Use This

1. Read [[SCHEMA]] to understand the vault structure
2. Read [[_agent/operating-rules]] for conventions
3. Read project pages in [[projects/]] for context
4. Use `brain search` or `brain retrieve` for on-demand recall
5. Write updates back to the vault with provenance

## How Humans Use This

Open this folder in [Obsidian](https://obsidian.md) to browse, edit, and review.
Everything is human-readable Markdown with structured frontmatter.
"""

_SCHEMA_BODY = """\
# Vault Schema

## Directory Structure

- `_agent/` — agent instructions, operating rules, semantic/episodic memory
- `dashboards/` — auto-generated dashboards (health, stale items, open questions)
- `projects/` — per-project pages with overview, status, decisions, pitfalls
- `sessions/` — session summaries, transcript index, lineage
- `entities/` — people, organizations, projects, tools
- `concepts/` — technical concepts, mental models, comparisons
- `procedures/` — workflows, playbooks, how-tos
- `skills/` — Hermes skill catalog and improvement candidates
- `raw/` — immutable source captures (articles, papers, sessions)
- `_meta/` — indexes, manifests, hashes, config

## Page Types

| Type | Template | Description |
|------|----------|-------------|
| project | project-overview | Project with status, decisions, pitfalls |
| session | session-summary | Summary of a Hermes session |
| decision | decision | Key decision with context and rationale |
| failure | failure | Failure analysis with root cause |
| success | success | Success pattern with what worked |
| entity | — | Person, org, tool, project reference |
| concept | — | Technical concept or mental model |
| procedure | — | Step-by-step workflow |
| dashboard | — | Auto-generated status page |
| schema | — | This page or other schema docs |

## Frontmatter

Every page requires:
- `title` (required)
- `type` (one of the above)
- `status` (active/draft/stale/archived/superseded)
- `tier` (hot/warm/cold/archive)
- `memory_type` (working/episodic/semantic/procedural)
- `confidence` (high/medium/low)
- `provenance` (how the page was created)
"""

_INDEX_BODY = """\
# Vault Index

This index is rebuilt by `brain build-index`. Last rebuild: pending.

## By Type

- Dashboards: see [[dashboards/]]
- Projects: see [[projects/]]
- Sessions: see [[sessions/]]
- Entities: see [[entities/]]
- Concepts: see [[concepts/]]
- Procedures: see [[procedures/]]

## By Tier

- L2 WARM: [[dashboards/agent-dashboard]], [[_agent/START_HERE]], [[_agent/operating-rules]]
- L3 COLD: [[projects/]], [[sessions/summaries/]], [[concepts/]]
"""

_LOG_BODY = """\
# Vault Log

Chronological log of all automated changes to the vault.

| Timestamp | Action | Page | Provenance |
|-----------|--------|------|------------|
| init | vault_created | [[START_HERE]] | brain init |
"""

_AGENT_START_BODY = """\
# Agent Instructions

## When You Start

1. Read [[../SCHEMA]] for vault structure
2. Read [[_agent/operating-rules]] for conventions
3. Read [[_agent/semantic/project-status]] for current project state
4. Read [[_agent/semantic/user-preferences]] for user style
5. Read [[_agent/semantic/environment-facts]] for system context

## During Work

- Save durable facts to [[_agent/semantic/]] pages
- Log decisions to [[_agent/episodic/decisions/]]
- Log failures to [[_agent/episodic/failures/]]
- Log successes to [[_agent/episodic/successes/]]
- Keep L1 HOT memory compact (~2KB) — use pointers to warm pages

## After Work

- Update [[_agent/semantic/project-status]]
- Update [[_agent/semantic/open-loops]]
- Check [[dashboards/stale-items]]
"""
