"""Resources exposed by the MCP server.

`ui://counter` returns the single-file HTML bundle produced by the React
MCP App. The bundle is **served by the MCP App itself** (a `vite preview`
HTTP server) — this module relays it: on every `resources/read` it fetches
the HTML over HTTP from `MCP_APP_BUNDLE_URL` and returns it inline.

This keeps the *serving* responsibility on the mcp-app side. The MCP Apps
SDK (`@modelcontextprotocol/ext-apps`) only supports inline HTML — the host
renders `resource.contents[0].text` via an iframe `srcdoc` and cannot load
from the app's URL directly — so the server must return a self-contained
bundle. The mcp-app build therefore stays single-file (vite-plugin-singlefile).

Any fetch failure (connection refused, timeout, non-200, oversized, non-utf8)
degrades gracefully to a placeholder so the host always renders something.

`MCP_APP_BUNDLE_URL` defaults to the host dev value; Docker Compose overrides
it with the compose service URL (`http://mcp-app:4173/`).
"""

from __future__ import annotations

import os

import httpx
from mcp.server.fastmcp import FastMCP

UI_RESOURCE_URI = "ui://counter"
UI_RESOURCE_MIME = "text/html;profile=mcp-app"

_BUNDLE_URL_ENV = "MCP_APP_BUNDLE_URL"
_DEFAULT_BUNDLE_URL = "http://localhost:4173/"
_MAX_BUNDLE_BYTES = 16 * 1024 * 1024
_FETCH_TIMEOUT = 5.0  # seconds (connect + read); bounds host hangs


_PLACEHOLDER_HTML = """<!doctype html>
<html><body>
<p>MCP App bundle not reachable.</p>
<p>Ensure the mcp-app preview server is running (<code>pnpm -C apps/mcp-app
serve</code> or the Docker dev environment) and that
<code>MCP_APP_BUNDLE_URL</code> points at it.</p>
</body></html>
"""


def read_bundle() -> str:
    """Fetch the single-file HTML bundle from the MCP App over HTTP.

    Fetched on every call so dev rebuilds (``vite build --watch``) are picked
    up. Runs on a FastMCP worker thread (sync resource readers are off-loaded
    via anyio), so a blocking ``httpx.Client`` call is fine here. ``httpx`` is
    a transitive dependency of ``mcp``.
    """
    url = os.environ.get(_BUNDLE_URL_ENV) or _DEFAULT_BUNDLE_URL
    try:
        with httpx.Client(timeout=_FETCH_TIMEOUT) as client:
            resp = client.get(url)
    except httpx.HTTPError:
        return _PLACEHOLDER_HTML
    if resp.status_code != 200:
        return _PLACEHOLDER_HTML
    data = resp.content
    if len(data) > _MAX_BUNDLE_BYTES:
        return _PLACEHOLDER_HTML
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return _PLACEHOLDER_HTML


def register(mcp: FastMCP) -> None:
    @mcp.resource(
        UI_RESOURCE_URI,
        name="Counter App UI",
        description="Single-file HTML bundle for the Counter MCP App.",
        mime_type=UI_RESOURCE_MIME,
    )
    def counter_ui() -> str:
        return read_bundle()
