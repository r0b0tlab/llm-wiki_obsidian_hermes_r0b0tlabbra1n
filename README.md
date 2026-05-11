# llm-wiki_obsidian_hermes_r0b0tlabbra1n

> The best filesystem-first LLM-Wiki + Obsidian + Hermes Agent memory system.
> Markdown is source of truth. Indexes are rebuildable acceleration layers.
> Built for Hermes, portable to any agent.

**Credit:** @mr-r0b0t on X — r0b0tlab

---

## What This Is

A rigorous, reusable, first-principles agent memory system. Inspired by:

- **Karpathy's LLM Wiki** — knowledge as a maintained, compounding artifact
- **GBrain** (garrytan/gbrain) — Markdown source of truth + database retrieval
- **MemGPT/Letta** — OS-tier memory management (hot/warm/cold/archive)
- **Zep/Graphiti** — temporal knowledge graphs with provenance

## Why Markdown/Obsidian Is Source of Truth

- Human-auditable: you can read, edit, and correct everything in Obsidian
- Agent-editable: structured frontmatter + wikilinks are deterministic
- Git-friendly: diffs, history, blame, rollback
- Index-independent: all indexes can be rebuilt from .md files alone
- Portable: no vendor lock-in, works with any LLM/agent platform

## How It Differs From RAG

| RAG | LLM-Wiki-Obsidian-Hermes |
|-----|--------------------------|
| Discovers knowledge every query | Compiles knowledge once, maintains over time |
| Stale embeddings silently drift | Source hashes detect drift instantly |
| Agents can't self-correct | Agents edit structured pages with review |
| Opaque vector soup | Transparent, grep-able filesystem |
| One-shot retrieval | Multi-tier: hot/warm/cold/archive |

## Architecture

```text
Hermes Agent
  |
  +-- built-in MEMORY.md / USER.md      (tiny hot memory + pointers)
  +-- session_search                     (FTS5 recall of prior sessions)
  +-- memory provider plugin             (optional prefetch/retrieval)
  +-- skill pack                         (manual agent workflows)
  +-- cron jobs                          (collector, heartbeat, audit)
  +-- MCP tools                          (query brain from any agent)
  |
  v
r0b0tlabbra1n
  |
  +-- vault/                             (Markdown/Obsidian source of truth)
  +-- raw/                               (immutable source captures)
  +-- indexes/                           (SQLite FTS, embeddings, graph)
  +-- scripts/                           (ingest, lint, search, eval)
  +-- plugins/hermes_memory/             (Hermes provider plugin)
  +-- skills/                            (Hermes skill installable by user)
  +-- mcp_server/                        (optional MCP brain server)
  +-- evals/                             (benchmarks and gold sets)
```

## Memory Tiers

- **L1 HOT (<= few KB):** Hermes built-in MEMORY.md + USER.md — tiny pointer layer
- **L2 WARM:** START_HERE, dashboards, project status, operating rules
- **L3 COLD:** session summaries, raw evidence, detailed project pages
- **L4 ARCHIVE:** immutable raw captures, old logs, superseded pages

## Quickstart

```bash
# Clone
git clone https://github.com/r0b0tlab/llm-wiki_obsidian_hermes_r0b0tlabbra1n ~/brain
cd ~/brain

# Install
pip install -e .

# Initialize a brain vault
brain init --vault ~/my-brain

# Lint
brain lint --vault ~/my-brain

# Search
brain search "how to deploy vLLM" --vault ~/my-brain
```

## Hermes Integration Modes

| Mode | Description | Setup |
|------|-------------|-------|
| **A: Filesystem-only** | Vault + Python scripts + Hermes skill | `hermes skills install llm-wiki-brain` |
| **B: Indexed local** | SQLite FTS5 + link graph + local embeddings | Mode A + `brain index build` |
| **C: Hermes-native** | Memory provider plugin + cron jobs + MCP | Mode B + plugin install |
| **D: World-class** | Temporal graph + hybrid retrieval + eval harness | All of the above |

## Four Memory Types

- **Working:** current prompt/history/tool outputs (Hermes runtime)
- **Episodic:** sessions, events, decisions, failures (sessions/, _agent/episodic/)
- **Semantic:** stable facts, project status, concepts (_agent/semantic/, projects/)
- **Procedural:** skills, workflows, playbooks (skills/, procedures/)

## Key Design Principles

1. Markdown is the source of truth — indexes are derived and rebuildable
2. Raw sources are immutable — every synthesized claim has provenance
3. Always-loaded memory stays tiny — retrieval is explicit and budgeted
4. Automation must be idempotent — a fresh agent must orient in < 2 minutes
5. Humans can browse and correct everything in Obsidian
6. Secrets never enter the vault
7. No one-off event becomes an operating rule without evidence
8. Agent memory must be evaluated, not vibe-checked

## Relationship to Inspirations

- **LLM Wiki (Karpathy):** the vault is the compiled knowledge layer; agents maintain it
- **GBrain (garrytan):** Markdown truth + retrieval indexes; hybrid search; evaluation
- **MemGPT/Letta:** tier-based memory with explicit promotion/demotion
- **Zep/Graphiti:** temporal facts with validity windows and provenance

## License

MIT

## Credits

@mr-r0b0t on X — r0b0tlab

Inspired by:
- [Karpathy LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [garrytan/gbrain](https://github.com/garrytan/gbrain)
- [MemGPT](https://arxiv.org/abs/2310.08560)
- [Generative Agents](https://arxiv.org/abs/2304.03442)
