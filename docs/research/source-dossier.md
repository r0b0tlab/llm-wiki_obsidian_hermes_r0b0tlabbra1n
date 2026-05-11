# LLM Wiki Brain — Research Dossier

## Source Systems Reviewed

### 1. Karpathy LLM Wiki
- **Source:** https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- **Key insight:** Knowledge should compound as a maintained artifact — ingest → synthesize → maintain → query → refine
- **Architecture:** raw immutable sources → maintained Markdown wiki → schema/instruction doc
- **Applied:** Markdown vault is canonical knowledge layer; indexes rebuildable from source

### 2. garrytan/gbrain (v0.31)
- **Source:** https://github.com/garrytan/gbrain (cloned 2026-05-11)
- **Tech:** TypeScript/Bun, PGLite (embedded Postgres WASM), Supabase + pgvector
- **Architecture:** Markdown truth + DB retrieval, CLI + MCP, hybrid search (vector + keyword + RRF)
- **Key features:** compiled truth + timeline model, typed knowledge graphs, eval harness (LongMemEval)
- **Applied:** Markdown source of truth with rebuildable indexes, hybrid retrieval, eval from day one
- **Different:** We use Python + SQLite/FTS5 (not TS/Bun + Postgres), filesystem-first (not DB-first)

### 3. MemGPT / Letta
- **Source:** https://arxiv.org/abs/2310.08560, https://docs.letta.com/
- **Key insight:** OS-tier memory: limited fast context, larger slow storage, explicit paging
- **Applied:** L1-L4 tier system with promotion/demotion rules, background cron consolidation

### 4. Generative Agents
- **Source:** https://arxiv.org/abs/2304.03442
- **Key insight:** Reflection synthesizes lower-level memories into higher-level insights
- **Applied:** Cron reflection jobs produce pattern pages, retrieval combines recency + importance + similarity

### 5. Mem0
- **Source:** https://docs.mem0.ai/
- **Key insight:** Memory layered by scope; token efficiency matters
- **Applied:** Explicit scope fields, token budgets on all retrieval packets

### 6. Zep / Graphiti
- **Source:** https://help.getzep.com/graphiti/
- **Key insight:** Facts need validity windows, contradiction tracking
- **Applied:** Future: temporal edges with valid_from/valid_to/superseded_by

### 7. LangGraph / LangMem
- **Source:** https://langchain-ai.github.io/langgraph/concepts/memory/
- **Key insight:** Distinct memory types: semantic, episodic, procedural, profile
- **Applied:** Page type taxonomy, promotion rules per type

## Hermes Native Integration

### Already Used
- `memory` tool → L1 HOT built-in memory (MEMORY.md + USER.md)
- `session_search` → interactive recall of past sessions
- `skill_view` → procedural instructions for agents
- `search_files` / `read_file` → vault navigation
- `cronjob` → heartbeat + audit automation

### Planned
- Memory provider plugin → native prefetch/retrieval via plugin hooks
- Context engine plugin → lossless compression with DAG anchors
- MCP server → brain accessible to any MCP-compatible agent

## Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| Python + SQLite/FTS5 over TS/Postgres | Hermes-first, zero external deps, portable |
| Markdown source of truth over DB-first | Human-auditable, git-friendly, rebuildable indexes |
| Standalone FTS5 over content= mode | Simpler, works reliably with snippet() |
| Vault-root-relative wikilinks over file-relative | Deterministic, easier for agents to write |
| Secret scanner on every write | Defense in depth, prevents accidental leaks |
| Idempotent session ingest | Safe to run repeatedly via cron |

## Comparison Table

| Feature | LLM Wiki (Karpathy) | GBrain | MemGPT | r0b0tlabbra1n |
|---------|---------------------|--------|--------|---------------|
| Language | N/A (concept) | TypeScript | Python | Python |
| Storage | Markdown | Markdown + PGLite | SQLite + vector | Markdown + SQLite |
| Search | Full-text | Hybrid (vector + keyword + RRF) | Embedding | FTS5 (future: hybrid) |
| Memory Tiers | L1/L2/L3 | Compiled truth + timeline | Hot/warm/cold | L1-L4 hot/warm/cold/archive |
| Eval | Manual | BrainBench + LongMemEval | LongMemEval | Planned |
| Agent Integration | Manual | MCP + CLI + plugin | API + SDK | Hermes skill + memory provider + MCP |
| Secret Scanning | No | No | No | Yes (on every write) |
