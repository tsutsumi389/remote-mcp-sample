import { useState } from "react";

import type { TaskList } from "./types";

type Props = {
  data: TaskList;
  isConnected: boolean;
  busy: boolean;
  error: string | null;
  callTool: (name: string, args?: Record<string, unknown>) => Promise<unknown>;
  applyResult: (structuredContent: unknown) => void;
};

function formatTime(epochSeconds: number): string {
  // Server stores time.time() in seconds; Date wants milliseconds.
  return new Date(epochSeconds * 1000).toLocaleTimeString();
}

export function TasksScreen({
  data,
  isConnected,
  busy,
  error,
  callTool,
  applyResult,
}: Props) {
  const [draft, setDraft] = useState("");
  const disabled = busy || !isConnected;

  const run = async (name: string, args?: Record<string, unknown>) => {
    applyResult(await callTool(name, args));
  };

  const onAdd = async (event: React.FormEvent) => {
    event.preventDefault();
    const title = draft.trim();
    if (!title) return;
    await run("add_task", { title });
    setDraft("");
  };

  return (
    <main className="main">
      <header className="header">
        <h1 className="heading">Tasks</h1>
        <span className="muted">{isConnected ? "connected" : "connecting…"}</span>
      </header>

      <form className="task-form" onSubmit={onAdd}>
        <input
          className="task-input"
          type="text"
          placeholder="Add a task…"
          value={draft}
          disabled={disabled}
          onChange={(e) => setDraft(e.target.value)}
        />
        <button type="submit" className="btn" disabled={disabled || !draft.trim()}>
          Add
        </button>
      </form>

      <section className="value-card">
        <table className="task-table">
          <thead>
            <tr>
              <th>Done</th>
              <th>Task</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {data.tasks.length === 0 ? (
              <tr>
                <td className="task-empty" colSpan={3}>
                  No tasks yet — add one above.
                </td>
              </tr>
            ) : (
              data.tasks.map((task) => (
                <tr key={task.id}>
                  <td>
                    <input
                      type="checkbox"
                      checked={task.done}
                      disabled={disabled}
                      aria-label={`Toggle "${task.title}"`}
                      onChange={() => run("toggle_task", { id: task.id })}
                    />
                  </td>
                  <td>
                    <span className={task.done ? "task-title done" : "task-title"}>
                      {task.title}
                    </span>
                  </td>
                  <td className="task-created">{formatTime(task.created_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      <section className="actions">
        <button
          type="button"
          className="btn btn-ghost"
          disabled={disabled}
          onClick={() => run("list_tasks")}
        >
          Refresh
        </button>
      </section>

      {error && <p className="error">{error}</p>}
    </main>
  );
}
