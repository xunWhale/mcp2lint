# mcp2lint

Find the lines that break when a Python MCP server moves from SDK **v1** to **v2** — before you run it and read a traceback.

```console
$ mcp2lint ./my-server
src/my_server/server.py:4:1: error [MCP001] mcp.server.fastmcp was renamed to mcp.server.mcpserver in v2
    from mcp.server.fastmcp import FastMCP
    fix: from mcp.server.mcpserver import MCPServer as FastMCP
src/my_server/http.py:32:10: error [MCP030] port= on the server constructor is not a v2 parameter
    port=int(os.environ.get("MCP_PORT", "8331")),
    fix: pass it to mcp.run(transport=..., port=...) instead
2 error(s), 0 warning(s)
```

## Why this exists

MCP SDK v2 renamed `mcp.server.fastmcp` to `mcp.server.mcpserver`, moved every pydantic field from camelCase to snake_case, and took the transport settings off the server constructor. Projects that pin `mcp` loosely and don't bound it below 2 start failing at import time:

```
ModuleNotFoundError: No module named 'mcp.server.fastmcp'
```

That single traceback was open in **188 issues across GitHub** when this tool was written, 40 of them filed in the previous seven days, most with no reply. The traceback names one line. The other four fixes are still waiting behind it.

`mcp2lint` reads the AST, reports every v1-only construct with a file, line, and the v2 replacement, and exits non-zero so CI can catch a dependency bump before a user does.

## Install

Not on PyPI yet:

```bash
pip install "mcp2lint @ git+https://github.com/xunWhale/mcp2lint"
```

## Usage

```bash
mcp2lint .                       # scan the current directory
mcp2lint src/ server.py          # scan specific paths
mcp2lint . --errors-only         # skip warnings
mcp2lint . --format json         # machine-readable, for CI
```

Exit codes: `0` clean, `1` at least one error, `2` bad path.

## What it checks

| Rule | Finds |
| :--- | :--- |
| `MCP001` | `from mcp.server.fastmcp import FastMCP` (module renamed to `mcp.server.mcpserver`) |
| `MCP002` | `from mcp.shared.version import ...` (moved to `mcp.types.version`) |
| `MCP003` | `from mcp.shared.context import RequestContext` (split into client/server contexts) |
| `MCP004` | `streamablehttp_client` (removed; use `streamable_http_client`) |
| `MCP010` | removed `mcp.types` names: `Content`, `ResourceReference`, `*RequestType`, ... |
| `MCP011` | `McpError` (renamed `MCPError`) |
| `MCP020` | camelCase attribute access: `.inputSchema`, `.isError`, `.mimeType`, `.nextCursor`, ... |
| `MCP030` | `host=` / `port=` / `stateless_http=` left on the server constructor |

Every rule comes from the [official v1 to v2 migration guide](https://py.sdk.modelcontextprotocol.io/v2/migration/). `MCP020` covers the attributes listed under "Field names changed from camelCase to snake_case"; the models still accept camelCase as constructor kwargs, so those are not reported.

The scanner reads only the AST. It never imports your code, so it is safe to point at a repository you have not installed.

## What it does not do

- No autofix. Renaming `FastMCP` can collide with a local name, and guessing is worse than telling you.
- No behaviour warnings. "Sync handlers now run on a worker thread" and "`model_dump()` needs `by_alias=True`" are real v2 changes, but not detectable from one file, so they are out of scope rather than half-detected.
- No dependency check. It does not read your `pyproject.toml` to see whether `mcp` is already bounded below 2.

## Verification

The rules were checked against three real repositories that each have an open `ModuleNotFoundError: No module named 'mcp.server.fastmcp'` issue:

| Repository | Findings |
| :--- | :--- |
| `gammaremover/gamma-watermark-remover-mcp` | 5 (2x `MCP001`, 3x `MCP030`) |
| `jelmervdm/sophos-firewall-mcp` | 3 (3x `MCP001`) |
| `zvec-ai/zvec-mcp-server` | 1 (1x `MCP001`) |

All three reproduce the reported crash. `mcp2lint` named the import line plus the constructor kwargs their issues never mentioned.

## Development

```bash
git clone https://github.com/xunWhale/mcp2lint && cd mcp2lint
python -m venv .venv && . .venv/bin/activate
pip install -e . pytest
pytest -q
```

Zero runtime dependencies. Python 3.9+.

## License

MIT

![CI](https://github.com/xunWhale/mcp2lint/actions/workflows/ci.yml/badge.svg)
