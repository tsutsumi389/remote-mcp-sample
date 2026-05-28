import { BarChart } from "./BarChart";
import type { Dashboard, KpiCard } from "./types";

type Props = {
  data: Dashboard;
  isConnected: boolean;
  busy: boolean;
  error: string | null;
  callTool: (name: string, args?: Record<string, unknown>) => Promise<unknown>;
  applyResult: (structuredContent: unknown) => void;
};

function formatValue(card: KpiCard): string {
  const formatted = Number.isInteger(card.value)
    ? card.value.toLocaleString()
    : card.value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  if (card.unit === "$") return `$${formatted}`;
  if (card.unit === "%") return `${formatted}%`;
  return card.unit ? `${formatted} ${card.unit}` : formatted;
}

function formatDelta(deltaPct: number): { text: string; trend: "up" | "down" | "flat" } {
  if (Math.abs(deltaPct) < 0.05) return { text: "0.0%", trend: "flat" };
  const arrow = deltaPct > 0 ? "▲" : "▼";
  return {
    text: `${arrow} ${Math.abs(deltaPct).toFixed(1)}%`,
    trend: deltaPct > 0 ? "up" : "down",
  };
}

function formatTime(epochSeconds: number): string {
  return new Date(epochSeconds * 1000).toLocaleTimeString();
}

export function DashboardScreen({
  data,
  isConnected,
  busy,
  error,
  callTool,
  applyResult,
}: Props) {
  const disabled = busy || !isConnected;

  const run = async (name: string, args?: Record<string, unknown>) => {
    applyResult(await callTool(name, args));
  };

  return (
    <main className="main main-wide">
      <header className="header">
        <h1 className="heading">Dashboard</h1>
        <span className="muted">
          {isConnected ? "connected" : "connecting…"}
          {" · refreshed "}
          {formatTime(data.refreshed_at)}
        </span>
      </header>

      <section className="kpi-grid" aria-label="Key performance indicators">
        {data.kpis.map((card) => {
          const delta = formatDelta(card.delta_pct);
          return (
            <div key={card.label} className="kpi-card">
              <div className="kpi-label">{card.label}</div>
              <div className="kpi-value">{formatValue(card)}</div>
              <div className={`kpi-delta kpi-delta--${delta.trend}`}>
                {delta.text}
              </div>
            </div>
          );
        })}
      </section>

      <section className="value-card">
        <div className="value-label">Trend (7 buckets)</div>
        <BarChart points={data.trend} width={440} height={140} />
      </section>

      <section className="value-card">
        <div className="value-label">Recent activity</div>
        {data.activity.length === 0 ? (
          <p className="task-empty">All clear — no alerts.</p>
        ) : (
          <ul className="activity-list">
            {data.activity.map((item) => (
              <li key={item.id} className="activity-row">
                <span
                  className={`severity-badge severity-badge--${item.severity}`}
                >
                  {item.severity}
                </span>
                <span className="activity-message">{item.message}</span>
                <button
                  type="button"
                  className="btn btn-small"
                  disabled={disabled}
                  onClick={() => run("acknowledge_alert", { alert_id: item.id })}
                  aria-label={`Acknowledge "${item.message}"`}
                >
                  Ack
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="actions actions-dashboard">
        <button
          type="button"
          className="btn"
          disabled={disabled}
          onClick={() => run("refresh_dashboard")}
        >
          Refresh
        </button>
        <button
          type="button"
          className="btn btn-ghost"
          disabled={disabled}
          onClick={() => run("get_dashboard")}
        >
          Reload
        </button>
      </section>

      {error && <p className="error">{error}</p>}
    </main>
  );
}
