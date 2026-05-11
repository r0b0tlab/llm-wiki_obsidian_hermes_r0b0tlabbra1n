# r0b0tlabbra1n Holistic Grade

Date: 2026-05-11 18:07 CDT
Reviewer: Hermes Agent / gpt-5.5
Repo: /home/mr-r0b0t/LLM-Wiki-Obsidian-Hermes-r0b0tlab

## Overall Score

62 / 100

Confidence: high for current repo state. Evidence includes source inspection, docs/claim comparison, pytest, ruff, CLI smoke tests, and a small adversarial vault pass.

Verdict: credible v0.1 research/prototype skeleton, not yet a production-grade or fully honest public artifact. Publishable only if README/docs clearly label future components and fix the command mismatch. Do not market it as “best” or “world-class” yet.

## Category Scores

| Category | Score | Max | Rationale |
|---|---:|---:|---|
| Vision / Product Fit | 8 | 10 | Strong problem framing: filesystem-first, Obsidian-readable, Hermes-friendly memory that compounds. Deductions for overclaiming relative to implementation. |
| Architecture / System Design | 11 | 15 | Good L1/L2/L3/L4 model, memory type separation, Markdown source of truth, rebuildable FTS. Deductions for docs describing plugin/MCP/evals/embeddings/source-hash paths that are future or empty. |
| Core Implementation Correctness | 11 | 15 | init/lint/build-index/search/ingest work; 36 tests pass; FTS5 standalone table is the right call. Deductions for CLI/lint UX, FTS quote edge case, shallow ingest summaries, and partial link/backlink semantics. |
| Retrieval and Memory Quality | 5 | 15 | Basic tier-aware FTS works, but score is always 0.0, no meaningful ranking, no recency/importance/provenance weighting, heuristic extraction only, no eval harness. |
| Security / Privacy / Safety | 7 | 10 | Secret scanner exists and `safe_write_page` blocks secrets; read-only session ingest. Deductions: `append_to_page` bypasses secret scan, raw prompt-injection handling is docs-only, no broader path/write sandbox. |
| Testing / Evals / Quality Gates | 7 | 15 | 36 pytest tests pass and cover main modules. Ruff fails with 11 issues. No CI, no coverage gate, no retrieval eval/gold set, no realistic session fixtures beyond unit-ish cases. |
| Hermes / Obsidian Integration | 7 | 10 | Useful Hermes skill, cron prompt docs, vault templates, and current machine wiki pattern. Deductions: no actual Hermes provider plugin, empty MCP server, empty evals, cron wiring is prompt-level not operational. |
| Docs / UX / Packaging / Operability | 6 | 10 | README is clear and branded; package installs locally. Deductions: README overclaims, `brain index build` mismatch, clean-machine setup should use venv, some dirs claimed but empty. |

Total: 62 / 100

## Objective Checks Run

```text
.venv/bin/python -m pytest -q
=> 36 passed in 0.24s

.venv/bin/ruff check .
=> 11 errors
   - unsorted imports
   - unused imports
   - unused local variable
   - 2 line length violations

.venv/bin/brain --help
=> commands: build-index, ingest-sessions, init, lint, search

brain init/lint/build-index/search smoke test on /tmp/r0b0tlabbra1n-review-vault
=> init succeeded
=> lint produced INFO orphan pages only, but command exits nonzero because any issue triggers sys.exit(1)
=> build-index indexed 21 pages
=> search returned JSON results, all score=0.0
```

Repo size quick count excluding .git/.venv/caches:

```text
51 files
32 Python files / 2341 lines
10 Markdown files / 2737 lines
1 TOML file / 59 lines
```

## Claim vs Reality

| Feature / Claim | Status | Evidence |
|---|---|---|
| Markdown source of truth | Implemented | Vault templates and index rebuild from .md files exist. |
| Vault init/templates | Implemented | `brain init --vault ...` works. |
| Frontmatter parsing/validation | Implemented | Models/frontmatter/lint/tests exist. |
| Wikilink extraction/broken-link lint | Implemented, partial | Extraction and basic broken link checks exist; backlink/graph is in-memory only and path semantics are limited. |
| SQLite FTS5 search | Implemented | `BrainIndex` standalone FTS5 table; smoke test works. |
| Search ranking | Partial / weak | `score` hardcoded to 0.0; FTS result order is not exposed as meaningful rank. |
| Token-budgeted retrieval | Partial | Rough snippet budget truncation exists; no full context packet CLI output by default. |
| Session ingest | Implemented, shallow | Reads state.db with `mode=ro`, idempotent manifest; summaries are first user messages, not distilled memory. |
| Secret scanning | Implemented, partial enforcement | Scanner and tests exist; `safe_write_page` blocks, `append_to_page` bypasses. |
| L1/L2/L3/L4 tier model | Implemented in schema/docs/models, partial behavior | Tiers exist and retrieval can prefer warm/cold; lifecycle automation is not real. |
| Promotion/demotion pipeline | Partial / placeholder | Heuristic `extract_facts`; no real corroboration engine. |
| Embeddings | Documented/future only | Optional deps declared; no vector index implementation. |
| Graph index / temporal graph | Documented/future only | Empty/limited link graph helper; no persisted graph index. |
| MCP server | Misleading if presented as real | `mcp_server/` exists but contains no files. |
| Evals/gold sets | Misleading if presented as real | `evals/` exists but contains no files. |
| Hermes memory provider plugin | Documented-only / absent | README architecture mentions plugin; no plugin implementation found. |
| Cron automation | Partial | Prompt docs exist; no installed/scheduled job or robust script. |
| Source hash drift detection | Documented/field-only | `source_hash` field exists; no drift checker observed. |

## Adversarial Checks

A temporary vault test found:

```text
empty_lint_levels: ['INFO']
malformed frontmatter: WARNING Missing or invalid frontmatter
secret in markdown: lint detects it
safe_write_page with GitHub-like token: ValueError, blocked
append_to_page with GitHub-like token: writes successfully, bypassing scanner
traversal wikilink ../../../etc/passwd: reported as broken, not resolved outside vault
search empty query: ok, 0 results
search 'Hermes AND memory': ok
search '"unterminated': OperationalError unterminated string
search 'foo:bar': ok, 0 results
search unicode + Hermes: ok
```

The FTS query builder protects many cases but does not escape embedded quotes.

## P0 / P1 / P2 Gaps

### P0 before strong public claims

1. Fix README honesty.
   - Replace “best” with “v0.1 prototype” or similar.
   - Split implemented-now vs planned-next.
   - Mark embeddings, graph, plugin, MCP, eval harness, temporal graph, source drift, and cron automation as future unless implemented.

2. Fix README command mismatch.
   - README table says `brain index build`; CLI is `brain build-index`.

3. Fix ruff.
   - 11 current failures; most are mechanical.

4. Fix FTS query escaping for embedded double quotes.
   - `"unterminated` currently causes sqlite OperationalError.

5. Secret scan every write path.
   - `append_to_page` must scan, or be renamed/guarded as unsafe.

### P1 to make it a genuinely strong v0.1

1. Add real ranking.
   - Use `bm25(pages_fts)` and return nonzero scores.
   - Sort by rank plus tier/recency/confidence.

2. Add integration tests for the actual CLI via Click runner or subprocess.
   - Include lint exit-code behavior.

3. Improve `brain lint` exit semantics.
   - INFO-only orphan pages should not make the process fail.
   - Exit nonzero only for ERROR, maybe optionally WARNING with `--strict`.

4. Add a small eval harness.
   - 10-20 gold queries over a fixture vault.
   - Measure expected page in top-k, answer support, and token budget behavior.

5. Improve session ingest.
   - Store richer summaries, decisions, failures, commands, and provenance.
   - Handle unexpected Hermes schema more gracefully.

6. Add source-hash drift checker if docs keep promising it.

### P2 polish

1. Add clean-machine install docs using venv.
2. Add GitHub Actions CI: pytest, ruff, maybe coverage.
3. Add examples/tutorial vault.
4. Add coverage report.
5. Add operator docs for scheduled heartbeat/audit.
6. Either implement or remove empty `mcp_server/` and `evals/` directories from marketed architecture.

## Bottom Line

This is a good foundation and the idea is directionally right. The architecture is better than the implementation maturity right now.

As code: useful, small, test-passing prototype.
As product/research artifact: promising but overclaims.
As a public “best filesystem-first memory system”: not yet.

Score stands at 62/100. With README honesty, ruff fix, FTS escaping, append secret-scan enforcement, basic BM25 ranking, and a tiny retrieval eval, it can plausibly move into the low/mid 70s quickly.
