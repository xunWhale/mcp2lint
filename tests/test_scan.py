from __future__ import annotations

from pathlib import Path

from mcp2lint.scan import scan_paths, scan_source


def _write(tmp_path: Path, name: str, body: str) -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def test_detects_renamed_fastmcp_import(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "server.py",
        "from mcp.server.fastmcp import FastMCP\n\nmcp = FastMCP('x')\n",
    )
    findings = scan_source(path.read_text(), path)
    assert [f.rule.id for f in findings] == ["MCP001"]
    assert findings[0].line == 1


def test_detects_camel_case_attribute(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "client.py",
        "async def go(session):\n"
        "    tools = await session.list_tools()\n"
        "    return tools.tools[0].inputSchema\n",
    )
    findings = scan_source(path.read_text(), path)
    assert [f.rule.id for f in findings] == ["MCP020"]
    assert "input_schema" in findings[0].rule.fix


def test_detects_transport_kwargs_on_constructor(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "http.py",
        "from mcp.server.mcpserver import MCPServer\n"
        "mcp = MCPServer('x', host='0.0.0.0', port=8000)\n",
    )
    findings = scan_source(path.read_text(), path)
    assert sorted(f.rule.id for f in findings) == ["MCP030", "MCP030"]


def test_detects_removed_type_and_error(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "types_use.py",
        "from mcp.types import Content\nfrom mcp import McpError\n",
    )
    findings = scan_source(path.read_text(), path)
    assert sorted(f.rule.id for f in findings) == ["MCP010", "MCP011"]


def test_clean_v2_file_reports_nothing(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "clean.py",
        "from mcp.server.mcpserver import MCPServer\n"
        "from mcp.types import TextContent\n\n"
        "mcp = MCPServer('x')\n\n\n"
        "@mcp.tool()\n"
        "def hello() -> list:\n"
        "    return [TextContent(type='text', text='hi')]\n",
    )
    findings = scan_source(path.read_text(), path)
    assert findings == []


def test_syntax_error_is_skipped(tmp_path: Path) -> None:
    path = _write(tmp_path, "broken.py", "def oops(:\n")
    assert scan_source(path.read_text(), path) == []


def test_scan_paths_walks_a_tree(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    _write(package, "a.py", "from mcp.server.fastmcp import FastMCP\n")
    _write(package, "b.py", "from mcp.server.mcpserver import MCPServer\n")
    report = scan_paths([tmp_path])
    assert len(report.errors) == 1
    assert report.errors[0].path.name == "a.py"


def test_skips_virtualenv_directories(tmp_path: Path) -> None:
    venv = tmp_path / ".venv" / "lib"
    venv.mkdir(parents=True)
    _write(venv, "vendored.py", "from mcp.server.fastmcp import FastMCP\n")
    report = scan_paths([tmp_path])
    assert report.findings == []


def test_v2_streamable_http_client_is_not_flagged(tmp_path: Path) -> None:
    """The v2 name has underscores; only the v1 alias was removed."""
    path = _write(
        tmp_path,
        "ok.py",
        "from mcp.client.streamable_http import streamable_http_client\n",
    )
    assert scan_source(path.read_text(), path) == []


def test_removed_name_in_a_live_module_is_flagged(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "old.py",
        "from mcp.client.streamable_http import streamablehttp_client\n",
    )
    findings = scan_source(path.read_text(), path)
    assert [f.rule.id for f in findings] == ["MCP004"]


def test_other_names_in_shared_context_are_not_flagged(tmp_path: Path) -> None:
    """mcp.shared.context still exports BaseContext; only RequestContext moved."""
    path = _write(
        tmp_path,
        "ctx.py",
        "from mcp.shared.context import BaseContext\n",
    )
    assert scan_source(path.read_text(), path) == []


def test_request_context_is_flagged_wherever_it_is_imported(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "ctx_old.py",
        "from mcp.shared.context import RequestContext\n",
    )
    findings = scan_source(path.read_text(), path)
    assert [f.rule.id for f in findings] == ["MCP003"]
