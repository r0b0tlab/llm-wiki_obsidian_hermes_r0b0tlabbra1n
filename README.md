# llm-wiki_obsidian_hermes_r0b0tlabbra1n

> A filesystem-first LLM-Wiki + Obsidian + Hermes Agent memory system.
> Markdown is source of truth. Indexes are rebuildable acceleration layers.
> Built by @mr-r0b0t on X — r0b0tlab.

## What This Is

r0b0tlabbra1n is a local, auditable agent-memory system for Hermes and other CLI agents. It keeps durable knowledge in human-editable Markdown, uses Obsidian wikilinks for navigation, and builds deterministic local indexes for retrieval, graph/backlinks, source-hash drift checks, and evaluation.

It is designed to compound knowledge better than normal chat history or one-shot RAG:

- Humans can read, edit, diff, and correct everything.
- Agents can lint, search, ingest sessions, and maintain project state.
- Indexes are disposable: rebuild from Markdown at any time.
- Security checks block secrets from entering the vault write path.
- Retrieval quality is measured with a gold-query eval harness.

## Feature Status

| Capability | Status | Command / Path |
|---|---|---|
| Vault initialization | Implemented | `brain init --vault ~/my-brain` |
| Frontmatter, wikilink, secret linting | Implemented | `brain lint --vault ~/my-brain` |
| SQLite FTS5 search with BM25 ranking | Implemented | `brain build-index`, `brain search` |
| Weighted, tier-aware context packets | Implemented | `brain search "query" --context` |
| Source hash manifest and drift detection | Implemented | `brain drift-check` |
| Link graph and backlinks | Implemented | `brain graph`, `brain backlinks` |
| Retrieval eval harness | Implemented | `brain eval --gold evals/gold_queries.yaml` |
| Read-only Hermes session ingest | Implemented | `brain ingest-sessions --hermes-home ~/.hermes` |
| Promotion candidate generation | Implemented | `brain promote-candidates` |
| Hermes skill pack | Implemented | `hermes/skills/llm-wiki-brain/` |
| Runnable heartbeat/audit scripts | Implemented | `hermes/cron_scripts/` |
| Minimal MCP/agent JSON facade | Implemented | `mcp_server/brain_mcp.py` |
| Optional vector embeddings | Roadmap | not required for local deterministic v0.1 |
| Advanced temporal graph DB | Roadmap | current graph is local JSON wikilink graph |

## Quickstart

```bash
git clone https://github.com/r0b0tlab/llm-wiki_obsidian_hermes_r0b0tlabbra1n ~/brain-code
cd ~/brain-code
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"

.venv/bin/brain init --vault ~/my-brain
.venv/bin/brain lint --vault ~/my-brain
.venv/bin/brain build-index --vault ~/my-brain
.venv/bin/brain search "how to deploy vLLM" --vault ~/my-brain --context
```

## Core CLI

```bash
brain init --vault ~/my-brain
brain lint --vault ~/my-brain
brain build-index --vault ~/my-brain
brain search "Hermes memory" --vault ~/my-brain --json
brain search "Hermes memory" --vault ~/my-brain --context --budget 2000
brain ingest-sessions --hermes-home ~/.hermes --vault ~/my-brain
brain graph --vault ~/my-brain --json
brain backlinks _agent/operating-rules --vault ~/my-brain
brain drift-check --vault ~/my-brain
brain eval --vault tests/fixtures/eval-vault --gold evals/gold_queries.yaml
brain promote-candidates --vault ~/my-brain --json
```

## Architecture

```text
Hermes / CLI agents
  ├─ built-in compact memory pointers
  ├─ llm-wiki-brain skill
  ├─ cron heartbeat/audit scripts
  └─ optional MCP/JSON facade
        ↓
r0b0tlabbra1n package
  ├─ vault initialization and safe writes
  ├─ lint: frontmatter + wikilinks + secrets
  ├─ read-only Hermes session ingest
  ├─ retrieval: FTS5 BM25 + tier/confidence/recency weighting
  ├─ eval harness: top-1, top-3, MRR
  ├─ graph index: wikilinks + backlinks JSON
  └─ source hash manifest + drift check
        ↓
Markdown / Obsidian vault
  ├─ _agent/ semantic and episodic memory
  ├─ projects/, sessions/, entities/, concepts/, procedures/
  ├─ raw/ untrusted source evidence
  └─ _meta/ rebuildable indexes and manifests
```

## Security Model

- Secret scanner covers common HF, OpenAI, Anthropic, GitHub, JWT, AWS, AgentMail, Google, and env assignment patterns.
- `safe_write_page` and `append_to_page` scan content before writing.
- Session ingest opens Hermes `state.db` with SQLite `mode=ro`.
- Raw transcripts are treated as untrusted evidence and excluded from default indexing.
- Wikilink resolution refuses traversal outside the vault.

## Quality Gates

```bash
bash scripts/quality_gate.sh
.venv/bin/ruff check .
.venv/bin/python -m pytest -q
.venv/bin/brain eval --vault tests/fixtures/eval-vault --gold evals/gold_queries.yaml
```

CI runs ruff, pytest, CLI smoke, and retrieval eval smoke on Python 3.11 and 3.12.

## Credits

@mr-r0b0t on X — r0b0tlab

Inspired by Karpathy's LLM Wiki, garrytan/gbrain, MemGPT/Letta, Zep/Graphiti, and Obsidian-first personal knowledge management.

## License

MIT
