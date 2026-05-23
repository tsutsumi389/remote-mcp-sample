"""Run the MCP server with uvicorn (no auto-reload).

For development, prefer:
    uv run uvicorn mcp_server.server:app --reload --host 127.0.0.1 --port 3001

The bind host defaults to 127.0.0.1 so the sample does not expose the
unauthenticated MCP endpoint on every interface. Set MCP_SERVER_HOST=0.0.0.0
explicitly inside a container that needs to accept connections from the host.
"""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.environ.get("MCP_SERVER_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_SERVER_PORT", "3001"))
    uvicorn.run("mcp_server.server:app", host=host, port=port)


if __name__ == "__main__":
    main()
