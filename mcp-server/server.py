"""Sample MCP server for testing deployment on TrueFoundry.

Exposes a few toy tools and a resource. Defaults to the "streamable-http"
transport so it can run as a normal HTTP service inside a container, but
also supports "stdio" (set MCP_TRANSPORT=stdio) for local MCP clients
such as Claude Desktop or Cursor that spawn the server as a subprocess.
"""

import os
import time
from datetime import datetime, timezone

from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp.server.mcpserver import MCPServer

mcp = MCPServer(
    name="sample-mcp-server",
    instructions="A minimal sample MCP server used to smoke-test container deployments.",
)


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b


@mcp.tool()
def reverse_text(text: str) -> str:
    """Reverse the characters in a string."""
    return text[::-1]


@mcp.tool()
def get_server_time() -> str:
    """Return the server's current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


@mcp.resource("info://server")
def server_info() -> str:
    """Static info about this sample server."""
    return "sample-mcp-server: a demo MCP server for TrueFoundry deployment testing."


@mcp.custom_route("/health", methods=["GET"])
async def health(_request: Request) -> JSONResponse:
    """Liveness/readiness probe endpoint for container platforms."""
    return JSONResponse({"status": "ok", "time": int(time.time())})


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "streamable-http")

    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        host = os.environ.get("HOST", "0.0.0.0")
        port = int(os.environ.get("PORT", "8000"))
        mcp.run(
            transport="streamable-http",
            host=host,
            port=port,
            stateless_http=True,
        )
