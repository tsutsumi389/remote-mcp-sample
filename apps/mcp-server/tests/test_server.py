"""Smoke tests for tools / resources via the FastMCP server."""

from __future__ import annotations

import httpx
import pytest

from mcp_server import resources, state as state_module
from mcp_server.dashboard import UI_DASHBOARD_RESOURCE_URI, dashboard_store
from mcp_server.resources import UI_RESOURCE_MIME, UI_RESOURCE_URI
from mcp_server.server import mcp
from mcp_server.tasks import UI_TASKS_RESOURCE_URI, task_store

_COUNTER_TOOLS = {"increment_counter", "reset_counter", "get_counter"}
_TASK_TOOLS = {"list_tasks", "add_task", "toggle_task"}
_DASHBOARD_TOOLS = {"get_dashboard", "refresh_dashboard", "acknowledge_alert"}

_SAMPLE_BUNDLE_HTML = "<!doctype html><html><body>sample bundle</body></html>"


def _html_response(html: str, status: int = 200) -> httpx.Response:
    return httpx.Response(
        status,
        content=html.encode("utf-8"),
        request=httpx.Request("GET", "http://mcp-app.test/"),
    )


@pytest.fixture(autouse=True)
def reset_state() -> None:
    state_module.state.reset()
    task_store.reset()
    dashboard_store.reset()


@pytest.fixture
def mock_bundle_http(monkeypatch) -> None:
    """Patch the HTTP layer so ``read_bundle()`` returns a known bundle.

    Patching ``httpx.Client.get`` (rather than ``resources.read_bundle``)
    covers both the ``ui://counter`` and ``ui://tasks`` resource readers with a
    single patch *and* exercises the real status/size/decode branches. Applied
    explicitly (not autouse) so it does not hijack ``TestClient`` HTTP in the
    ``/health`` test, which is also built on ``httpx.Client``.
    """

    def fake_get(self, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        return _html_response(_SAMPLE_BUNDLE_HTML)

    monkeypatch.setattr(httpx.Client, "get", fake_get)


async def test_counter_tools_carry_counter_ui_meta() -> None:
    tool_specs = await mcp.list_tools()
    by_name = {t.name: t for t in tool_specs}
    assert _COUNTER_TOOLS <= set(by_name)

    for name in _COUNTER_TOOLS:
        meta = by_name[name].meta or {}
        assert meta.get("ui/resourceUri") == UI_RESOURCE_URI, (
            f"{name} missing _meta['ui/resourceUri']"
        )


async def test_task_tools_expose_ui_tasks_meta() -> None:
    tool_specs = await mcp.list_tools()
    by_name = {t.name: t for t in tool_specs}
    assert _TASK_TOOLS <= set(by_name)

    for name in _TASK_TOOLS:
        meta = by_name[name].meta or {}
        assert meta.get("ui/resourceUri") == UI_TASKS_RESOURCE_URI, (
            f"{name} missing _meta['ui/resourceUri']"
        )


async def test_list_tasks_returns_seeded_tasks() -> None:
    result = await mcp.call_tool("list_tasks", {})
    tasks = _structured(result)["tasks"]
    assert isinstance(tasks, list) and len(tasks) >= 1
    first = tasks[0]
    assert isinstance(first["id"], int)
    assert isinstance(first["title"], str)
    assert isinstance(first["done"], bool)
    assert isinstance(first["created_at"], (int, float))


async def test_add_task_round_trip() -> None:
    before = _structured(await mcp.call_tool("list_tasks", {}))["tasks"]
    result = await mcp.call_tool("add_task", {"title": "Write docs"})
    tasks = _structured(result)["tasks"]
    assert len(tasks) == len(before) + 1
    added = tasks[-1]
    assert added["title"] == "Write docs"
    assert added["done"] is False
    assert isinstance(added["id"], int)
    assert isinstance(added["created_at"], (int, float))


async def test_add_task_ignores_blank_title() -> None:
    before = _structured(await mcp.call_tool("list_tasks", {}))["tasks"]
    after = _structured(await mcp.call_tool("add_task", {"title": "   "}))["tasks"]
    assert len(after) == len(before)


async def test_toggle_task_round_trip() -> None:
    tasks = _structured(await mcp.call_tool("add_task", {"title": "Toggle me"}))["tasks"]
    task_id = tasks[-1]["id"]

    toggled = _structured(await mcp.call_tool("toggle_task", {"id": task_id}))["tasks"]
    assert next(t for t in toggled if t["id"] == task_id)["done"] is True

    toggled = _structured(await mcp.call_tool("toggle_task", {"id": task_id}))["tasks"]
    assert next(t for t in toggled if t["id"] == task_id)["done"] is False


async def test_tasks_ui_resource_returns_html_with_apps_profile(mock_bundle_http) -> None:
    contents = await mcp.read_resource(UI_TASKS_RESOURCE_URI)
    assert contents, "ui://tasks returned no content"
    first = contents[0]
    assert first.mime_type == UI_RESOURCE_MIME
    text = first.content
    assert "<html" in text or "<!doctype html>" in text.lower()


async def test_dashboard_tools_expose_ui_dashboard_meta() -> None:
    tool_specs = await mcp.list_tools()
    by_name = {t.name: t for t in tool_specs}
    assert _DASHBOARD_TOOLS <= set(by_name)

    for name in _DASHBOARD_TOOLS:
        meta = by_name[name].meta or {}
        assert meta.get("ui/resourceUri") == UI_DASHBOARD_RESOURCE_URI, (
            f"{name} missing _meta['ui/resourceUri']"
        )


async def test_get_dashboard_returns_seeded_snapshot() -> None:
    data = _structured(await mcp.call_tool("get_dashboard", {}))

    kpis = data["kpis"]
    assert isinstance(kpis, list) and len(kpis) == 4
    assert [k["label"] for k in kpis] == ["Users", "Sales", "Errors", "Uptime"]

    trend = data["trend"]
    assert len(trend) == 7
    assert [p["label"] for p in trend] == [
        "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun",
    ]
    assert all(isinstance(p["value"], int) for p in trend)

    activity = data["activity"]
    assert len(activity) == 3
    assert {a["severity"] for a in activity} <= {"info", "warn", "error"}
    assert isinstance(data["refreshed_at"], (int, float))


async def test_refresh_dashboard_rolls_trend_window_deterministically() -> None:
    before = _structured(await mcp.call_tool("get_dashboard", {}))
    after = _structured(await mcp.call_tool("refresh_dashboard", {}))

    # Trend window rolled by one bucket: oldest dropped, next label appended.
    assert len(after["trend"]) == len(before["trend"]) == 7
    assert [p["label"] for p in after["trend"][:-1]] == [
        p["label"] for p in before["trend"][1:]
    ]
    assert after["trend"][-1]["label"] == "Mon"  # cycles from Sun

    # First tick swing is `(1 * 5) % 11 - 5 == 0`, so last trend value equals
    # the prior last value.
    assert after["trend"][-1]["value"] == before["trend"][-1]["value"]

    # KPI "Users" advanced by the deterministic step (+3).
    users_before = next(k for k in before["kpis"] if k["label"] == "Users")["value"]
    users_after = next(k for k in after["kpis"] if k["label"] == "Users")["value"]
    assert users_after == users_before + 3


async def test_acknowledge_alert_removes_targeted_entry_and_is_idempotent() -> None:
    before = _structured(await mcp.call_tool("get_dashboard", {}))
    assert len(before["activity"]) == 3
    alert_id = before["activity"][0]["id"]

    after = _structured(
        await mcp.call_tool("acknowledge_alert", {"alert_id": alert_id})
    )
    remaining_ids = [a["id"] for a in after["activity"]]
    assert alert_id not in remaining_ids
    assert len(after["activity"]) == 2

    # Unknown id is a no-op (does not raise, does not mutate).
    still = _structured(
        await mcp.call_tool("acknowledge_alert", {"alert_id": "does-not-exist"})
    )
    assert [a["id"] for a in still["activity"]] == remaining_ids


async def test_dashboard_ui_resource_returns_html_with_apps_profile(mock_bundle_http) -> None:
    contents = await mcp.read_resource(UI_DASHBOARD_RESOURCE_URI)
    assert contents, "ui://dashboard returned no content"
    first = contents[0]
    assert first.mime_type == UI_RESOURCE_MIME
    text = first.content
    assert "<html" in text or "<!doctype html>" in text.lower()


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


async def test_ui_resource_returns_html_with_apps_profile(mock_bundle_http) -> None:
    contents = await mcp.read_resource(UI_RESOURCE_URI)
    assert contents, "ui://counter returned no content"
    first = contents[0]
    assert first.mime_type == UI_RESOURCE_MIME
    text = first.content
    assert "<html" in text or "<!doctype html>" in text.lower()


def test_read_bundle_success_returns_fetched_html(mock_bundle_http) -> None:
    # mock_bundle_http serves _SAMPLE_BUNDLE_HTML over the patched HTTP layer.
    assert resources.read_bundle() == _SAMPLE_BUNDLE_HTML


def test_read_bundle_falls_back_when_fetch_fails(monkeypatch) -> None:
    def boom(self, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        raise httpx.ConnectError("refused", request=httpx.Request("GET", "http://x/"))

    monkeypatch.setattr(httpx.Client, "get", boom)
    assert "not reachable" in resources.read_bundle()


def test_read_bundle_falls_back_on_non_200(monkeypatch) -> None:
    monkeypatch.setattr(
        httpx.Client, "get", lambda self, *a, **k: _html_response("<html/>", status=503)
    )
    assert "not reachable" in resources.read_bundle()


def test_read_bundle_falls_back_when_oversized(monkeypatch) -> None:
    big = "x" * (resources._MAX_BUNDLE_BYTES + 1)
    monkeypatch.setattr(
        httpx.Client, "get", lambda self, *a, **k: _html_response(big)
    )
    assert "not reachable" in resources.read_bundle()


def test_health_endpoint_returns_ok() -> None:
    from fastapi.testclient import TestClient

    from mcp_server.server import app

    # The `with` block runs the FastAPI lifespan (starts the MCP session manager).
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def _structured(result) -> dict:
    # FastMCP.call_tool returns (content_list, structured_content) in recent
    # versions; tolerate either tuple shape or a single dict.
    if isinstance(result, tuple) and len(result) == 2:
        _, structured = result
        return structured  # type: ignore[return-value]
    if isinstance(result, dict):
        return result
    return getattr(result, "structuredContent", result)  # type: ignore[return-value]
