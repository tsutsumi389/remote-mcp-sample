"""Resources exposed by the MCP server.

`ui://counter` returns the single-file HTML bundle produced by the React
MCP App (`apps/mcp-app/dist/index.html`). The bundle path is configurable
via the `MCP_APP_BUNDLE_PATH` environment variable so the same code works
both inside the Docker dev environment (volume-mounted bundle) and when
run directly on the host.
"""

from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

UI_RESOURCE_URI = "ui://counter"
UI_RESOURCE_MIME = "text/html;profile=mcp-app"

DEFAULT_BUNDLE_PATH = (
    Path(__file__).resolve().parents[3] / "mcp-app" / "dist" / "index.html"
)

# Bundle reads are constrained to directories that legitimately host the
# React build output, to keep an untrusted MCP_APP_BUNDLE_PATH from leaking
# arbitrary readable files (e.g. /etc/passwd) through the ui://counter
# resource. /bundle is the mount point used by docker-compose.yml.
_ALLOWED_BUNDLE_DIRS = (
    DEFAULT_BUNDLE_PATH.parent,
    Path("/bundle"),
)
_MAX_BUNDLE_BYTES = 16 * 1024 * 1024


def _bundle_path() -> Path | None:
    override = os.environ.get("MCP_APP_BUNDLE_PATH")
    candidate = Path(override) if override else DEFAULT_BUNDLE_PATH
    try:
        resolved = candidate.resolve()
    except OSError:
        return None
    if resolved.suffix.lower() != ".html":
        return None
    for allowed in _ALLOWED_BUNDLE_DIRS:
        try:
            resolved.relative_to(allowed.resolve())
        except (OSError, ValueError):
            continue
        return resolved
    return None


_PLACEHOLDER_HTML = """<!doctype html>
<html><body>
<p>MCP App bundle not found.</p>
<p>Run <code>pnpm -C apps/mcp-app build</code> (or start the Docker dev
environment) to generate <code>dist/index.html</code>.</p>
</body></html>
"""


def read_bundle() -> str:
    """Read the bundled HTML on every call so dev rebuilds are picked up."""
    path = _bundle_path()
    if path is None or not path.is_file():
        return _PLACEHOLDER_HTML
    try:
        with path.open("rb") as fh:
            data = fh.read(_MAX_BUNDLE_BYTES + 1)
    except OSError:
        return _PLACEHOLDER_HTML
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
