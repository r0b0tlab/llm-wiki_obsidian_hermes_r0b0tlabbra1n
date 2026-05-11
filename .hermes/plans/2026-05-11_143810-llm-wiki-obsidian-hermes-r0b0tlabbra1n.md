# llm-wiki_obsidian_hermes_r0b0tlabbra1n Review and Optimization Plan

> **For Hermes:** This is a planning/research deliverable only. Use `subagent-driven-development` or dedicated research subagents to execute the phases later. Do not implement from this plan without first confirming the phase scope with the user.

**Goal:** Design and build the best filesystem-first LLM-Wiki + Obsidian + Hermes Agent memory system in the world, named `llm-wiki_obsidian_hermes_r0b0tlabbra1n`.

**Architecture:** A standalone GitHub-ready project that treats Markdown/Obsidian as the human-auditable source of truth, Hermes native memory as a compact always-injected index, Hermes session SQLite as the raw interaction event log, and optional DB/vector/graph indexes as regenerable acceleration layers. The system should preserve prompt-cache stability, avoid giant always-injected memories, and expose Hermes-native skills/tools/plugins/cron jobs for ingestion, retrieval, linting, reflection, and publishing.

**Tech Stack:** Python 3.11+, Markdown/Obsidian, SQLite/WAL/FTS5, optional sqlite-vec/pgvector/PGLite/Postgres, optional graph store, Hermes skills, Hermes memory provider plugin, Hermes context engine plugin, Hermes cron jobs, Hermes MCP server/client support, file/search/session_search tools, git.

---

## Document Metadata

- Version: 0.1 planning draft
- Date: 2026-05-11
- Author: Hermes Agent for r0b0tlab
- Project directory: `/home/mr-r0b0t/LLM-Wiki-Obsidian-Hermes-r0b0tlab`
- Proposed package/repo name: `llm-wiki_obsidian_hermes_r0b0tlabbra1n`
- Intended GitHub org: `r0b0tlab`
- Credit requirement: README and metadata should credit `@mr-r0b0t on X — r0b0tlab`
- Status: planning / review / architecture design
- Approval: pending user review

---

## Executive Summary

The current Hermes setup already has the right philosophy: keep built-in persistent memory tiny, place durable detailed state in a filesystem-first Obsidian/LLM wiki, read the wiki on demand, and automate consolidation with cron. The opportunity is to convert this from an ad-hoc local vault into a rigorous, reusable, first-principles memory system that other Hermes users can install.

The core insight from Karpathy's LLM Wiki is that memory should compound as a maintained artifact: ingest → synthesize → maintain → query → refine. The core insight from GBrain is that the human-editable Markdown brain should be source-of-truth while retrieval indexes, graph edges, embeddings, and CLI/MCP surfaces are acceleration layers. The core insight from Hermes is that prompt-cache stability and bounded always-injected memory are non-negotiable: detailed recall must be retrieved on demand or via ephemeral prefetch, not stuffed into the system prompt.

The proposed system has four layers:

1. Raw evidence layer: immutable source material, Hermes sessions, tool outputs, project docs, web captures.
2. Compiled wiki layer: Obsidian-friendly Markdown pages for projects, sessions, decisions, failures, successes, entities, concepts, procedures, skills, and dashboards.
3. Index layer: SQLite/FTS5, optional embeddings, optional temporal graph, link graph, manifests, source hashes, and evaluation corpora. Regenerable from Markdown and raw evidence.
4. Hermes integration layer: compact memory pointers, a skill pack, optional memory-provider plugin, optional context-engine plugin, cron jobs, MCP server, slash-command-compatible workflows, and project `.hermes.md` pointers.

The plan below first reviews source systems and current Hermes constraints, then defines target architecture, schemas, algorithms, evaluation, rollout, and risk controls.

---

## Table of Contents

1. Source Review
2. Current Hermes Memory System Review
3. First-Principles Design Requirements
4. Proposed Architecture
5. Data Model and Vault Layout
6. Retrieval and Recall Strategy
7. Ingestion and Consolidation Pipeline
8. Hermes-Native Integration Plan
9. Obsidian UX Plan
10. Evaluation and Benchmark Plan
11. Security, Privacy, and Governance
12. Implementation Phases
13. Detailed Task Plan
14. Files Likely to Change/Create
15. Tests and Validation
16. Risk Register
17. Assumptions and Constraints
18. Dependencies
19. Communication Plan
20. Change Management
21. Budget and Procurement
22. Glossary
23. References

---

## 1. Source Review

### 1.1 Karpathy LLM Wiki gist

Source: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

Key lessons:

- Standard RAG rediscovers knowledge on every query; an LLM Wiki compiles knowledge once and maintains it over time.
- The wiki is a persistent, compounding artifact.
- Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase.
- Architecture has three layers:
  - raw immutable sources
  - maintained Markdown wiki
  - schema/instruction document defining conventions and workflows
- Core operations:
  - ingest new sources
  - create/update summaries, entity pages, concept pages, comparisons
  - cross-reference pages
  - note contradictions
  - log actions
  - answer queries by reading the compiled wiki
  - save valuable query-derived syntheses back into the wiki
- Human role: curate sources, guide judgment, review outputs.
- Agent role: maintain structure, update pages, cross-link, track provenance.

Implications for `r0b0tlabbra1n`:

- The Markdown vault is the canonical knowledge layer, not embeddings.
- Every automated index must be rebuildable from raw + wiki files.
- Query answers should become first-class wiki artifacts when they are expensive to recreate.
- The schema must be strict enough to prevent entropy but easy for agents to follow.

### 1.2 garrytan/gbrain

Source: https://github.com/garrytan/gbrain

Observed architecture from current repo summary:

- Public TypeScript/Bun repo titled “Garry's Opinionated OpenClaw/Hermes Agent Brain.”
- Markdown source of truth plus database retrieval layer.
- Human-editable pages use a compiled truth + timeline model:
  - compiled truth: current best understanding
  - timeline: append-only evidence trail
- Default database: embedded Postgres/PGLite at `~/.gbrain/brain.pglite`.
- Optional backend: Supabase/Postgres + pgvector.
- CLI and MCP are thin wrappers over shared operations.
- Hybrid retrieval includes:
  - pgvector HNSW vector search
  - Postgres `tsvector` keyword search
  - Reciprocal Rank Fusion
  - cosine re-scoring
  - compiled-truth and backlink boosts
  - multi-query expansion
  - source-aware deduplication
- Typed knowledge graph extraction auto-wires edges such as `attended`, `works_at`, `invested_in`, `founded`, `advises`.
- Benchmarking posture includes BrainBench and LongMemEval-style metrics.

What to learn/copy:

- Markdown remains source of truth; database/indexes are derived.
- Provide CLI + MCP surfaces over the same core operations.
- Use hybrid retrieval, not pure vector search.
- Boost compiled truth and backlinks.
- Preserve evidence timelines so facts are auditable.
- Add typed graph edges for structured relationships, not just loose links.
- Include evaluation harnesses early.

What to avoid or adapt:

- Do not make Postgres/PGLite mandatory for a Hermes-first portable project; start with Python + SQLite/FTS5 and allow optional PGLite/Postgres adapters.
- Do not let generated graph facts silently become truth; graph edges need provenance, confidence, validity intervals, and human/agent review status.
- Do not treat MCP as the only integration. Hermes has native skills, memory providers, cron, plugins, and session_search that should be first-class.

### 1.3 MemGPT / Letta

Sources:

- MemGPT paper: https://arxiv.org/abs/2310.08560
- Letta docs: https://docs.letta.com/
- Letta memory docs: https://docs.letta.com/letta-code/memory

Key lessons:

- Treat memory like an operating system: limited fast context, larger slow storage, and explicit paging between tiers.
- Separate agents from conversations: an agent has state and memories; conversations are threads with that agent.
- Use memory tiers and context management rather than one giant prompt.
- Support background reflection/dreaming to consolidate memory outside the hot path.
- Provide memory doctor/audit tools to detect drift.
- Let agents self-edit memory but with structure and review.

Implications:

- `r0b0tlabbra1n` should define hot, warm, cold, and archive tiers.
- Hermes built-in `MEMORY.md` and `USER.md` are hot curated memory.
- Obsidian wiki pages are warm human-readable semantic memory.
- Hermes `state.db` and raw source captures are cold evidence memory.
- Background cron “dream” jobs should perform consolidation, promotion, demotion, and linting.

### 1.4 Generative Agents

Source: https://arxiv.org/abs/2304.03442

Key lessons:

- Store complete records of experience.
- Retrieve memories dynamically for planning.
- Reflection synthesizes lower-level memories into higher-level insights.
- Observation, planning, and reflection are all critical.

Implications:

- Sessions should be ingested as episodes, then promoted to semantic patterns only when repeated or important.
- Reflection jobs should produce higher-level pages: failure patterns, success patterns, decision principles, open loops.
- Retrieval ranking should combine recency, importance, semantic similarity, project scope, and explicit link proximity.

### 1.5 Mem0

Sources:

- Overview: https://docs.mem0.ai/overview
- Memory types: https://docs.mem0.ai/core-concepts/memory-types
- Memory evaluation: https://docs.mem0.ai/core-concepts/memory-evaluation

Key lessons:

- Memory should be layered by scope:
  - conversation memory
  - session memory
  - user memory
  - organizational memory
- Token efficiency matters. Accurate retrieval with less context is better than dumping full history.
- Memory extraction/distillation and multi-signal retrieval are core production concerns.
- Evaluation should include LoCoMo, LongMemEval, and custom task-based metrics.

Implications:

- `r0b0tlabbra1n` should avoid over-fetching. Every retrieval result should have a token budget and rationale.
- Add explicit scope fields: user, agent profile, workspace, project, session, platform, time range, source type.
- Include retrieval evaluation from day one.

### 1.6 Zep / Graphiti

Source: https://help.getzep.com/graphiti/graphiti/overview

Key lessons:

- Dynamic memory benefits from temporal knowledge graphs.
- Ingest data as discrete episodes with provenance.
- Track changing facts and invalidated relationships over time.
- Query with hybrid semantic, full-text, time, and graph algorithms.
- Custom entity types matter.
- GraphRAG is often static; agent memory needs continuous incremental updates.

Implications:

- Facts need validity windows: observed_at, valid_from, valid_to, superseded_by.
- Contradictions are not just text notes; they are temporal updates.
- Build a simple file-backed/SQLite temporal edge model first; make Neo4j/Postgres graph optional later.

### 1.7 LangGraph / LangMem

Source: https://langchain-ai.github.io/langgraph/concepts/memory/

Key lessons:

- Differentiate short-term and long-term memory.
- Long-term memory includes semantic, episodic, and procedural memory.
- Writing memories can happen in the hot path or in the background.
- Profiles and collections are different memory shapes.

Implications:

- Use distinct page families and promotion rules:
  - semantic: facts and stable knowledge
  - episodic: session/event records
  - procedural: skills and workflows
  - profile: user preferences and identity
- Hot-path writes should be minimal and deterministic.
- Background writes can be richer and reflective.

### 1.8 Cognee and other graph/RAG systems

Source: https://docs.cognee.ai/

Key lessons:

- Graph + vector + LLM pipelines can turn unstructured data into queryable memory.
- MCP and API surfaces make memory portable across agents.
- Pipelines and custom tasks are important for adaptation.

Implications:

- Provide MCP server tools so non-Hermes agents can query the brain.
- Keep pipeline definitions explicit and testable.
- Use graph/vector as accelerators, not the only source of truth.

---

## 2. Current Hermes Memory System Review

Reviewed local Hermes source/docs:

- `/home/mr-r0b0t/.hermes/hermes-agent/agent/memory_manager.py`
- `/home/mr-r0b0t/.hermes/hermes-agent/agent/memory_provider.py`
- `/home/mr-r0b0t/.hermes/hermes-agent/tools/memory_tool.py`
- `/home/mr-r0b0t/.hermes/hermes-agent/tools/session_search_tool.py`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/user-guide/features/memory.md`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/developer-guide/prompt-assembly.md`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/developer-guide/memory-provider-plugin.md`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/developer-guide/context-engine-plugin.md`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/developer-guide/context-compression-and-caching.md`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/developer-guide/session-storage.md`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/developer-guide/cron-internals.md`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/developer-guide/creating-skills.md`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/developer-guide/adding-tools.md`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/developer-guide/architecture.md`

### 2.1 Built-in memory

Hermes built-in memory uses two files under profile-scoped `~/.hermes/memories/`:

- `MEMORY.md`: agent notes, environment facts, conventions, tool quirks
- `USER.md`: user profile, preferences, style, expectations

Important constraints:

- `MEMORY.md` target limit: 2,200 chars.
- `USER.md` target limit: 1,375 chars.
- Both are injected as frozen snapshots at session start.
- Mid-session writes persist to disk but do not alter the current system prompt.
- This preserves prompt-cache stability.
- The `memory` tool supports add/replace/remove with substring matching.
- Memory content is scanned for prompt-injection/exfiltration patterns before being stored.

Design implication:

- Built-in Hermes memory must remain a tiny “L1 cache” and pointer layer, not the full brain.
- `r0b0tlabbra1n` should mirror or summarize only tiny durable pointers into built-in memory.

### 2.2 Memory provider plugins

Hermes exposes `MemoryProvider` with lifecycle hooks:

- `initialize(session_id, **kwargs)`
- `system_prompt_block()`
- `prefetch(query, session_id=...)`
- `queue_prefetch(query, session_id=...)`
- `sync_turn(user, assistant, session_id=...)`
- `get_tool_schemas()`
- `handle_tool_call()`
- `on_turn_start()`
- `on_session_end()`
- `on_session_switch()`
- `on_pre_compress()`
- `on_memory_write()`
- `on_delegation()`
- `shutdown()`

Important constraints:

- Only one external memory provider is allowed at a time.
- `sync_turn()` must be non-blocking.
- Providers must use `hermes_home` / `get_hermes_home()` and not hardcode `~/.hermes`.
- Subagents and cron may have special `agent_context`; providers should avoid corrupting primary user memory with cron/subagent noise.
- Prefetched memory is wrapped in `<memory-context>` and scrubbed from streaming output to avoid leaking internal memory blocks.

Design implication:

- `r0b0tlabbra1n` should ship an optional Hermes memory provider plugin named something like `r0b0tlabbra1n` or `llm-wiki-brain`.
- The provider should be context-only by default, with explicit tools for search/ingest/promote.
- It should not auto-write rich summaries during every turn until the user enables that mode.

### 2.3 Session storage and search

Hermes stores sessions in `~/.hermes/state.db`:

- SQLite with WAL mode.
- `sessions` table for metadata, model info, costs, parent_session_id.
- `messages` table for full message history.
- FTS5 tables for full-text and trigram search.
- `state_meta` for key/value state.
- Session lineage via `parent_session_id`.

`session_search` searches FTS5, groups matches by session, loads truncated transcript windows up to about 100k chars, and asks an auxiliary model to summarize relevant sessions.

Design implication:

- Full session ingest should read `state.db` read-only via SQLite URI mode: `file:/path/to/state.db?mode=ro`.
- Do not write to Hermes `state.db` from this project.
- Preserve session lineage and platform/source tags in the wiki.
- Use `session_search` for interactive recall, but use read-only SQLite batch ingest for deterministic full vault maintenance.

### 2.4 Prompt assembly and caching

Hermes system prompt layers include identity, tool guidance, static provider blocks, frozen memory snapshots, user profile snapshot, skills index, one project context file, timestamp/session, and platform hint.

Context file priority:

1. `.hermes.md` / `HERMES.md`
2. `AGENTS.md`
3. `CLAUDE.md`
4. `.cursorrules` / Cursor rules

Important constraints:

- Only one project context source is loaded.
- Adding `.hermes.md` can hide existing `AGENTS.md`/`CLAUDE.md` instructions.
- Prompt-cache stability is a first-order design constraint.

Design implication:

- The project should provide a tiny optional `.hermes.md` pointer template, not auto-install it blindly.
- The brain should rely on on-demand tools and memory-provider prefetch, not giant prompt injection.

### 2.5 Context engine plugins

Hermes supports replacing the built-in context compressor with a `ContextEngine` plugin.

Important hooks:

- `should_compress()`
- `compress()`
- `on_session_start()`
- `on_session_end()`
- `on_pre_compress()` via memory providers
- optional engine tools such as `lcm_grep`

Design implication:

- v1 should not replace Hermes compression by default.
- A later `r0b0tlabbra1n` context engine could implement lossless context management: extract compressed middle turns into a session DAG/wiki page, then return short summary plus retrievable anchors.

### 2.6 Cron, skills, tools, MCP, plugins

Hermes-native capabilities to exploit:

- Skills: procedural instructions, scripts, templates, references; easiest shareable integration.
- Cron: scheduled heartbeat, session collector, deep audit, source drift checks.
- Memory provider plugin: prefetch, sync, on-memory-write, on-delegation.
- Context engine plugin: lossless compression / DAG context later.
- MCP: expose the brain to other agents and let Hermes consume external MCP tools.
- Gateway delivery: daily/weekly reports can be delivered to Telegram or other platforms.
- `session_search`: recall past conversations interactively without overloading context.
- `delegate_task`: parallel research/ingest workers for large source batches.
- File/search tools: native markdown vault operations.

---

## 3. First-Principles Design Requirements

### 3.1 Non-negotiable principles

1. Markdown is the source of truth.
2. Raw sources are immutable.
3. Every synthesized claim should have provenance.
4. Every durable fact has a scope and freshness policy.
5. Always-loaded memory stays tiny.
6. Retrieval is explicit, budgeted, and explainable.
7. Indexes are derived and rebuildable.
8. Automation must be idempotent.
9. A fresh Hermes agent must orient in under two minutes.
10. Humans can browse and correct everything in Obsidian.
11. Secrets never enter the vault.
12. No one-off event is promoted to an operating rule without evidence.
13. Agent memory must be evaluated, not vibe-checked.

### 3.2 Memory taxonomy

Use four memory types:

- Working memory: current prompt/history/tool outputs; owned by Hermes runtime.
- Episodic memory: sessions, events, decisions, failures, successes; stored in `sessions/` and `_agent/episodic/`.
- Semantic memory: stable facts, project status, user/environment facts, concepts; stored in `_agent/semantic/`, `projects/`, `entities/`, `concepts/`.
- Procedural memory: skills, workflows, commands, playbooks; stored in `skills/`, `procedures/`, and optionally promoted into Hermes skills.

Use four tiers:

- L1 hot: Hermes `MEMORY.md` and `USER.md`, <= a few KB.
- L2 warm: START_HERE, dashboards, project status, operating rules.
- L3 cold: session summaries, raw evidence, detailed project pages.
- L4 archive: immutable raw captures, old logs, superseded pages.

### 3.3 Quality dimensions

Each memory item/page should be scored or labeled by:

- confidence: high / medium / low
- source count
- recency
- scope
- owner
- contradiction status
- review status
- expiry/staleness policy
- provenance completeness
- retrieval usefulness

---

## 4. Proposed Architecture

```text
Hermes Agent
  |
  |-- built-in MEMORY.md / USER.md  (tiny hot memory + pointers)
  |-- session_search                (FTS5 recall of prior sessions)
  |-- memory provider plugin        (optional r0b0tlabbra1n recall/prefetch)
  |-- skill pack                    (manual agent workflows)
  |-- cron jobs                     (collector, heartbeat, audit)
  |-- MCP tools                     (query brain from any agent)
  |-- context engine plugin         (future lossless compression)
  |
  v
llm-wiki_obsidian_hermes_r0b0tlabbra1n
  |
  |-- vault/                        (Markdown/Obsidian source of truth)
  |-- raw/                          (immutable source captures)
  |-- indexes/                      (SQLite FTS, embeddings, graph, link graph)
  |-- scripts/                      (ingest, lint, search, eval, redact)
  |-- plugins/hermes_memory/         (optional Hermes plugin install target)
  |-- skills/                       (Hermes skill(s) installable by user)
  |-- mcp_server/                   (optional MCP brain server)
  |-- evals/                        (benchmarks and gold sets)
  |-- docs/                         (architecture, setup, examples)
```

### 4.1 Operating modes

Mode A: Filesystem-only minimum viable brain

- Markdown vault + Python scripts + Hermes skill.
- SQLite optional but recommended.
- No external services.

Mode B: Indexed local brain

- SQLite FTS5 + link graph + local embeddings.
- CLI search and ranking.
- Hermes skill uses scripts for lookup.

Mode C: Hermes-native brain

- Memory provider plugin prefetches scoped context.
- Cron jobs collect sessions and run reflection.
- MCP server exposes query/ingest/lint/promote tools.

Mode D: World-class research brain

- Temporal graph, hybrid retrieval, reranking, eval harness, visual dashboards, Obsidian dataview, benchmark reports.

---

## 5. Data Model and Vault Layout

### 5.1 Proposed repository layout

```text
llm-wiki_obsidian_hermes_r0b0tlabbra1n/
├── README.md
├── LICENSE
├── pyproject.toml
├── r0b0tlabbra1n/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── paths.py
│   ├── models.py
│   ├── ingest/
│   │   ├── hermes_sessions.py
│   │   ├── projects.py
│   │   ├── web_sources.py
│   │   └── skills.py
│   ├── vault/
│   │   ├── schema.py
│   │   ├── frontmatter.py
│   │   ├── links.py
│   │   ├── write_ops.py
│   │   └── templates.py
│   ├── index/
│   │   ├── sqlite_index.py
│   │   ├── embeddings.py
│   │   ├── graph.py
│   │   ├── rank.py
│   │   └── rebuild.py
│   ├── memory/
│   │   ├── extract.py
│   │   ├── promote.py
│   │   ├── reflect.py
│   │   ├── retrieve.py
│   │   └── policy.py
│   ├── evals/
│   │   ├── datasets.py
│   │   ├── metrics.py
│   │   └── run.py
│   ├── security/
│   │   ├── redact.py
│   │   └── secret_scan.py
│   └── obsidian/
│       ├── dataview.py
│       └── graph_export.py
├── hermes/
│   ├── skills/llm-wiki-brain/SKILL.md
│   ├── plugins/memory/r0b0tlabbra1n/__init__.py
│   ├── plugins/memory/r0b0tlabbra1n/plugin.yaml
│   ├── plugins/context_engine/r0b0tlabbra1n_lcm/__init__.py
│   └── cron_prompts/
├── mcp_server/
├── templates/
│   ├── vault/START_HERE.md
│   ├── vault/SCHEMA.md
│   ├── vault/index.md
│   ├── vault/log.md
│   ├── pages/project-overview.md
│   ├── pages/session-summary.md
│   ├── pages/decision.md
│   ├── pages/failure.md
│   ├── pages/success.md
│   └── context/.hermes.md
├── scripts/
│   ├── brain-init
│   ├── brain-ingest-hermes
│   ├── brain-search
│   ├── brain-lint
│   ├── brain-redact
│   └── brain-eval
├── docs/
│   ├── architecture.md
│   ├── hermes-integration.md
│   ├── obsidian-setup.md
│   ├── memory-policy.md
│   └── evaluation.md
├── evals/
│   ├── gold/
│   └── reports/
└── tests/
```

### 5.2 Proposed vault layout

```text
vault/
├── START_HERE.md
├── SCHEMA.md
├── index.md
├── log.md
├── README.md
├── raw/
│   ├── articles/
│   ├── papers/
│   ├── sessions/
│   ├── projects/
│   ├── skills/
│   └── assets/
├── dashboards/
│   ├── agent-dashboard.md
│   ├── project-dashboard.md
│   ├── stale-items.md
│   ├── open-questions.md
│   ├── memory-health.md
│   └── retrieval-quality.md
├── _agent/
│   ├── START_HERE.md
│   ├── operating-rules.md
│   ├── memory-policy.md
│   ├── review-checklist.md
│   ├── session-template.md
│   ├── semantic/
│   │   ├── project-status.md
│   │   ├── user-preferences.md
│   │   ├── environment-facts.md
│   │   ├── tool-quirks.md
│   │   ├── failure-patterns.md
│   │   ├── success-patterns.md
│   │   ├── decision-principles.md
│   │   └── open-loops.md
│   ├── episodic/
│   │   ├── decisions/
│   │   ├── failures/
│   │   ├── successes/
│   │   └── incidents/
│   ├── heartbeat/
│   └── audits/
├── projects/
│   └── <project>/
│       ├── overview.md
│       ├── status.md
│       ├── architecture.md
│       ├── log.md
│       ├── decisions.md
│       ├── pitfalls.md
│       └── procedures.md
├── sessions/
│   ├── summaries/
│   ├── transcripts-index.md
│   └── lineage.md
├── entities/
├── concepts/
├── comparisons/
├── queries/
├── procedures/
├── skills/
│   ├── catalog/
│   └── improvement-candidates.md
└── _meta/
    ├── config.yaml
    ├── ingestion-manifest.jsonl
    ├── source-hashes.json
    ├── link-graph.json
    ├── entity-graph.jsonl
    ├── memory-items.jsonl
    ├── retrieval-index.sqlite
    ├── lint-history.jsonl
    ├── eval-history.jsonl
    └── vault-state.json
```

### 5.3 Page frontmatter

Every compiled page should include:

```yaml
---
title: Human Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: project | session | decision | failure | success | entity | concept | procedure | query | dashboard | schema
status: active | draft | stale | archived | superseded
scope: user | agent | workspace | project | global
project: optional-project-slug
session_ids: []
sources: []
confidence: high | medium | low
review_status: unreviewed | agent-reviewed | human-reviewed
agent_written: true
provenance_complete: true | false
expires: null
superseded_by: null
tags: []
---
```

### 5.4 Memory item schema

For machine index JSONL:

```json
{
  "id": "mem_...",
  "type": "semantic|episodic|procedural|profile",
  "scope": "user|agent|workspace|project|global",
  "project": "slug-or-null",
  "text": "atomic memory statement",
  "source_pages": ["projects/x/overview.md"],
  "source_events": ["session:...", "message:..."],
  "confidence": "high|medium|low",
  "importance": 0.0,
  "recency_ts": 0,
  "created_at": "ISO",
  "updated_at": "ISO",
  "valid_from": "ISO|null",
  "valid_to": "ISO|null",
  "status": "active|stale|superseded|rejected",
  "hash": "sha256"
}
```

---

## 6. Retrieval and Recall Strategy

### 6.1 Retrieval pipeline

Input: user query + Hermes runtime context.

Signals:

- lexical BM25/FTS5 match
- semantic embedding similarity
- wikilink/backlink proximity
- graph neighborhood proximity
- project scope match
- session/source/platform match
- recency
- importance
- confidence/review status
- page type boost
- compiled truth boost

Algorithm:

1. Normalize query and infer scope.
2. Run FTS5 keyword search.
3. Run vector search when embeddings are enabled.
4. Expand query with project aliases, entity aliases, and wikilinks.
5. Gather graph neighbors for top entities.
6. Fuse rankings with reciprocal rank fusion.
7. Deduplicate by source page and memory hash.
8. Rerank with cheap cross-encoder/LLM only when needed.
9. Construct a token-budgeted context packet.
10. Return citations and “why retrieved” metadata.

### 6.2 Context packet format for Hermes

Memory provider prefetch should return compact fenced content:

```text
# r0b0tlabbra1n recalled context
Query: ...
Scope: project=..., user=..., session=...
Budget: 2,500 tokens

## Must-know facts
- Fact with citation [[projects/foo/status]]

## Relevant procedures
- Procedure with path `procedures/x.md`

## Recent related episodes
- Session summary with date and source

## Open risks / stale warnings
- Warning if memory may be stale
```

Rules:

- Default max prefetch: 1,500–3,000 tokens.
- Never include raw secrets.
- Prefer page pointers over dumping long content.
- Include confidence/staleness warnings.
- Do not prefetch during cron/subagent contexts unless explicitly enabled.

### 6.3 Manual tools

Hermes memory provider or MCP should expose:

- `brain_search(query, scope=None, limit=10)`
- `brain_read(page)`
- `brain_ingest_source(path_or_url, mode)`
- `brain_ingest_hermes_sessions(after=None)`
- `brain_promote(memory_id_or_page)`
- `brain_lint()`
- `brain_status()`
- `brain_open_questions()`

---

## 7. Ingestion and Consolidation Pipeline

### 7.1 Source ingest

For every new source:

1. Capture raw content under `raw/` with source URL/path and hash.
2. Run secret redaction before writing compiled pages.
3. Extract entities, concepts, claims, dates, and relationships.
4. Search existing wiki for matching pages.
5. Create/update pages with wikilinks and provenance.
6. Update index and dashboards.
7. Append log entry.
8. Rebuild indexes.
9. Run lint.

### 7.2 Hermes session ingest

Read-only ingestion from `$HERMES_HOME/state.db`:

1. Open SQLite URI in read-only mode.
2. Query sessions newer than last manifest cursor.
3. Preserve `id`, `parent_session_id`, source, model, token/cost metadata.
4. Extract session summary:
   - user goal
   - actions taken
   - decisions
   - failures
   - successes
   - files/commands/URLs
   - unresolved open loops
5. Create session summary page.
6. Create atomic episodic records when warranted.
7. Link to projects and skills.
8. Update `sessions/lineage.md`.
9. Append to ingestion manifest.

### 7.3 Promotion pipeline

Use staged promotion:

```text
event → evidence → session summary → episodic note → semantic pattern → operating rule or skill patch → verification
```

Promotion criteria:

- Session summary: every substantive session.
- Episodic note: important decision/failure/success.
- Semantic pattern: 2+ independent occurrences or one user-confirmed durable preference.
- Operating rule: 3+ occurrences or one critical incident + user confirmation.
- Skill patch: reusable procedure validated by execution.
- Built-in Hermes memory: only tiny, durable, high-utility facts.

### 7.4 Reflection jobs

Daily heartbeat:

- ingest new sessions
- update dashboards
- detect stale projects
- refresh project status
- surface open questions
- run lint/secret scan
- send concise Telegram digest if meaningful

Weekly deep audit:

- full link/frontmatter/index lint
- memory bloat audit
- contradiction audit
- source drift check
- skill improvement candidates
- retrieval eval sample
- promote/demote operating rules

Monthly rebuild:

- rebuild all derived indexes
- recompute embeddings/graph
- rerun benchmark suite
- archive stale pages

---

## 8. Hermes-Native Integration Plan

### 8.1 Skill pack

Create Hermes skill `llm-wiki-brain`.

Use when:

- user asks about the brain/wiki/memory system
- user asks to ingest sources into the vault
- user asks to query project/session memory
- user asks to audit memory quality
- user asks to set up Obsidian/Hermes memory integration

Skill should include:

- orientation procedure
- ingest procedure
- query procedure
- lint procedure
- promotion policy
- secret safety rules
- exact CLI commands
- references to templates/scripts

### 8.2 Memory provider plugin

Create optional provider under `hermes/plugins/memory/r0b0tlabbra1n/`.

Core behavior:

- `is_available`: brain config exists and vault path resolves.
- `initialize`: load config, open SQLite index read-only or lazy writable for brain index only.
- `system_prompt_block`: short static instruction, not rich memory.
- `queue_prefetch`: start background retrieval for next turn.
- `prefetch`: return cached scoped memory packet.
- `sync_turn`: append turn event to a local queue/manifest, non-blocking.
- `on_session_end`: optionally trigger summarization job or mark session for cron collector.
- `on_pre_compress`: extract key facts before compression and store as pending episodic evidence.
- `on_memory_write`: mirror built-in Hermes memory writes into semantic pages with provenance.
- `on_delegation`: record delegated task/result as evidence linked to parent session.

Safety defaults:

- auto-prefetch on, auto-rich-write off.
- no writes in `agent_context != primary` unless explicitly configured.
- no writes from cron unless the cron job is a brain maintenance job.
- strict token budget.

### 8.3 Context engine plugin, later phase

Future plugin: `r0b0tlabbra1n_lcm`.

Purpose:

- Replace lossy compression with loss-minimized archival.
- Before compression, write middle-turn evidence to session DAG pages and index.
- Return concise summary plus retrieval anchors.
- Expose `brain_context_grep` tool.

Do not make this default until evaluation proves it improves task success and does not harm prompt caching or role alternation.

### 8.4 Cron jobs

Recommended Hermes cron jobs:

1. `r0b0tlabbra1n-session-collector`
   - Schedule: every 2–4 hours or daily.
   - Script first collects new session IDs.
   - Agent summarizes and updates vault.

2. `r0b0tlabbra1n-daily-heartbeat`
   - Schedule: daily 09:00.
   - Skills: `llm-wiki-brain`, `obsidian`.
   - Updates dashboards and open loops.

3. `r0b0tlabbra1n-weekly-audit`
   - Schedule: weekly.
   - Runs lint, secret scan, stale memory detection, eval sample.

4. `r0b0tlabbra1n-index-rebuild`
   - Schedule: weekly/monthly or after major ingest.
   - no_agent script-only acceptable if deterministic.

### 8.5 MCP server

Expose brain operations through MCP for other agents:

- search
- read page
- ingest source
- lint
- get project status
- get user profile summary
- get memory health

Hermes can connect via native MCP configuration; other tools can use the same server.

### 8.6 Project context files

Provide `.hermes.md` template only:

```markdown
# Project Memory Pointer

Device/project knowledge lives at: <vault path>
Before substantive work, read:
- START_HERE.md
- _agent/START_HERE.md
- relevant projects/<project>/overview.md

Do not load the whole vault.
```

Installer must check for existing `.hermes.md`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules` and warn before writing.

---

## 9. Obsidian UX Plan

### 9.1 Human dashboards

Create dashboards:

- Agent dashboard: health, latest heartbeat, failures, skill candidates.
- Project dashboard: active/stale/completed projects.
- Memory health: broken links, stale facts, low-confidence pages.
- Retrieval quality: eval runs, top failures, recall metrics.
- Open questions: unresolved user decisions.

### 9.2 Obsidian conventions

- Use wikilinks for all internal references.
- Use YAML frontmatter consistently.
- Use Dataview-friendly fields.
- Use tags sparingly from controlled taxonomy.
- Keep pages under ~200 lines when possible.
- Split large pages into overview + detailed subpages.
- Store images/assets in `raw/assets/`.

### 9.3 Visual graph

Maintain `_meta/link-graph.json` and optionally export graph visuals:

- projects ↔ sessions
- sessions ↔ decisions/failures/successes
- skills ↔ procedures
- entities/concepts ↔ sources
- contradictions/supersessions

---

## 10. Evaluation and Benchmark Plan

### 10.1 Evaluation questions

Build gold questions from real use:

- What did we decide about X?
- Which command fixed Y?
- What projects are active and blocked?
- What should a new agent read before working on project Z?
- What user preference applies here?
- Which memories are stale or contradicted?
- Which skill should be loaded for this task?

### 10.2 Metrics

- Recall@K for relevant pages.
- Precision@K for non-noisy retrieval.
- Answer groundedness: every answer cites source pages.
- Token efficiency: useful answer context under fixed token budgets.
- Freshness: latest known project status is retrieved.
- Staleness avoidance: stale pages are flagged, not treated as current.
- Secret safety: zero secrets in vault/index/logs.
- Agent task impact: fewer repeated user corrections, fewer missed project conventions.

### 10.3 Benchmark suites

- Custom Hermes Session Recall benchmark.
- Project Resumption benchmark.
- Tool Quirk Recall benchmark.
- User Preference Recall benchmark.
- Failure Pattern Avoidance benchmark.
- LongMemEval-style long-session recall benchmark.
- LoCoMo-inspired multi-session personalized memory benchmark.

### 10.4 Eval reports

Write reports to:

```text
evals/reports/YYYY-MM-DD-memory-eval.md
vault/dashboards/retrieval-quality.md
```

---

## 11. Security, Privacy, and Governance

### 11.1 Secret safety

Hard rule: no secrets in Markdown vault.

Detect and block:

- HF tokens (`hf_`)
- OpenAI/Anthropic/GitHub tokens
- bearer tokens
- private keys
- `.env` values
- password assignments
- OAuth tokens

Store key names and config paths only, never values.

### 11.2 Prompt injection safety

- Treat raw sources as untrusted.
- Strip or quarantine instructions embedded in raw source material.
- Compiled pages should state facts, not commands to the agent, unless the page type is procedural and reviewed.
- Operating rules require evidence/review.
- Memory-provider prefetch wraps context as background reference, not user input.

### 11.3 Write controls

- Raw files immutable after ingest.
- Compiled pages atomically written.
- Indexes rebuilt from source.
- Every automated write logs changed files.
- Bulk updates require explicit scope in interactive sessions.

---

## 12. Implementation Phases

### Phase 0: Research freeze and source dossier

Objective: turn this plan into a source-backed design dossier.

Tasks:

1. Clone or inspect `garrytan/gbrain` more deeply.
2. Extract exact command surface, schema, benchmark harness, and database design.
3. Save source notes under `docs/research/`.
4. Save comparison table of memory systems.
5. Decide v1 scope.

Exit criteria:

- Source dossier pages exist.
- Architecture choices are linked to evidence.

### Phase 1: Standalone repo scaffold

Objective: create installable standalone project.

Tasks:

1. Initialize git repo under `/home/mr-r0b0t/LLM-Wiki-Obsidian-Hermes-r0b0tlab`.
2. Add `README.md` with r0b0tlab branding and credit.
3. Add `pyproject.toml`.
4. Add package skeleton.
5. Add CLI entry points.
6. Add tests skeleton.
7. Add MIT license or confirm license choice.

Exit criteria:

- `python -m pytest` passes.
- `brain --help` works.
- README describes Hermes/Obsidian/LLM Wiki purpose.

### Phase 2: Vault schema and initializer

Objective: create the canonical filesystem-first vault.

Tasks:

1. Implement templates.
2. Implement `brain init --vault PATH`.
3. Generate START_HERE, SCHEMA, index, log, dashboards, `_agent` pages.
4. Validate frontmatter.
5. Validate wikilinks.

Exit criteria:

- A new vault passes lint immediately after init.

### Phase 3: Lint, redaction, and index completeness

Objective: protect quality before ingestion.

Tasks:

1. Implement secret scanner.
2. Implement frontmatter lint.
3. Implement broken wikilink detection.
4. Implement orphan detection.
5. Implement index completeness check.
6. Implement source hash verification.
7. Add tests with fixture vaults.

Exit criteria:

- `brain lint` exits 0 on clean fixture and 1 on bad fixture.
- Secret fixture is blocked.

### Phase 4: Hermes session ingest

Objective: convert Hermes `state.db` into useful wiki memory.

Tasks:

1. Read `state.db` in read-only mode.
2. Track cursor in `_meta/ingestion-manifest.jsonl`.
3. Summarize sessions into pages.
4. Preserve lineage.
5. Extract decisions/failures/successes.
6. Link projects and skills.
7. Add tests with synthetic SQLite session DB.

Exit criteria:

- Synthetic sessions ingest into correct pages.
- Re-running ingest is idempotent.

### Phase 5: Search and retrieval index

Objective: make memory queryable without huge context.

Tasks:

1. Build SQLite FTS5 index from Markdown pages.
2. Parse wikilinks/backlinks.
3. Implement ranking and source deduplication.
4. Add context packet builder with token budget.
5. Add optional embeddings interface.
6. Add tests for retrieval relevance.

Exit criteria:

- `brain search "query"` returns cited pages and snippets.
- Retrieval packet respects token budget.

### Phase 6: Hermes skill integration

Objective: make any Hermes agent use the brain with existing tools.

Tasks:

1. Write `hermes/skills/llm-wiki-brain/SKILL.md`.
2. Add scripts under skill `scripts/` for search/lint/ingest.
3. Add references/templates.
4. Install locally for testing.
5. Test skill load with `skill_view` and real workflows.

Exit criteria:

- Hermes can query and lint the brain by loading the skill.

### Phase 7: Cron automation

Objective: automate maintenance safely.

Tasks:

1. Write self-contained cron prompts.
2. Add deterministic pre-run scripts.
3. Create daily heartbeat job.
4. Create weekly audit job.
5. Use local delivery first; Telegram optional after clean dry runs.
6. Document rollback/removal.

Exit criteria:

- Daily heartbeat updates dashboards without secrets or broken links.

### Phase 8: Hermes memory provider plugin

Objective: enable native prefetch and turn/event hooks.

Tasks:

1. Implement `MemoryProvider` plugin.
2. Implement config schema.
3. Implement fast `prefetch` with cached background query.
4. Implement non-blocking `sync_turn` queue.
5. Implement safe `on_memory_write` mirror.
6. Implement explicit provider tools.
7. Add tests against Hermes provider ABC.

Exit criteria:

- Provider activates via `memory.provider`.
- Prefetch returns useful context under budget.
- No streaming leaks.

### Phase 9: MCP server

Objective: make the brain agent-agnostic.

Tasks:

1. Expose search/read/lint/status tools via MCP.
2. Add Hermes native MCP setup docs.
3. Add smoke tests with MCP client.

Exit criteria:

- Hermes and another MCP client can query the same brain.

### Phase 10: Evaluation harness

Objective: prove memory quality.

Tasks:

1. Create gold QA format.
2. Generate seed benchmark from existing wiki/session data.
3. Implement recall and grounded-answer metrics.
4. Compare modes: FTS only, hybrid, graph boost, memory-provider packet.
5. Write dashboard report.

Exit criteria:

- Eval report shows measurable recall/precision/token budget.

### Phase 11: Optional temporal graph and embeddings

Objective: world-class retrieval beyond FTS.

Tasks:

1. Add temporal entity/relationship extraction.
2. Store edges with validity intervals and provenance.
3. Add graph neighborhood retrieval.
4. Add embedding adapters.
5. Add hybrid RRF ranking.
6. Evaluate against baseline.

Exit criteria:

- Hybrid retrieval beats FTS-only on benchmark without excessive tokens.

### Phase 12: Optional lossless context engine

Objective: integrate with Hermes compression.

Tasks:

1. Implement context engine plugin prototype.
2. On compression, archive middle turns into session DAG/wiki pages.
3. Return summary plus anchors.
4. Add role alternation tests.
5. Compare against default compressor.

Exit criteria:

- Context engine improves long-task recall and does not break Hermes invariants.

---

## 13. Detailed Task Plan

### Task 1: Create source dossier files

Files:

- Create: `docs/research/karpathy-llm-wiki.md`
- Create: `docs/research/gbrain-review.md`
- Create: `docs/research/agent-memory-systems.md`
- Create: `docs/research/hermes-native-surfaces.md`

Verification:

- Each file has references and design lessons.
- `grep -R "https://" docs/research` shows citations.

### Task 2: Create README

Files:

- Create: `README.md`

Required content:

- What this is.
- Why Markdown/Obsidian is source of truth.
- How it differs from RAG.
- Hermes integration modes.
- Quickstart.
- Architecture diagram.
- Credit: `@mr-r0b0t on X — r0b0tlab`.
- Relationship to Karpathy LLM Wiki and GBrain inspirations.

Verification:

- README includes project name exactly: `llm-wiki_obsidian_hermes_r0b0tlabbra1n`.
- README includes credit.

### Task 3: Add Python package scaffold

Files:

- Create: `pyproject.toml`
- Create: `r0b0tlabbra1n/__init__.py`
- Create: `r0b0tlabbra1n/cli.py`
- Create: `tests/test_cli.py`

Verification:

- `python -m pytest -q`
- `python -m r0b0tlabbra1n.cli --help`

### Task 4: Implement vault initializer

Files:

- Create: `r0b0tlabbra1n/vault/templates.py`
- Create: `templates/vault/*.md`
- Modify: `r0b0tlabbra1n/cli.py`
- Test: `tests/test_init_vault.py`

Verification:

- Temporary vault contains required directories/files.
- Init is idempotent.

### Task 5: Implement lint/redact

Files:

- Create: `r0b0tlabbra1n/security/secret_scan.py`
- Create: `r0b0tlabbra1n/vault/lint.py`
- Test: `tests/test_lint.py`
- Test: `tests/test_secret_scan.py`

Verification:

- Broken wikilinks fail.
- Invalid frontmatter fails.
- Secret fixture fails.

### Task 6: Implement Hermes session ingest

Files:

- Create: `r0b0tlabbra1n/ingest/hermes_sessions.py`
- Create: `r0b0tlabbra1n/memory/extract.py`
- Test: `tests/test_hermes_session_ingest.py`

Verification:

- Uses SQLite read-only URI.
- Preserves parent_session_id.
- Does not write to source DB.

### Task 7: Implement search/index

Files:

- Create: `r0b0tlabbra1n/index/sqlite_index.py`
- Create: `r0b0tlabbra1n/index/rank.py`
- Create: `r0b0tlabbra1n/memory/retrieve.py`
- Test: `tests/test_search.py`

Verification:

- Query returns cited page paths.
- Token budget honored.

### Task 8: Create Hermes skill

Files:

- Create: `hermes/skills/llm-wiki-brain/SKILL.md`
- Create: `hermes/skills/llm-wiki-brain/scripts/brain_search.py`
- Create: `hermes/skills/llm-wiki-brain/references/memory-policy.md`

Verification:

- `skill_view(name='llm-wiki-brain')` loads after install.
- Required paths/config documented.

### Task 9: Implement memory provider plugin

Files:

- Create: `hermes/plugins/memory/r0b0tlabbra1n/__init__.py`
- Create: `hermes/plugins/memory/r0b0tlabbra1n/plugin.yaml`
- Test: `tests/hermes/test_memory_provider_contract.py`

Verification:

- Satisfies Hermes `MemoryProvider` interface.
- `sync_turn` is non-blocking.
- Uses `hermes_home`.

### Task 10: Add evaluation harness

Files:

- Create: `r0b0tlabbra1n/evals/datasets.py`
- Create: `r0b0tlabbra1n/evals/metrics.py`
- Create: `r0b0tlabbra1n/evals/run.py`
- Create: `evals/gold/sample.jsonl`
- Test: `tests/test_evals.py`

Verification:

- Baseline report generated.
- Metrics include Recall@K, Precision@K, token budget, groundedness.

---

## 14. Files Likely to Change/Create

Inside project:

```text
/home/mr-r0b0t/LLM-Wiki-Obsidian-Hermes-r0b0tlab/README.md
/home/mr-r0b0t/LLM-Wiki-Obsidian-Hermes-r0b0tlab/pyproject.toml
/home/mr-r0b0t/LLM-Wiki-Obsidian-Hermes-r0b0tlab/r0b0tlabbra1n/**
/home/mr-r0b0t/LLM-Wiki-Obsidian-Hermes-r0b0tlab/hermes/**
/home/mr-r0b0t/LLM-Wiki-Obsidian-Hermes-r0b0tlab/templates/**
/home/mr-r0b0t/LLM-Wiki-Obsidian-Hermes-r0b0tlab/docs/**
/home/mr-r0b0t/LLM-Wiki-Obsidian-Hermes-r0b0tlab/tests/**
/home/mr-r0b0t/LLM-Wiki-Obsidian-Hermes-r0b0tlab/evals/**
```

Do not modify Hermes core initially. Ship integration as standalone skill/plugin assets. If upstream Hermes changes are later needed, propose a separate NousResearch PR.

---

## 15. Tests and Validation

### 15.1 Unit tests

- Frontmatter parse/validate.
- Wikilink parse/resolve.
- Secret scanner.
- Vault init idempotence.
- SQLite session ingest with synthetic DB.
- Search ranking.
- Context packet budgeting.
- Memory promotion policy.
- Provider interface compliance.

### 15.2 Integration tests

- Initialize fixture vault.
- Ingest synthetic Hermes session DB.
- Run lint.
- Rebuild index.
- Search for known facts.
- Generate dashboard.
- Run eval benchmark.

### 15.3 Hermes smoke tests

- Load skill.
- Run brain search script from skill.
- Activate memory provider in temp `HERMES_HOME`.
- Confirm prefetch returns safe context.
- Confirm no writes happen for subagent/cron contexts unless allowed.

### 15.4 Security tests

- Redact common token patterns.
- Block prompt-injection memory writes.
- Ensure `.env` values are never copied.
- Confirm raw source prompt injections do not become operating rules.

### 15.5 Performance tests

- 1k pages search latency.
- 10k pages search latency.
- index rebuild time.
- context packet token counts.

---

## 16. Risk Register

| ID | Risk | Likelihood | Impact | Mitigation | Contingency |
|---|---|---:|---:|---|---|
| R1 | Vault becomes a junk drawer of unreviewed agent output | Medium | High | Strict schema, lint, promotion rules, dashboards | Archive/rebuild from raw + manifests |
| R2 | Secrets leak into Markdown | Medium | Critical | Redaction before writes, secret scan in lint and tests | Quarantine file, rotate secret, add regression test |
| R3 | Retrieval over-fetches and bloats prompt | Medium | High | Token budgets, compact packets, citations only | Disable prefetch, use manual search |
| R4 | Memory provider writes noisy facts every turn | Medium | High | Auto-rich-write off by default, cron consolidation | Purge pending queue and rebuild semantic pages |
| R5 | `.hermes.md` hides existing project instructions | Medium | High | Installer detects existing context files and asks | Use non-invasive README pointer only |
| R6 | Graph extraction hallucinates relationships | Medium | Medium | Store confidence/provenance/review status | Treat graph as candidate index only |
| R7 | Embedding/index dependency makes install brittle | Medium | Medium | SQLite/FTS-only v1 baseline | Optional adapters later |
| R8 | Cron jobs recursively or noisily update memory | Low | High | Self-contained prompts, no cron recursion, local dry run | Pause/remove cron jobs |
| R9 | Evaluation is postponed and quality is unmeasured | Medium | High | Build eval harness by Phase 10 at latest, seed from fixtures | Block advanced retrieval until metrics exist |
| R10 | Standalone project drifts from Hermes upstream APIs | Medium | Medium | Pin docs reviewed, contract tests, optional plugin isolation | Compatibility matrix and version gating |

---

## 17. Assumptions and Constraints

### Assumptions

- Primary target is Hermes Agent running on Linux with local filesystem access.
- User wants a standalone GitHub repo under `r0b0tlab`, not a fork of Hermes Agent.
- Obsidian compatibility matters for human browsing and editing.
- Hermes built-in memory should remain compact.
- Current local Hermes repo/docs are representative of current Nous Research developer docs.
- Initial implementation can be local-only and open-source.

### Constraints

- Do not inject the whole vault into Hermes context.
- Do not write secrets to the vault.
- Do not write to Hermes `state.db`; read only.
- Do not modify Hermes core for v1.
- Maintain prompt-cache stability.
- Use profile-aware paths when integrating with Hermes.
- Cron jobs cannot ask clarifying questions.
- Subagents cannot interact with user; parent must verify external side effects.

---

## 18. Dependencies

| Dependency | Purpose | Required v1 | Notes |
|---|---|---:|---|
| Python 3.11+ | CLI/scripts/tests | Yes | Matches Hermes environment |
| SQLite / FTS5 | local index | Yes | stdlib sqlite3, verify FTS5 enabled |
| PyYAML or ruamel.yaml | frontmatter | Maybe | Can start with simple parser, but YAML lib better |
| pytest | tests | Yes | Development dependency |
| Obsidian | human UX | No | Vault works without app |
| Hermes Agent | native integration | Yes for Hermes mode | Skill/plugin/cron integration |
| Git | versioned vault/repo | Yes | Auditable changes |
| Embedding model/provider | semantic search | Optional | Add after FTS baseline |
| Postgres/PGLite/pgvector | advanced index | Optional | GBrain-inspired later phase |
| MCP SDK | MCP server | Optional | Later phase |

---

## 19. Communication Plan

| Stakeholder | Channel | Frequency | Content |
|---|---|---|---|
| User / r0b0tlab | CLI chat + Telegram if requested | Per phase | Summary, changed files, validation, blockers |
| Future Hermes agents | `START_HERE.md`, dashboards, project pages | Always | Orientation and current state |
| GitHub users | README, docs, issues | Release milestones | Setup, examples, limitations |
| Maintainers | CHANGELOG, eval reports | Per release | Quality metrics and compatibility |

Escalation:

- If secrets are detected: stop, report path/pattern, ask user before proceeding.
- If existing context files would be overridden: stop and ask.
- If eval regresses: block release until explained.

---

## 20. Change Management

- Every architecture change gets a decision record in `docs/decisions/` or vault `_agent/episodic/decisions/`.
- Every schema migration gets a migration note and test fixture.
- Every automated promotion rule must be documented in `docs/memory-policy.md`.
- Breaking changes require README upgrade notes.
- Integration with Hermes core APIs must include compatibility tests and documented Hermes version/commit.

---

## 21. Budget and Procurement

Budget: `$0.00 USD` for the initial local open-source implementation.

Initial implementation uses local filesystem, Python, SQLite, Git, Hermes, and Obsidian-compatible Markdown. No paid cloud services are required.

Procurement: Not applicable for v1. Optional future providers such as hosted embeddings, Postgres/Supabase, or managed memory APIs may have costs, but they are not required for the baseline design.

---

## 22. Glossary

- LLM Wiki: persistent, maintained Markdown knowledge base compiled by an LLM from raw sources.
- Obsidian: Markdown note application that supports wikilinks, graph view, and frontmatter workflows.
- Hermes Agent: Nous Research agent framework with tools, skills, memory, plugins, cron, gateway, and sessions.
- Hot memory: tiny always-injected curated memory.
- Warm memory: frequently used Markdown pages and dashboards read on demand.
- Cold memory: raw/session evidence retained for audit and reprocessing.
- Episodic memory: records of events and experiences.
- Semantic memory: stable facts, concepts, and current state.
- Procedural memory: workflows, skills, and how-to knowledge.
- Provenance: evidence trail for a claim or page.
- FTS5: SQLite full-text search engine.
- RRF: Reciprocal Rank Fusion, a method to combine rankings.
- MCP: Model Context Protocol, a standard tool/resource interface for agents.
- Memory provider plugin: Hermes plugin that can prefetch, sync, and expose memory tools.
- Context engine plugin: Hermes plugin that manages/compresses conversation context.

---

## 23. References

Primary sources reviewed:

- Karpathy LLM Wiki gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- garrytan/gbrain: https://github.com/garrytan/gbrain
- MemGPT paper: https://arxiv.org/abs/2310.08560
- Generative Agents paper: https://arxiv.org/abs/2304.03442
- Letta docs: https://docs.letta.com/
- Letta memory docs: https://docs.letta.com/letta-code/memory
- Mem0 overview: https://docs.mem0.ai/overview
- Mem0 memory types: https://docs.mem0.ai/core-concepts/memory-types
- Mem0 memory evaluation: https://docs.mem0.ai/core-concepts/memory-evaluation
- Zep Graphiti overview: https://help.getzep.com/graphiti/graphiti/overview
- LangGraph memory concepts: https://langchain-ai.github.io/langgraph/concepts/memory/
- Cognee docs: https://docs.cognee.ai/

Hermes local docs/code reviewed:

- `/home/mr-r0b0t/.hermes/hermes-agent/agent/memory_manager.py`
- `/home/mr-r0b0t/.hermes/hermes-agent/agent/memory_provider.py`
- `/home/mr-r0b0t/.hermes/hermes-agent/tools/memory_tool.py`
- `/home/mr-r0b0t/.hermes/hermes-agent/tools/session_search_tool.py`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/user-guide/features/memory.md`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/developer-guide/prompt-assembly.md`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/developer-guide/memory-provider-plugin.md`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/developer-guide/context-engine-plugin.md`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/developer-guide/context-compression-and-caching.md`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/developer-guide/session-storage.md`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/developer-guide/cron-internals.md`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/developer-guide/creating-skills.md`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/developer-guide/adding-tools.md`
- `/home/mr-r0b0t/.hermes/hermes-agent/website/docs/developer-guide/architecture.md`

---

## Immediate Next Step Recommendation

Do Phase 0 first: deep-clone/review GBrain and create the source dossier before writing code. The risk of premature implementation is high because the best design is a synthesis of LLM Wiki, GBrain, Hermes memory-provider constraints, and temporal graph/evaluation lessons. Once Phase 0 is complete, implement the v1 filesystem-only brain with lint/redaction before any automation.
