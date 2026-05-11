---
name: llm-wiki-brain
description: Filesystem-first LLM-Wiki + Obsidian agent memory system. Use when the agent needs to read, write, search, or maintain its persistent knowledge base. Provides brain search, lint, ingest-sessions, and build-index commands via the r0b0tlabbra1n package.
version: 0.1.0
metadata:
  author: "@mr-r0b0t on X — r0b0tlab"
  hermes:
    tags: [memory, knowledge, obsidian, wiki, brain]
    category: memory
    min_hermes_version: "0.8.0"
---

# LLM Wiki Brain — Hermes Agent Memory System

## When to Use

Load this skill when the agent needs to:
- Search its persistent knowledge base for facts, procedures, or project context
- Record new durable information (decisions, failures, successes, project status)
- Check vault health (lint for broken links, stale items, secrets)
- Ingest Hermes sessions into the brain vault
- Navigate the vault structure

## Requirements

- Python 3.11+
- `r0b0tlabbra1n` package installed (`pip install r0b0tlabbra1n` or `pip install -e .` from the repo)
- Brain vault initialized (`brain init --vault PATH`)
- Hermes `state.db` accessible for session ingest (read-only)

## Quickstart

```bash
# Install
pip install r0b0tlabbra1n

# Initialize a brain
brain init --vault ~/my-brain

# Build the search index
brain build-index --vault ~/my-brain

# Search
brain search "how to deploy vLLM" --vault ~/my-brain
```

## Core Workflows

### 1. Orient in a new session

When starting work, an agent should:
1. `brain search "project status" --vault ~/my-brain` — get current state
2. Read `~/my-brain/START_HERE.md` and `~/my-brain/_agent/START_HERE.md`
3. Read `~/my-brain/_agent/semantic/project-status.md` for project context

### 2. Record a decision

```bash
# Create a decision page
python -c "
from r0b0tlabbra1n.vault.write_ops import safe_write_page
from r0b0tlabbra1n.models import PageFrontmatter, PageType, PageStatus, MemoryTier
from pathlib import Path

vault = Path.home() / 'my-brain'
page = vault / '_agent' / 'episodic' / 'decisions' / 'decision-slug.md'
fm = PageFrontmatter(
    title='Decision: Something Decided',
    type=PageType.DECISION,
    status=PageStatus.ACTIVE,
    tier=MemoryTier.L3_COLD,
    provenance='agent',
)
body = '''# Decision: Something Decided

**Context:** Why this decision was needed.

**Options considered:**
1. Option A
2. Option B

**Decision:** We chose X because...

**Impact:** What this affects going forward.
'''
safe_write_page(page, fm, body, provenance='agent')
print(f'Decision saved: {page}')
"
```

### 3. Search before acting

Before making changes, search for relevant past context:

```bash
brain search "project topic" --vault ~/my-brain --budget 2000
```

### 4. Lint the vault

Regularly check vault health:

```bash
brain lint --vault ~/my-brain
```

Expected output: zero ERRORs, zero WARNINGs. INFO (orphans) is fine.

### 5. Ingest new sessions

After significant work, ingest the session:

```bash
brain ingest-sessions --hermes-home ~/.hermes --vault ~/my-brain
```

Run `brain build-index --vault ~/my-brain` after ingestion.

## Vault Structure

```
~/my-brain/
├── START_HERE.md          # Entry point
├── SCHEMA.md              # Structure and conventions
├── index.md               # Page index
├── log.md                 # Chronological activity log
├── _agent/                # Agent instructions and memories
│   ├── START_HERE.md
│   ├── operating-rules.md
│   ├── semantic/          # Durable facts
│   └── episodic/          # Session/event records
├── dashboards/            # Health and status dashboards
├── projects/              # Per-project pages
├── sessions/              # Session summaries
├── entities/              # People, orgs, tools
├── concepts/              # Technical concepts
└── _meta/                 # Indexes, manifests, config
```

## Memory Tiers

- **L1 HOT**: Hermes built-in `MEMORY.md` (~2KB) — compact pointers only
- **L2 WARM**: Dashboards, project status, operating rules — auto-loaded
- **L3 COLD**: Session summaries, detailed pages — retrieved on demand
- **L4 ARCHIVE**: Raw captures, superseded pages — never auto-loaded

## Promotion Rules

- Fact observed 3+ times → promote to L2 WARM
- Fact used 5+ retrievals → promote to L1 HOT as compact pointer
- Page stale > 30 days → demote to L3 COLD
- Page stale > 90 days → demote to L4 ARCHIVE

## Secrets Policy

**NEVER** store secrets, API keys, tokens, or passwords in the vault.
Store key names and config paths only. The secret scanner runs on every write.

## Common Patterns

**Find what you need:**
```
brain search "keyword" --vault ~/my-brain
```

**Check vault health:**
```
brain lint --vault ~/my-brain
```

**Update the index after changes:**
```
brain build-index --vault ~/my-brain
```

**Bring sessions into the brain:**
```
brain ingest-sessions --vault ~/my-brain
brain build-index --vault ~/my-brain
```

## Pitfalls

- Always run `brain build-index` after adding new pages or the search won't find them
- Session ingest is idempotent — safe to run repeatedly
- Use `brain lint` before committing changes to the vault
- The vault is filesystem-first: you can always read/write .md files directly
- Orphan pages are INFO-level only — not errors
- Secrets in the vault are hard-blocked by the secret scanner

## Verification

After setup, verify:
```bash
brain init --vault /tmp/test-brain
brain lint --vault /tmp/test-brain
# Should show only INFO-level orphan messages, no ERRORs or WARNINGs
```
