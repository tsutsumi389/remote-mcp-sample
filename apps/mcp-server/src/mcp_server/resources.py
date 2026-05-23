"""Resources exposed by the MCP server.

`ui://counter` returns the single-file HTML bundle produced by the React
MCP App. The bundle path is configurable via the `MCP_APP_BUNDLE_PATH`
environment variable so the same code works both inside the Docker dev
environment (volume-mounted bundle at /bundle) and when run directly on
the host.

Bundle reads are constrained to directories resolved at module load
(`_ALLOWED_BUNDLE_DIRS`) so that a later symlink swap on `/bundle` or the
host build directory cannot widen the read scope. Files are opened with
`O_NOFOLLOW` to close the TOCTOU window between path resolution and read.
"""

from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

UI_RESOURCE_URI = "ui://counter"
UI_RESOURCE_MIME = "text/html;profile=mcp-app"

_BUNDLE_ENV = "MCP_APP_BUNDLE_PATH"
_MAX_BUNDLE_BYTES = 16 * 1024 * 1024
_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)


def _strict_resolve(p: Path) -> Path | None:
    try:
        return p.resolve(strict=True)
    except (OSError, RuntimeError):
        return None


def _find_host_default() -> Path | None:
    """Walk up from this module to find ``apps/mcp-app/dist/index.html``.

    Robust to repository layout changes — does not depend on a fixed
    ``parents[N]`` depth.
    """
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor / "apps" / "mcp-app" / "dist" / "index.html"
        if candidate.is_file():
            return candidate
    return None


_HOST_DEFAULT = _find_host_default()


def _initial_allowed_dirs() -> tuple[Path, ...]:
    dirs: list[Path] = []
    if _HOST_DEFAULT is not None:
        d = _strict_resolve(_HOST_DEFAULT.parent)
        if d is not None:
            dirs.append(d)
    bundle_mount = _strict_resolve(Path("/bundle"))
    if bundle_mount is not None:
        dirs.append(bundle_mount)
    # dedupe preserving order
    seen: dict[Path, None] = {}
    for d in dirs:
        seen.setdefault(d, None)
    return tuple(seen)


_ALLOWED_BUNDLE_DIRS: tuple[Path, ...] = _initial_allowed_dirs()


def _bundle_path() -> Path | None:
    override = os.environ.get(_BUNDLE_ENV)
    if override:
        candidate: Path | None = Path(override)
    else:
        candidate = _HOST_DEFAULT
    if candidate is None:
        return None
    resolved = _strict_resolve(candidate)
    if resolved is None:
        return None
    if resolved.suffix.lower() != ".html":
        return None
    for allowed in _ALLOWED_BUNDLE_DIRS:
        try:
            resolved.relative_to(allowed)
        except ValueError:
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
    if path is None:
        return _PLACEHOLDER_HTML
    try:
        fd = os.open(path, os.O_RDONLY | _NOFOLLOW)
    except OSError:
        return _PLACEHOLDER_HTML
    try:
        with os.fdopen(fd, "rb") as fh:
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
