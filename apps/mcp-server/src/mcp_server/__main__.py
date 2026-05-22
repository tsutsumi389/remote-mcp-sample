"""Run the MCP server with uvicorn (no auto-reload).

For development, prefer:
    uv run uvicorn mcp_server.server:app --reload --host 0.0.0.0 --port 3001
"""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("MCP_SERVER_PORT", "3001"))
    uvicorn.run("mcp_server.server:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
