"""Task-list sample: tools + UI resource for the Tasks MCP App screen.

This is a second sample alongside the Counter. It demonstrates piping a
*table* of structured rows from the server to an MCP Apps screen. The tools
return Pydantic `TaskList` values, so FastMCP emits a JSON output schema and
populates `CallToolResult.structuredContent` — the React App reads that field
and renders a table.

Each tool carries `_meta["ui/resourceUri"] = "ui://tasks"`. The `ui://tasks`
resource reuses the *same* single-file bundle as `ui://counter`
(`resources.read_bundle()`); the React App routes to the right screen based on
the shape of the structured content it receives.

State is in-memory and resets on process restart, matching `state.py`.
"""

from __future__ import annotations

import threading
import time

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from mcp_server.resources import UI_RESOURCE_MIME, read_bundle

UI_TASKS_RESOURCE_URI = "ui://tasks"
TASKS_UI_META: dict = {"ui/resourceUri": UI_TASKS_RESOURCE_URI}


class Task(BaseModel):
    id: int
    title: str
    done: bool = False
    created_at: float  # seconds since epoch, like HistoryPoint.ts


class TaskList(BaseModel):
    tasks: list[Task] = Field(default_factory=list)


_SEED_TITLES = (
    "Read the MCP Apps quickstart",
    "Build the single-file bundle",
    "Wire a tool to the UI resource",
)


class TaskStore:
    """Thread-safe, in-memory task list.

    Every method returns a fresh `TaskList` snapshot (a copy), so callers can
    never mutate the internal list. Toggling replaces the matched element via
    `model_copy` rather than mutating it in place, keeping the snapshot honest.
    """

    def __init__(self) -> None:
        self._tasks: list[Task] = []
        self._next_id = 1
        self._lock = threading.Lock()
        self._seed()

    def _seed(self) -> None:
        with self._lock:
            self._tasks = [
                Task(id=i, title=title, done=False, created_at=time.time())
                for i, title in enumerate(_SEED_TITLES, start=1)
            ]
            self._next_id = len(self._tasks) + 1

    def list(self) -> TaskList:
        with self._lock:
            return TaskList(tasks=list(self._tasks))

    def add(self, title: str) -> TaskList:
        title = title.strip()
        with self._lock:
            if title:
                self._tasks.append(
                    Task(id=self._next_id, title=title, created_at=time.time())
                )
                self._next_id += 1
            return TaskList(tasks=list(self._tasks))

    def toggle(self, task_id: int) -> TaskList:
        with self._lock:
            self._tasks = [
                t.model_copy(update={"done": not t.done}) if t.id == task_id else t
                for t in self._tasks
            ]
            return TaskList(tasks=list(self._tasks))

    def reset(self) -> TaskList:
        self._seed()
        return self.list()


task_store = TaskStore()


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="list_tasks",
        description=(
            "Return the full task list. Useful for the UI to (re)hydrate the "
            "table without mutating anything."
        ),
        meta=TASKS_UI_META,
    )
    def list_tasks() -> TaskList:
        return task_store.list()

    @mcp.tool(
        name="add_task",
        description="Add a new task with the given `title` and return the full list.",
        meta=TASKS_UI_META,
    )
    def add_task(title: str) -> TaskList:
        return task_store.add(title)

    @mcp.tool(
        name="toggle_task",
        description=(
            "Toggle the done state of the task with the given `id` and return "
            "the full list. Unknown ids are a no-op."
        ),
        meta=TASKS_UI_META,
    )
    def toggle_task(id: int) -> TaskList:
        return task_store.toggle(id)

    @mcp.resource(
        UI_TASKS_RESOURCE_URI,
        name="Tasks App UI",
        description="Single-file HTML bundle for the Tasks MCP App (shared bundle).",
        mime_type=UI_RESOURCE_MIME,
    )
    def tasks_ui() -> str:
        return read_bundle()
