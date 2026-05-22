"""In-memory counter state.

Intentionally minimal. Resets when the process restarts; not safe across
workers. This sample uses it to keep the focus on MCP wiring rather than
persistence. Return types use Pydantic so FastMCP emits a JSON output
schema, which in turn makes `CallToolResult.structuredContent` available
to the React MCP App.
"""

from __future__ import annotations

import threading
import time

from pydantic import BaseModel, Field

HISTORY_LIMIT = 20


class HistoryPoint(BaseModel):
    ts: float
    value: int


class CounterSnapshot(BaseModel):
    value: int
    history: list[HistoryPoint] = Field(default_factory=list)


class CounterState:
    def __init__(self) -> None:
        self._value = 0
        self._history: list[HistoryPoint] = []
        self._lock = threading.Lock()

    @property
    def value(self) -> int:
        with self._lock:
            return self._value

    def snapshot(self) -> CounterSnapshot:
        with self._lock:
            return CounterSnapshot(value=self._value, history=list(self._history))

    def add(self, delta: int) -> CounterSnapshot:
        with self._lock:
            self._value += delta
            self._history.append(HistoryPoint(ts=time.time(), value=self._value))
            if len(self._history) > HISTORY_LIMIT:
                self._history = self._history[-HISTORY_LIMIT:]
            return CounterSnapshot(value=self._value, history=list(self._history))

    def reset(self) -> CounterSnapshot:
        with self._lock:
            self._value = 0
            self._history = []
            return CounterSnapshot(value=self._value, history=list(self._history))


state = CounterState()
