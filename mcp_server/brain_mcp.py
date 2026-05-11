#!/usr/bin/env python3
"""Minimal stdio-friendly brain tool facade.

This is intentionally dependency-light: it exposes CLI-callable JSON operations that
can be wrapped by Hermes native MCP or other agents.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from r0b0tlabbra1n.evals.retrieval_eval import evaluate
from r0b0tlabbra1n.index.sqlite_index import BrainIndex
from r0b0tlabbra1n.memory.retrieve import retrieve
from r0b0tlabbra1n.vault.lint import lint_vault


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("--vault", type=Path, required=True)
    s.add_argument("query")
    lint_parser = sub.add_parser("lint")
    lint_parser.add_argument("--vault", type=Path, required=True)
    e = sub.add_parser("eval")
    e.add_argument("--vault", type=Path, required=True)
    e.add_argument("--gold", type=Path, required=True)
    args = p.parse_args()
    if args.cmd == "search":
        print(json.dumps(retrieve(BrainIndex(args.vault), args.query), indent=2))
    elif args.cmd == "lint":
        print(json.dumps(lint_vault(args.vault), indent=2))
    elif args.cmd == "eval":
        print(json.dumps(evaluate(args.vault, args.gold), indent=2))


if __name__ == "__main__":
    main()
