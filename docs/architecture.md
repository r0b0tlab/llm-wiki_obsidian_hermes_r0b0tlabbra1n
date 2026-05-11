# LLM Wiki Brain — Architecture

## Design Principles

1. Markdown is source of truth — indexes are derived and rebuildable.
2. Raw sources are immutable evidence and treated as untrusted input.
3. Always-loaded memory stays tiny; retrieval is explicit and budgeted.
4. Automation is idempotent and safe to run from cron.
5. Humans can browse and correct everything in Obsidian.
6. Secrets never enter the vault through supported write paths.
7. Memory quality is evaluated, not vibe-checked.

## Implemented Layers

```text
Layer 4: Agent integration
├── Hermes skill: hermes/skills/llm-wiki-brain
├── Runnable cron scripts: hermes/cron_scripts/heartbeat.py, weekly_audit.py
├── Minimal MCP/JSON facade: mcp_server/brain_mcp.py
└── CLI: brain init/lint/build-index/search/ingest/eval/graph/drift-check

Layer 3: Rebuildable indexes
├── SQLite FTS5 standalone table with BM25 ranking
├── Weighted retrieval: tier + confidence + status + recency
├── Link graph/backlinks JSON
├── Source-hash manifest and drift checker
└── Retrieval eval harness with gold queries

Layer 2: Compiled Markdown wiki
├── Structured YAML frontmatter
├── L1/L2/L3/L4 tier labels
├── episodic/semantic/procedural memory types
└── Obsidian wikilinks

Layer 1: Raw evidence
├── Read-only Hermes state.db ingest
├── Optional raw transcript export under raw/
└── raw evidence marked untrusted
```

## Data Flow

```text
Hermes state.db --mode=ro--> brain ingest-sessions
                              ↓
                       session summaries
                              ↓
Markdown vault -----> brain build-index -----> FTS5 + hashes + graph
                              ↓
                       brain search/eval/context
```

## Retrieval

`brain search` uses FTS5 BM25 rank and then applies deterministic boosts:

- warm/hot tier boost
- confidence boost
- active/stale status adjustment
- recent update boost

`brain search --context` returns a bounded `<memory-context>` packet for agent prompts.

## Drift and Graph

`brain build-index` writes `_meta/source-hashes.json`, `_meta/link-graph.json`, and `_meta/backlinks.json`. `brain drift-check` compares the current vault to the last manifest.

## Security

- Secret scanner blocks supported tokens and `.env`-style secret assignments.
- `append_to_page` and `safe_write_page` scan before writes.
- Lint scans existing Markdown for secrets.
- Raw transcripts are optional and scanned before export.
- Wikilink traversal outside the vault is not resolved.

## Roadmap

- Optional vector embeddings for semantic search.
- Richer temporal graph beyond local wikilink graph.
- LLM-assisted extraction as an optional backend, not a required dependency.
