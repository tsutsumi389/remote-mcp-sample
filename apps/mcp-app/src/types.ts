// Shared data shapes + runtime type guards.
//
// The single-file bundle backs two UI resources (ui://counter and ui://tasks).
// The host delivers a tool's result via `ontoolresult`, but that notification
// does not reliably carry the resource URI, so the App routes to a screen by
// inspecting the *shape* of `structuredContent`. These guards are how it tells
// CounterData (`value` + `history`) from TaskList (`tasks`).

export type HistoryPoint = { ts: number; value: number };
export type CounterData = { value: number; history: HistoryPoint[] };

export type Task = {
  id: number;
  title: string;
  done: boolean;
  created_at: number; // seconds since epoch (multiply by 1000 for Date)
};
export type TaskList = { tasks: Task[] };

export function isHistoryPoint(value: unknown): value is HistoryPoint {
  if (!value || typeof value !== "object") return false;
  const p = value as Record<string, unknown>;
  return (
    typeof p.ts === "number" &&
    Number.isFinite(p.ts) &&
    typeof p.value === "number" &&
    Number.isFinite(p.value)
  );
}

export function isCounterData(value: unknown): value is CounterData {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  if (typeof v.value !== "number" || !Number.isFinite(v.value)) return false;
  if (!Array.isArray(v.history)) return false;
  return v.history.every(isHistoryPoint);
}

export function isTask(value: unknown): value is Task {
  if (!value || typeof value !== "object") return false;
  const t = value as Record<string, unknown>;
  return (
    typeof t.id === "number" &&
    Number.isFinite(t.id) &&
    typeof t.title === "string" &&
    typeof t.done === "boolean" &&
    typeof t.created_at === "number" &&
    Number.isFinite(t.created_at)
  );
}

export function isTaskList(value: unknown): value is TaskList {
  if (!value || typeof value !== "object") return false;
  const o = value as Record<string, unknown>;
  return Array.isArray(o.tasks) && o.tasks.every(isTask);
}
