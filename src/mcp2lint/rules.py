"""Every breaking v1 -> v2 change we know how to spot, in one table.

Sourced from the official migration guide:
https://py.sdk.modelcontextprotocol.io/v2/migration/
"""

from __future__ import annotations

from dataclasses import dataclass

ERROR = "error"
WARNING = "warning"


@dataclass(frozen=True)
class Rule:
    """One checkable incompatibility."""

    id: str
    summary: str
    fix: str
    severity: str = ERROR


#: Import paths that no longer resolve, keyed by the exact module string.
DEAD_IMPORTS: dict[str, Rule] = {
    "mcp.server.fastmcp": Rule(
        id="MCP001",
        summary="mcp.server.fastmcp was renamed to mcp.server.mcpserver in v2",
        fix=(
            "from mcp.server.mcpserver import MCPServer as FastMCP  "
            "# or rename the symbol everywhere"
        ),
    ),
    "mcp.shared.version": Rule(
        id="MCP002",
        summary="mcp.shared.version was removed in v2",
        fix="from mcp.types.version import LATEST_PROTOCOL_VERSION",
    ),
}

#: Individual names removed from a module that still exists. Reporting the whole
#: module here would flag the names that are still exported next to them, which
#: is exactly the false positive this tool cannot afford.
DEAD_NAMES: dict[tuple[str, str], Rule] = {
    (
        "mcp.shared.context",
        "RequestContext",
    ): Rule(
        id="MCP003",
        summary="mcp.shared.context.RequestContext was split in v2",
        fix=(
            "from mcp.server.context import ServerRequestContext  "
            "# or mcp.client.context.ClientRequestContext"
        ),
    ),
    (
        "mcp.client.streamable_http",
        "streamablehttp_client",
    ): Rule(
        id="MCP004",
        summary="streamablehttp_client was removed in v2",
        fix="use streamable_http_client (with underscores) instead",
    ),
}

#: Symbols removed from mcp.types, keyed by the old name.
DEAD_TYPE_NAMES: dict[str, str] = {
    "Content": "ContentBlock",
    "ResourceReference": "ResourceTemplateReference",
    "ClientRequestType": "ClientRequest",
    "ClientNotificationType": "ClientNotification",
    "ClientResultType": "ClientResult",
    "ServerRequestType": "ServerRequest",
    "ServerNotificationType": "ServerNotification",
    "ServerResultType": "ServerResult",
}

#: camelCase attributes that no longer exist on the pydantic models.
CAMEL_ATTRIBUTES: dict[str, str] = {
    "inputSchema": "input_schema",
    "outputSchema": "output_schema",
    "isError": "is_error",
    "nextCursor": "next_cursor",
    "mimeType": "mime_type",
    "structuredContent": "structured_content",
    "serverInfo": "server_info",
    "protocolVersion": "protocol_version",
    "uriTemplate": "uri_template",
    "listChanged": "list_changed",
    "progressToken": "progress_token",
}

#: Constructor kwargs that still parse but no longer do what they did.
CONSTRUCTOR_MOVES: dict[str, str] = {
    "port": "pass it to mcp.run(transport=..., port=...) instead",
    "host": "pass it to mcp.run(transport=..., host=...) instead",
    "stateless_http": "pass it to mcp.run(transport=..., stateless_http=...) instead",
    "json_response": "pass it to mcp.run(transport=..., json_response=...) instead",
    "sse_path": "pass it to mcp.run(transport=..., sse_path=...) instead",
    "streamable_http_path": "pass it to mcp.run(transport=..., streamable_http_path=...)",
}
