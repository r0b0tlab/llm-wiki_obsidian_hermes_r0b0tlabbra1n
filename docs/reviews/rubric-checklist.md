# r0b0tlabbra1n Rubric Checklist

| Category | Points | Evidence command/path | Status |
|---|---:|---|---|
| Vision / Product Fit | 10 | README.md, docs/architecture.md | implemented |
| Architecture / System Design | 15 | docs/architecture.md, r0b0tlabbra1n/index, r0b0tlabbra1n/vault | implemented |
| Core Implementation Correctness | 15 | pytest, CLI smoke tests | implemented |
| Retrieval and Memory Quality | 15 | brain eval --vault tests/fixtures/eval-vault --gold evals/gold_queries.yaml | implemented |
| Security / Privacy / Safety | 10 | tests/test_secret_scan.py, tests/test_quality_hardening.py | implemented |
| Testing / Evals / Quality Gates | 15 | ruff, pytest, scripts/quality_gate.sh, .github/workflows/ci.yml | implemented |
| Hermes / Obsidian Integration | 10 | hermes/skills, hermes/cron_scripts, mcp_server | implemented |
| Docs / UX / Packaging / Operability | 10 | README.md, docs/tutorial.md, docs/release-checklist.md | implemented |
