#!/usr/bin/env python3
"""Runnable brain heartbeat: lint, index, drift check, eval smoke."""

from __future__ import annotations

import argparse
from pathlib import Path

from r0b0tlabbra1n.evals.retrieval_eval import evaluate, format_report
from r0b0tlabbra1n.index.graph_index import build_graph
from r0b0tlabbra1n.index.sqlite_index import BrainIndex
from r0b0tlabbra1n.vault.hashes import check_drift
from r0b0tlabbra1n.vault.lint import lint_vault


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, required=True)
    parser.add_argument("--gold", type=Path, default=Path("evals/gold_queries.yaml"))
    args = parser.parse_args()
    issues = lint_vault(args.vault)
    errors = [i for i in issues if i["level"] == "ERROR"]
    count = BrainIndex(args.vault).rebuild()
    build_graph(args.vault)
    drift = check_drift(args.vault)
    print(f"Brain heartbeat: indexed={count} errors={len(errors)} drift_clean={drift['clean']}")
    if args.gold.exists():
        print(format_report(evaluate(args.vault, args.gold)))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
