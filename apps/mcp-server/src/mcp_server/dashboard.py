"""Dashboard sample: tools + UI resource for the Dashboard MCP App screen.

This is the third sample alongside Counter and Tasks. It demonstrates a single
tool call returning a *composite* snapshot that drives multiple widgets at once
(KPI cards + trend bar chart + activity list). FastMCP emits a JSON output
schema for the `Dashboard` Pydantic model and populates
`CallToolResult.structuredContent` — the React App routes to the Dashboard
screen by the shape of that payload.

Each tool carries `_meta["ui/resourceUri"] = "ui://dashboard"`. The
`ui://dashboard` resource reuses the *same* single-file bundle as
`ui://counter` / `ui://tasks` (`resources.read_bundle()`); shape-based routing
in the React App selects the right screen.

State is in-memory and resets on process restart, matching `state.py` and
`tasks.py`. `tick()` advances values deterministically (no `random`) so tests
can assert exact post-refresh state.
"""

from __future__ import annotations

import threading
import time
from typing import Literal

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from mcp_server.resources import UI_RESOURCE_MIME, read_bundle

UI_DASHBOARD_RESOURCE_URI = "ui://dashboard"
DASHBOARD_UI_META: dict = {"ui/resourceUri": UI_DASHBOARD_RESOURCE_URI}

Severity = Literal["info", "warn", "error"]


class KpiCard(BaseModel):
    label: str
    value: float
    unit: str = ""
    delta_pct: float = 0.0


class TrendPoint(BaseModel):
    label: str
    value: int


class ActivityItem(BaseModel):
    id: str
    message: str
    severity: Severity = "info"
    created_at: float  # seconds since epoch, like Task.created_at


class Dashboard(BaseModel):
    kpis: list[KpiCard] = Field(default_factory=list)
    trend: list[TrendPoint] = Field(default_factory=list)
    activity: list[ActivityItem] = Field(default_factory=list)
    refreshed_at: float


_TREND_LABELS: tuple[str, ...] = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_SEED_TREND_VALUES: tuple[int, ...] = (12, 18, 22, 30, 27, 24, 33)

_SEED_KPIS: tuple[KpiCard, ...] = (
    KpiCard(label="Users", value=1240, unit="", delta_pct=4.2),
    KpiCard(label="Sales", value=34200, unit="$", delta_pct=12.5),
    KpiCard(label="Errors", value=3, unit="", delta_pct=-50.0),
    KpiCard(label="Uptime", value=99.9, unit="%", delta_pct=0.1),
)

# Per-tick KPI step (one entry per card, same order as _SEED_KPIS).
_KPI_STEPS: tuple[float, ...] = (3, 250, -1, 0.05)

_SEED_ACTIVITY: tuple[tuple[str, str, Severity], ...] = (
    ("act-1", "Deployment v1.4.2 completed", "info"),
    ("act-2", "Error rate above 1% in /api/v1/orders", "warn"),
    ("act-3", "Payment gateway timeout (3 retries)", "error"),
)


class DashboardStore:
    """Thread-safe, in-memory dashboard state.

    `tick()` is deterministic so tests can assert exact post-refresh state.
    Snapshots are fresh copies — callers never see internal lists.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._kpis: list[KpiCard] = []
        self._trend: list[TrendPoint] = []
        self._activity: list[ActivityItem] = []
        self._tick = 0
        self._seed_locked()

    def _seed_locked(self) -> None:
        now = time.time()
        self._kpis = [card.model_copy() for card in _SEED_KPIS]
        self._trend = [
            TrendPoint(label=label, value=value)
            for label, value in zip(_TREND_LABELS, _SEED_TREND_VALUES, strict=True)
        ]
        self._activity = [
            ActivityItem(id=aid, message=msg, severity=sev, created_at=now)
            for aid, msg, sev in _SEED_ACTIVITY
        ]
        self._tick = 0

    def _snapshot_locked(self) -> Dashboard:
        return Dashboard(
            kpis=list(self._kpis),
            trend=list(self._trend),
            activity=list(self._activity),
            refreshed_at=time.time(),
        )

    def snapshot(self) -> Dashboard:
        with self._lock:
            return self._snapshot_locked()

    def tick(self) -> Dashboard:
        with self._lock:
            self._tick += 1

            # KPI nudge: clamp at 0 and recompute delta_pct from the step that
            # was actually applied (handles the clamp without divide-by-zero).
            next_kpis: list[KpiCard] = []
            for card, step in zip(self._kpis, _KPI_STEPS, strict=True):
                new_value = max(0.0, card.value + step)
                achieved = new_value - card.value
                delta_pct = (achieved / card.value * 100.0) if card.value > 0 else 0.0
                next_kpis.append(
                    card.model_copy(
                        update={"value": new_value, "delta_pct": round(delta_pct, 2)}
                    )
                )
            self._kpis = next_kpis

            # Trend rolls one bucket: drop oldest, append next label + a
            # deterministic small swing around the previous last value.
            last_value = self._trend[-1].value if self._trend else 0
            swing = (self._tick * 5) % 11 - 5  # cycles within [-5, 5]
            next_value = max(0, last_value + swing)
            next_label = _TREND_LABELS[
                (len(_TREND_LABELS) - 1 + self._tick) % len(_TREND_LABELS)
            ]
            self._trend = self._trend[1:] + [
                TrendPoint(label=next_label, value=next_value)
            ]

            return self._snapshot_locked()

    def acknowledge(self, alert_id: str) -> Dashboard:
        with self._lock:
            self._activity = [a for a in self._activity if a.id != alert_id]
            return self._snapshot_locked()

    def reset(self) -> Dashboard:
        with self._lock:
            self._seed_locked()
            return self._snapshot_locked()


dashboard_store = DashboardStore()


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="get_dashboard",
        description=(
            "Return the latest dashboard snapshot (KPI cards, 7-bucket trend, "
            "recent activity). Useful for the UI to (re)hydrate without "
            "mutating anything."
        ),
        meta=DASHBOARD_UI_META,
    )
    def get_dashboard() -> Dashboard:
        return dashboard_store.snapshot()

    @mcp.tool(
        name="refresh_dashboard",
        description=(
            "Nudge KPI values by a deterministic step and roll the trend "
            "window by one bucket, then return the new snapshot."
        ),
        meta=DASHBOARD_UI_META,
    )
    def refresh_dashboard() -> Dashboard:
        return dashboard_store.tick()

    @mcp.tool(
        name="acknowledge_alert",
        description=(
            "Remove the activity entry with the given `alert_id` and return "
            "the new snapshot. Unknown ids are a no-op."
        ),
        meta=DASHBOARD_UI_META,
    )
    def acknowledge_alert(alert_id: str) -> Dashboard:
        return dashboard_store.acknowledge(alert_id)

    @mcp.resource(
        UI_DASHBOARD_RESOURCE_URI,
        name="Dashboard App UI",
        description="Single-file HTML bundle for the Dashboard MCP App (shared bundle).",
        mime_type=UI_RESOURCE_MIME,
    )
    def dashboard_ui() -> str:
        return read_bundle()
