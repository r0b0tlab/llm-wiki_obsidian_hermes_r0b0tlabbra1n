# LLM Wiki Brain — Architecture

## Design Principles

1. **Markdown is source of truth** — indexes are derived and rebuildable
2. **Raw sources are immutable** — every synthesized claim has provenance
3. **Always-loaded memory stays tiny** — retrieval is explicit and budgeted
4. **Automation must be idempotent** — safe to run via cron
5. **Humans can browse and correct everything in Obsidian**
6. **Secrets never enter the vault** — hard-blocked by scanner

## System Layers

```
Layer 4: Hermes Integration
├── Built-in MEMORY.md/USER.md (L1 HOT pointers)
├── session_search (FTS5 recall)
├── Skill: llm-wiki-brain (procedural workflows)
├── Memory Provider Plugin (future: prefetch/hooks)
├── Context Engine Plugin (future: lossless compression)
├── Cron Jobs (heartbeat, audit, session collector)
└── MCP Server (future: agent-agnostic access)

Layer 3: Index Layer
├── SQLite FTS5 (full-text search)
├── Link graph (wikilinks → backlinks)
├── Embeddings (future: optional vector search)
└── Source hashes (drift detection)

Layer 2: Compiled Wiki Layer
├── Vault pages with structured frontmatter
├── Tier: hot → warm → cold → archive
├── Memory type: episodic → semantic → procedural
└── Wikilinks between pages

Layer 1: Raw Evidence Layer
├── Immutable source captures
├── Hermes session transcripts (state.db)
├── Project docs, web captures, papers
└── Source manifests and hashes
```

## Data Flow

```
Hermes Session → state.db
                     ↓
              brain ingest-sessions
                     ↓
              Session Summary Pages (L3 COLD)
                     ↓
              brain build-index
                     ↓
              FTS5 Search Index
                     ↓
              brain search → Context Packet (token-budgeted)

Cron Heartbeat → brain lint → brain build-index → dashboard update
Cron Audit → check staleness → promote/demote tiers → report
```

## Memory Tier Lifecycle

```
Created (L3 COLD)
  → 3+ corroborations → L2 WARM
  → 5+ retrievals → L1 HOT (compact pointer)
  → Stale 30+ days → L3 COLD
  → Stale 90+ days → L4 ARCHIVE
```

## Security Model

- **Secret scanner**: runs on every `safe_write_page()` call
- **Patterns detected**: HF tokens, OpenAI keys, GitHub tokens, JWT, private keys, env secrets
- **Prompt injection guard**: raw sources treated as untrusted; compiled pages state facts, not commands
- **Write controls**: raw files immutable; compiled pages atomic; every write logged
- **Read-only session ingest**: `state.db` opened with `mode=ro`; never writes to source DB
