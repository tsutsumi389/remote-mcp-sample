"""MCP tools for the Counter sample.

Each tool carries `_meta["ui/resourceUri"] = "ui://counter"` so an MCP Apps
aware host knows which HTML resource to render in the iframe. The key name
matches the `RESOURCE_URI_META_KEY` constant exported by
`@modelcontextprotocol/ext-apps` (v0.1.0).

Return types are `CounterSnapshot` (Pydantic), which makes FastMCP emit a
JSON output schema and populate `CallToolResult.structuredContent` — the
React App reads that field directly.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_server.resources import UI_RESOURCE_URI
from mcp_server.state import CounterSnapshot, state

UI_META: dict = {"ui/resourceUri": UI_RESOURCE_URI}


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="increment_counter",
        description=(
            "Increment the counter by `by` (default 1) and return the new "
            "value plus recent history."
        ),
        meta=UI_META,
    )
    def increment_counter(by: int = 1) -> CounterSnapshot:
        return state.add(by)

    @mcp.tool(
        name="reset_counter",
        description="Reset the counter to 0 and return the cleared state.",
        meta=UI_META,
    )
    def reset_counter() -> CounterSnapshot:
        return state.reset()

    @mcp.tool(
        name="get_counter",
        description=(
            "Return the current counter value and history. Useful for the "
            "UI to fetch the latest state without mutating it."
        ),
        meta=UI_META,
    )
    def get_counter() -> CounterSnapshot:
        return state.snapshot()
