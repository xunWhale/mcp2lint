"""Command line entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mcp2lint import __version__
from mcp2lint.scan import scan_paths


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mcp2lint",
        description=(
            "Find code that breaks when a project moves from the MCP Python "
            "SDK v1 to v2. Exit code 1 means errors were found."
        ),
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Files or directories to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--errors-only",
        action="store_true",
        help="Hide warnings; only show things that will actually break",
    )
    parser.add_argument("--version", action="version", version=f"mcp2lint {__version__}")
    return parser


def _render_text(findings, root: Path, errors_only: bool) -> str:
    lines = []
    for finding in findings:
        if errors_only and finding.rule.severity != "error":
            continue
        item = finding.as_dict(root)
        tag = "error" if item["severity"] == "error" else "warn "
        lines.append(
            f"{item['file']}:{item['line']}:{item['column']}: {tag} [{item['rule']}] "
            f"{item['message']}\n    {item['source']}\n    fix: {item['fix']}"
        )
    return "\n".join(lines)


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    paths = [Path(p) for p in args.paths]
    root = paths[0] if len(paths) == 1 and paths[0].is_dir() else Path.cwd()

    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        print(f"mcp2lint: no such path: {', '.join(missing)}", file=sys.stderr)
        return 2

    report = scan_paths(paths)

    if args.format == "json":
        payload = {
            "errors": len(report.errors),
            "warnings": len(report.warnings),
            "findings": [
                f.as_dict(root)
                for f in report.findings
                if not (args.errors_only and f.rule.severity != "error")
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        rendered = _render_text(report.findings, root, args.errors_only)
        if rendered:
            print(rendered)
        summary = f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)"
        print(summary if rendered else f"No v1-only MCP API found. {summary}")

    return 1 if report.errors else 0
