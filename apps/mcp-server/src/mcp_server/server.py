"""FastAPI app hosting the Counter MCP server (Streamable HTTP) + plain HTTP routes.

The MCP protocol endpoint stays at ``POST /mcp`` (unchanged for existing clients).
FastAPI serves plain HTTP routes alongside it (e.g. ``GET /health``).

Usage (dev):
    uv run uvicorn mcp_server.server:app --host 0.0.0.0 --port 3001 --reload

Usage (in-process):
    python -m mcp_server
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from mcp_server import dashboard, resources, tasks, tools, youtube

mcp = FastMCP("counter-sample")  # streamable_http_path defaults to "/mcp"

tools.register(mcp)
resources.register(mcp)
tasks.register(mcp)
dashboard.register(mcp)
youtube.register(mcp)

# Build the MCP Streamable HTTP ASGI app once. This also lazily creates the
# StreamableHTTP session manager that the FastAPI lifespan must run.
mcp_asgi = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Starlette does not run a mounted sub-app's lifespan, so we drive the MCP
    # session manager from the parent FastAPI app's lifespan.
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="counter-sample", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# Mount the MCP app at root LAST so specific FastAPI routes (/health, /docs,
# /openapi.json) take precedence; everything else (POST /mcp) falls through.
app.mount("/", mcp_asgi)
