"""FastMCP entrypoint exposing the Streamable HTTP ASGI app.

Usage (dev):
    uv run uvicorn mcp_server.server:app --host 0.0.0.0 --port 3001 --reload

Usage (in-process):
    python -m mcp_server
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_server import resources, tools

mcp = FastMCP("counter-sample")

tools.register(mcp)
resources.register(mcp)

# Streamable HTTP ASGI app — pass this to uvicorn.
app = mcp.streamable_http_app()
