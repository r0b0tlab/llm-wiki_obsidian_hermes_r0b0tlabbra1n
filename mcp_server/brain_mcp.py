#!/usr/bin/env python3
"""Dependency-light stdio JSON-RPC brain server and CLI facade.

The `serve` subcommand implements the MCP-style methods needed by local agents:
`initialize`, `tools/list`, and `tools/call` for brain_search, brain_lint,
and brain_eval. The legacy subcommands remain useful for shell callers.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from r0b0tlabbra1n.evals.retrieval_eval import evaluate
from r0b0tlabbra1n.index.sqlite_index import BrainIndex
from r0b0tlabbra1n.memory.retrieve import retrieve
from r0b0tlabbra1n.vault.lint import lint_vault

TOOLS = [
    {
        "name": "brain_search",
        "description": "Search a r0b0tlabbra1n vault and return ranked memory results.",
        "inputSchema": {
            "type": "object",
            "required": ["vault", "query"],
            "properties": {
                "vault": {"type": "string"},
                "query": {"type": "string"},
                "budget": {"type": "integer", "default": 2000},
            },
        },
    },
    {
        "name": "brain_lint",
        "description": "Lint a vault for frontmatter, wikilink, and secret issues.",
        "inputSchema": {
            "type": "object",
            "required": ["vault"],
            "properties": {"vault": {"type": "string"}},
        },
    },
    {
        "name": "brain_eval",
        "description": "Run retrieval evaluation against a gold query YAML file.",
        "inputSchema": {
            "type": "object",
            "required": ["vault", "gold"],
            "properties": {"vault": {"type": "string"}, "gold": {"type": "string"}},
        },
    },
]


def _tool_result(value: Any) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(value, indent=2, sort_keys=True)}]}


def call_tool(name: str, arguments: dict[str, Any]) -> dict:
    """Execute a declared brain tool and return MCP-style content."""
    if name == "brain_search":
        vault = Path(arguments["vault"])
        query = str(arguments["query"])
        budget = int(arguments.get("budget", 2000))
        return _tool_result(retrieve(BrainIndex(vault), query, budget=budget))
    if name == "brain_lint":
        return _tool_result(lint_vault(Path(arguments["vault"])))
    if name == "brain_eval":
        return _tool_result(evaluate(Path(arguments["vault"]), Path(arguments["gold"])))
    raise ValueError(f"Unknown tool: {name}")


def handle_rpc(request: dict[str, Any]) -> dict[str, Any] | None:
    """Handle one JSON-RPC request."""
    method = request.get("method")
    request_id = request.get("id")
    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "r0b0tlabbra1n-brain", "version": "0.1.0"},
                "capabilities": {"tools": {}},
            }
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            params = request.get("params") or {}
            result = call_tool(params["name"], params.get("arguments") or {})
        elif method == "notifications/initialized":
            return None
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except Exception as exc:  # pragma: no cover - defensive JSON-RPC boundary
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32000, "message": str(exc)},
        }


def serve() -> None:
    """Read newline-delimited JSON-RPC from stdin and write responses to stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        response = handle_rpc(json.loads(line))
        if response is not None:
            print(json.dumps(response), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("serve")
    search = sub.add_parser("search")
    search.add_argument("--vault", type=Path, required=True)
    search.add_argument("query")
    lint_parser = sub.add_parser("lint")
    lint_parser.add_argument("--vault", type=Path, required=True)
    eval_parser = sub.add_parser("eval")
    eval_parser.add_argument("--vault", type=Path, required=True)
    eval_parser.add_argument("--gold", type=Path, required=True)
    args = parser.parse_args()
    if args.cmd == "serve":
        serve()
    elif args.cmd == "search":
        print(json.dumps(retrieve(BrainIndex(args.vault), args.query), indent=2))
    elif args.cmd == "lint":
        print(json.dumps(lint_vault(args.vault), indent=2))
    elif args.cmd == "eval":
        print(json.dumps(evaluate(args.vault, args.gold), indent=2))


if __name__ == "__main__":
    main()
