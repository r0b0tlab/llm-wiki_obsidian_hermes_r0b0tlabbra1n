#!/usr/bin/env python3
"""Brain search script — callable from Hermes skill context."""

import sys
from pathlib import Path

from r0b0tlabbra1n.index.sqlite_index import BrainIndex
from r0b0tlabbra1n.memory.retrieve import retrieve


def main():
    if len(sys.argv) < 3:
        print("Usage: brain_search.py <vault_path> <query> [budget]", file=sys.stderr)
        sys.exit(1)

    vault = Path(sys.argv[1])
    query = sys.argv[2]
    budget = int(sys.argv[3]) if len(sys.argv) > 3 else 2000

    if not vault.exists():
        print(f"Vault not found: {vault}", file=sys.stderr)
        sys.exit(1)

    index = BrainIndex(vault)
    results = retrieve(index, query, budget=budget)

    for r in results:
        print(f"  {r['path']} ({r.get('title', 'N/A')})")
        if r.get("snippet"):
            print(f"    {r['snippet']}")
        print()


if __name__ == "__main__":
    main()
