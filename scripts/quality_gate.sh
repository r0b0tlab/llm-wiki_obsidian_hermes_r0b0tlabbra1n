#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/ruff check .
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest --cov=r0b0tlabbra1n --cov-report=term-missing --cov-fail-under=80
rm -rf /tmp/r0b0tlabbra1n-qg-vault
.venv/bin/brain init --vault /tmp/r0b0tlabbra1n-qg-vault
.venv/bin/brain lint --vault /tmp/r0b0tlabbra1n-qg-vault
.venv/bin/brain build-index --vault /tmp/r0b0tlabbra1n-qg-vault
.venv/bin/brain search "Hermes memory" --vault /tmp/r0b0tlabbra1n-qg-vault --json >/tmp/r0b0tlabbra1n-search.json
.venv/bin/brain drift-check --vault /tmp/r0b0tlabbra1n-qg-vault
.venv/bin/brain eval --vault tests/fixtures/eval-vault --gold evals/gold_queries.yaml
