"""YouTube search sample: tool + UI resource for the YouTube MCP App screen.

This is the fourth sample alongside Counter, Tasks, and Dashboard. It
demonstrates the canonical MCP App flow driven by *user input*: the screen
collects a query, calls `search_youtube`, and renders the structured results
as a grid of video cards.

The data is an in-memory, deterministic *mock* catalog (no API key, no network)
so the sample runs out of the box — the point is the data flow, not real
YouTube access. `search_youtube` filters the catalog by a case-insensitive
substring match over title + channel, sorts by view count, and returns a
Pydantic `YoutubeSearchResults` value. FastMCP emits a JSON output schema and
populates `CallToolResult.structuredContent`; the React App routes to the
YouTube screen by the shape of that payload.

The tool carries `_meta["ui/resourceUri"] = "ui://youtube"`. The `ui://youtube`
resource reuses the *same* single-file bundle as the other screens
(`resources.read_bundle()`); shape-based routing in the React App selects the
right screen.

Each video carries a `thumbnail_hue` (0-359) instead of an image URL: the App
renders a deterministic inline SVG placeholder from it, keeping the bundle
self-contained and free of outbound image fetches.
"""

from __future__ import annotations

import threading

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from mcp_server.resources import UI_RESOURCE_MIME, read_bundle

UI_YOUTUBE_RESOURCE_URI = "ui://youtube"
YOUTUBE_UI_META: dict = {"ui/resourceUri": UI_YOUTUBE_RESOURCE_URI}

_DEFAULT_LIMIT = 12


class YoutubeVideo(BaseModel):
    id: str
    title: str
    channel: str
    view_count: int
    published_at: float  # seconds since epoch, like Task.created_at
    thumbnail_hue: int  # 0-359; the App renders a placeholder SVG from this


class YoutubeSearchResults(BaseModel):
    query: str
    results: list[YoutubeVideo] = Field(default_factory=list)
    total_count: int = 0


# Fixed reference epoch (2024-01-01T00:00:00Z) so `published_at` values are
# deterministic across runs — each entry is this base minus a fixed age.
_BASE_EPOCH = 1_704_067_200
_DAY = 86_400

# (id, title, channel, view_count, age_days, hue)
_SEED_CATALOG: tuple[tuple[str, str, str, int, int, int], ...] = (
    ("vid-py-async", "Python async/await explained in 10 minutes", "CodeCraft", 1_842_000, 12, 210),
    ("vid-rust-intro", "Rust for Python developers — a gentle intro", "CodeCraft", 642_000, 40, 25),
    ("vid-ts-generics", "TypeScript generics from zero to hero", "DevBytes", 421_500, 7, 200),
    ("vid-react-hooks", "React hooks you should actually use", "DevBytes", 988_300, 21, 265),
    ("vid-mcp-apps", "Building MCP Apps with interactive UIs", "Model Context Live", 73_900, 3, 145),
    ("vid-docker-101", "Docker in 100 seconds (the real version)", "DevBytes", 2_310_000, 90, 190),
    ("vid-lofi-beats", "Lofi beats to code / study to — 24/7", "ChillHopMusic", 5_120_000, 365, 320),
    ("vid-jazz-piano", "Relaxing jazz piano for deep focus", "ChillHopMusic", 1_004_700, 120, 300),
    ("vid-pasta-carbonara", "Authentic carbonara — only 4 ingredients", "HomeKitchen", 3_450_000, 58, 35),
    ("vid-ramen-broth", "The 12-hour ramen broth, sped up", "HomeKitchen", 812_400, 14, 18),
    ("vid-sourdough", "Sourdough bread for absolute beginners", "HomeKitchen", 1_276_000, 200, 45),
    ("vid-speedrun", "Speedrunning a classic in under 5 minutes", "PixelArena", 4_002_900, 30, 110),
    ("vid-game-review", "Is the new open-world game worth it?", "PixelArena", 658_200, 5, 130),
    ("vid-guitar-loop", "Ambient guitar loop for coding sessions", "ChillHopMusic", 233_100, 9, 285),
    ("vid-ml-transformers", "Transformers explained without the math", "CodeCraft", 1_511_800, 75, 230),
)


class YoutubeStore:
    """Thread-safe, in-memory mock YouTube catalog.

    `search()` returns a fresh `YoutubeSearchResults` snapshot every time, so
    callers never touch the internal list. The catalog is read-only (the sample
    has no mutating tools), but the lock keeps the access pattern consistent
    with the other stores and safe under FastMCP's worker threads.
    """

    def __init__(self) -> None:
        self._videos: list[YoutubeVideo] = []
        self._lock = threading.Lock()
        self._seed()

    def _seed(self) -> None:
        with self._lock:
            self._videos = [
                YoutubeVideo(
                    id=vid,
                    title=title,
                    channel=channel,
                    view_count=views,
                    published_at=float(_BASE_EPOCH - age_days * _DAY),
                    thumbnail_hue=hue,
                )
                for vid, title, channel, views, age_days, hue in _SEED_CATALOG
            ]

    def search(self, query: str, limit: int) -> YoutubeSearchResults:
        needle = query.strip().lower()
        capped = max(1, min(limit, len(_SEED_CATALOG)))
        with self._lock:
            matched = [
                v
                for v in self._videos
                if not needle
                or needle in v.title.lower()
                or needle in v.channel.lower()
            ]
        matched.sort(key=lambda v: v.view_count, reverse=True)
        return YoutubeSearchResults(
            query=query.strip(),
            results=matched[:capped],
            total_count=len(matched),
        )

    def reset(self) -> None:
        self._seed()


youtube_store = YoutubeStore()


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="search_youtube",
        description=(
            "Search the (mock) YouTube catalog by keyword and return matching "
            "videos sorted by view count. An empty `query` returns everything. "
            "`limit` caps the number of results (default 12)."
        ),
        meta=YOUTUBE_UI_META,
    )
    def search_youtube(query: str = "", limit: int = _DEFAULT_LIMIT) -> YoutubeSearchResults:
        return youtube_store.search(query, limit)

    @mcp.resource(
        UI_YOUTUBE_RESOURCE_URI,
        name="YouTube Search App UI",
        description="Single-file HTML bundle for the YouTube Search MCP App (shared bundle).",
        mime_type=UI_RESOURCE_MIME,
    )
    def youtube_ui() -> str:
        return read_bundle()
