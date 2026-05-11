"""Tests for the MCP/JSON facade contract."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_mcp_manifest_declares_tools():
    manifest = json.loads(Path("mcp_server/manifest.json").read_text(encoding="utf-8"))
    tool_names = {tool["name"] for tool in manifest["tools"]}
    assert {"brain_search", "brain_lint", "brain_eval"}.issubset(tool_names)
    assert manifest["transport"] == "stdio-json"


def test_mcp_rpc_initialize_and_tools_list():
    proc = subprocess.run(
        [".venv/bin/python", "mcp_server/brain_mcp.py", "serve"],
        input=(
            '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n'
            '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n'
        ),
        text=True,
        capture_output=True,
        check=True,
    )
    lines = [json.loads(line) for line in proc.stdout.splitlines()]
    assert lines[0]["result"]["serverInfo"]["name"] == "r0b0tlabbra1n-brain"
    assert any(tool["name"] == "brain_search" for tool in lines[1]["result"]["tools"])


def test_mcp_rpc_tool_call_search():
    proc = subprocess.run(
        [".venv/bin/python", "mcp_server/brain_mcp.py", "serve"],
        input=json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "brain_search",
                    "arguments": {
                        "vault": "tests/fixtures/eval-vault",
                        "query": "Hermes operating rules",
                    },
                },
            }
        )
        + "\n",
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    content = payload["result"]["content"][0]["text"]
    assert "_agent/operating-rules.md" in content
