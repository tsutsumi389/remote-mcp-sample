"""Smoke tests for tools / resources via the FastMCP server."""

from __future__ import annotations

import pytest

from mcp_server import resources, state as state_module
from mcp_server.resources import UI_RESOURCE_MIME, UI_RESOURCE_URI
from mcp_server.server import mcp


@pytest.fixture(autouse=True)
def reset_state() -> None:
    state_module.state.reset()


async def test_tools_list_exposes_three_tools_with_ui_meta() -> None:
    tool_specs = await mcp.list_tools()
    by_name = {t.name: t for t in tool_specs}
    assert set(by_name) == {"increment_counter", "reset_counter", "get_counter"}

    for tool in tool_specs:
        meta = tool.meta or {}
        assert meta.get("ui/resourceUri") == UI_RESOURCE_URI, (
            f"{tool.name} missing _meta['ui/resourceUri']"
        )


async def test_increment_then_reset_round_trip() -> None:
    result = await mcp.call_tool("increment_counter", {"by": 3})
    structured = _structured(result)
    assert structured["value"] == 3
    assert structured["history"][-1]["value"] == 3

    result = await mcp.call_tool("increment_counter", {"by": 2})
    structured = _structured(result)
    assert structured["value"] == 5

    result = await mcp.call_tool("reset_counter", {})
    structured = _structured(result)
    assert structured["value"] == 0
    assert structured["history"] == []


async def test_ui_resource_returns_html_with_apps_profile() -> None:
    contents = await mcp.read_resource(UI_RESOURCE_URI)
    assert contents, "ui://counter returned no content"
    first = contents[0]
    assert first.mime_type == UI_RESOURCE_MIME
    text = first.content
    assert "<html" in text or "<!doctype html>" in text.lower()


def test_read_bundle_falls_back_when_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MCP_APP_BUNDLE_PATH", str(tmp_path / "missing.html"))
    html = resources.read_bundle()
    assert "MCP App bundle not found" in html


def _structured(result) -> dict:
    # FastMCP.call_tool returns (content_list, structured_content) in recent
    # versions; tolerate either tuple shape or a single dict.
    if isinstance(result, tuple) and len(result) == 2:
        _, structured = result
        return structured  # type: ignore[return-value]
    if isinstance(result, dict):
        return result
    return getattr(result, "structuredContent", result)  # type: ignore[return-value]
