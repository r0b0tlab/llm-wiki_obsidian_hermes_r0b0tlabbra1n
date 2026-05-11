# Brain MCP Facade

`brain_mcp.py` is a dependency-light MCP-style stdio JSON-RPC server for agents that want to query a r0b0tlabbra1n vault without shelling out to the `brain` CLI directly.

Manifest: `mcp_server/manifest.json`

Start the server:

```bash
python mcp_server/brain_mcp.py serve
```

Supported JSON-RPC methods:

- `initialize`
- `tools/list`
- `tools/call`

Declared tools:

- `brain_search` — arguments: `vault`, `query`, optional `budget`
- `brain_lint` — arguments: `vault`
- `brain_eval` — arguments: `vault`, `gold`

Example request:

```json
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"brain_search","arguments":{"vault":"tests/fixtures/eval-vault","query":"Hermes operating rules"}}}
```

The script also keeps direct shell subcommands for simple use:

```bash
python mcp_server/brain_mcp.py search --vault tests/fixtures/eval-vault "Hermes operating rules"
python mcp_server/brain_mcp.py lint --vault tests/fixtures/eval-vault
python mcp_server/brain_mcp.py eval --vault tests/fixtures/eval-vault --gold evals/gold_queries.yaml
```
