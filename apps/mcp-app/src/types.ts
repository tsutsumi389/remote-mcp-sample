// Shared data shapes + runtime type guards.
//
// The single-file bundle backs three UI resources (ui://counter, ui://tasks,
// ui://dashboard). The host delivers a tool's result via `ontoolresult`, but
// that notification does not reliably carry the resource URI, so the App
// routes to a screen by inspecting the *shape* of `structuredContent`. These
// guards are how it tells CounterData (`value` + `history`) from TaskList
// (`tasks`) from Dashboard (`kpis` + `trend` + `activity`).

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

export type Severity = "info" | "warn" | "error";

export type KpiCard = {
  label: string;
  value: number;
  unit: string;
  delta_pct: number;
};

export type TrendPoint = { label: string; value: number };

export type ActivityItem = {
  id: string;
  message: string;
  severity: Severity;
  created_at: number;
};

export type Dashboard = {
  kpis: KpiCard[];
  trend: TrendPoint[];
  activity: ActivityItem[];
  refreshed_at: number;
};

export function isKpiCard(value: unknown): value is KpiCard {
  if (!value || typeof value !== "object") return false;
  const k = value as Record<string, unknown>;
  return (
    typeof k.label === "string" &&
    typeof k.value === "number" &&
    Number.isFinite(k.value) &&
    typeof k.unit === "string" &&
    typeof k.delta_pct === "number" &&
    Number.isFinite(k.delta_pct)
  );
}

export function isTrendPoint(value: unknown): value is TrendPoint {
  if (!value || typeof value !== "object") return false;
  const p = value as Record<string, unknown>;
  return (
    typeof p.label === "string" &&
    typeof p.value === "number" &&
    Number.isFinite(p.value)
  );
}

export function isSeverity(value: unknown): value is Severity {
  return value === "info" || value === "warn" || value === "error";
}

export function isActivityItem(value: unknown): value is ActivityItem {
  if (!value || typeof value !== "object") return false;
  const a = value as Record<string, unknown>;
  return (
    typeof a.id === "string" &&
    typeof a.message === "string" &&
    isSeverity(a.severity) &&
    typeof a.created_at === "number" &&
    Number.isFinite(a.created_at)
  );
}

export function isDashboard(value: unknown): value is Dashboard {
  if (!value || typeof value !== "object") return false;
  const d = value as Record<string, unknown>;
  if (!Array.isArray(d.kpis) || !d.kpis.every(isKpiCard)) return false;
  if (!Array.isArray(d.trend) || !d.trend.every(isTrendPoint)) return false;
  if (!Array.isArray(d.activity) || !d.activity.every(isActivityItem)) return false;
  return typeof d.refreshed_at === "number" && Number.isFinite(d.refreshed_at);
}
