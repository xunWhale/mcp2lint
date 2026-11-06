"""Walk a tree of Python files and report v1 -> v2 MCP SDK incompatibilities."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

from mcp2lint.rules import (
    CAMEL_ATTRIBUTES,
    CONSTRUCTOR_MOVES,
    DEAD_IMPORTS,
    DEAD_TYPE_NAMES,
    ERROR,
    Rule,
)

SKIP_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules",
    "__pycache__", ".mypy_cache", ".pytest_cache", ".tox", "build", "dist",
    ".eggs", "site-packages",
}


@dataclass(frozen=True)
class Finding:
    """One concrete place the code will break, or behave differently."""

    path: Path
    line: int
    column: int
    rule: Rule
    snippet: str

    def as_dict(self, root: Path) -> dict:
        try:
            shown = str(self.path.relative_to(root))
        except ValueError:
            shown = str(self.path)
        return {
            "file": shown,
            "line": self.line,
            "column": self.column,
            "rule": self.rule.id,
            "severity": self.rule.severity,
            "message": self.rule.summary,
            "fix": self.rule.fix,
            "source": self.snippet,
        }


@dataclass
class Report:
    """Everything one run found."""

    findings: list[Finding] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.rule.severity == ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.rule.severity != ERROR]

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)


def iter_python_files(root: Path) -> Iterator[Path]:
    """Yield every Python file under ``root``, skipping the usual noise."""
    if root.is_file():
        if root.suffix == ".py":
            yield root
        return
    for path in sorted(root.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def _module_of(node: ast.ImportFrom) -> str:
    return ("." * node.level) + (node.module or "")


def _snippet(lines: list[str], lineno: int) -> str:
    if 1 <= lineno <= len(lines):
        return lines[lineno - 1].strip()
    return ""


def scan_source(source: str, path: Path) -> list[Finding]:
    """Scan one file's source text. Never raises on a syntax error."""
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    lines = source.splitlines()
    findings: list[Finding] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = _module_of(node)
            if node.level == 0 and module in DEAD_IMPORTS:
                findings.append(
                    Finding(
                        path=path,
                        line=node.lineno,
                        column=node.col_offset + 1,
                        rule=DEAD_IMPORTS[module],
                        snippet=_snippet(lines, node.lineno),
                    )
                )
            if node.level == 0 and module in {"mcp.types", "mcp"}:
                for alias in node.names:
                    if alias.name in DEAD_TYPE_NAMES:
                        findings.append(
                            Finding(
                                path=path,
                                line=node.lineno,
                                column=node.col_offset + 1,
                                rule=Rule(
                                    id="MCP010",
                                    summary=f"mcp.types.{alias.name} was removed in v2",
                                    fix=f"use {DEAD_TYPE_NAMES[alias.name]} instead",
                                ),
                                snippet=_snippet(lines, node.lineno),
                            )
                        )
                    if alias.name == "McpError":
                        findings.append(
                            Finding(
                                path=path,
                                line=node.lineno,
                                column=node.col_offset + 1,
                                rule=Rule(
                                    id="MCP011",
                                    summary="McpError was renamed to MCPError in v2",
                                    fix="from mcp import MCPError",
                                ),
                                snippet=_snippet(lines, node.lineno),
                            )
                        )

        if isinstance(node, ast.Attribute) and node.attr in CAMEL_ATTRIBUTES:
            snake = CAMEL_ATTRIBUTES[node.attr]
            findings.append(
                Finding(
                    path=path,
                    line=node.lineno,
                    column=node.col_offset + 1,
                    rule=Rule(
                        id="MCP020",
                        summary=(
                            f"field {node.attr} is {snake} in v2; the camelCase "
                            "attribute no longer exists"
                        ),
                        fix=f"rename .{node.attr} to .{snake}",
                    ),
                    snippet=_snippet(lines, node.lineno),
                )
            )

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"FastMCP", "MCPServer", "Server"}:
                for keyword in node.keywords:
                    if keyword.arg in CONSTRUCTOR_MOVES:
                        findings.append(
                            Finding(
                                path=path,
                                line=keyword.value.lineno,
                                column=keyword.value.col_offset + 1,
                                rule=Rule(
                                    id="MCP030",
                                    summary=(
                                        f"{keyword.arg}= on the server constructor "
                                        "is not a v2 parameter"
                                    ),
                                    fix=CONSTRUCTOR_MOVES[keyword.arg],
                                ),
                                snippet=_snippet(lines, keyword.value.lineno),
                            )
                        )

    findings.sort(key=lambda f: (f.line, f.column))
    return findings


def scan_paths(paths: Iterable[Path]) -> Report:
    """Scan every path given, collecting one report."""
    report = Report()
    for root in paths:
        root = Path(root)
        for path in iter_python_files(root):
            try:
                source = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for finding in scan_source(source, path):
                report.add(finding)
    return report
