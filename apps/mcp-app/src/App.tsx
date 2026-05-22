import { useCallback, useState } from "react";
import { useApp } from "@modelcontextprotocol/ext-apps/react";

import { Chart } from "./Chart";

export type HistoryPoint = { ts: number; value: number };
export type CounterData = { value: number; history: HistoryPoint[] };

const EMPTY: CounterData = { value: 0, history: [] };

function applyHostContext(ctx: {
  theme?: string;
  safeAreaInsets?: { top: number; right: number; bottom: number; left: number };
}): void {
  if (ctx.theme) {
    document.documentElement.dataset.theme = ctx.theme;
  }
  if (ctx.safeAreaInsets) {
    const { top, right, bottom, left } = ctx.safeAreaInsets;
    document.body.style.padding = `${top}px ${right}px ${bottom}px ${left}px`;
  }
}

export function App() {
  const [data, setData] = useState<CounterData>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { app, isConnected } = useApp({
    appInfo: { name: "Counter App", version: "1.0.0" },
    capabilities: {},
    onAppCreated: (createdApp) => {
      // Hydrate from model-initiated tool result.
      createdApp.ontoolresult = (event) => {
        const structuredContent = event?.structuredContent;
        if (isCounterData(structuredContent)) {
          setData(structuredContent);
        } else if (structuredContent !== undefined) {
          setError("Unexpected tool result payload from server");
        }
      };
      // Hook signature only — illustrative, not used in this sample.
      createdApp.ontoolinputpartial = () => {};
      // Theme + safe-area follow the host.
      createdApp.onhostcontextchanged = (ctx) => applyHostContext(ctx);
      createdApp.onteardown = async () => ({});
    },
  });

  const callTool = useCallback(
    async (name: string, args: Record<string, unknown> = {}) => {
      if (!app) return;
      setBusy(true);
      setError(null);
      try {
        const result = await app.callServerTool({ name, arguments: args });
        const structured = result?.structuredContent;
        if (isCounterData(structured)) {
          setData(structured);
        } else {
          setError(`Unexpected response shape from ${name}`);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setBusy(false);
      }
    },
    [app],
  );

  return (
    <main className="main">
      <header className="header">
        <h1 className="heading">Counter</h1>
        <span className="muted">{isConnected ? "connected" : "connecting…"}</span>
      </header>

      <section className="value-card">
        <div className="value-label">current value</div>
        <div className="value">{data.value}</div>
      </section>

      <section className="chart-card">
        <Chart history={data.history} />
      </section>

      <section className="actions">
        <button
          type="button"
          className="btn"
          disabled={busy || !isConnected}
          onClick={() => callTool("increment_counter", { by: 1 })}
        >
          +1
        </button>
        <button
          type="button"
          className="btn"
          disabled={busy || !isConnected}
          onClick={() => callTool("increment_counter", { by: 5 })}
        >
          +5
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          disabled={busy || !isConnected}
          onClick={() => callTool("reset_counter")}
        >
          Reset
        </button>
        <button
          type="button"
          className="btn btn-ghost"
          disabled={busy || !isConnected}
          onClick={() => callTool("get_counter")}
        >
          Refresh
        </button>
      </section>

      {error && <p className="error">{error}</p>}
    </main>
  );
}

function isCounterData(value: unknown): value is CounterData {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  if (typeof v.value !== "number" || !Number.isFinite(v.value)) return false;
  if (!Array.isArray(v.history)) return false;
  return v.history.every(isHistoryPoint);
}

function isHistoryPoint(value: unknown): value is HistoryPoint {
  if (!value || typeof value !== "object") return false;
  const p = value as Record<string, unknown>;
  return (
    typeof p.ts === "number" &&
    Number.isFinite(p.ts) &&
    typeof p.value === "number" &&
    Number.isFinite(p.value)
  );
}
