import { Chart } from "./Chart";
import type { CounterData } from "./types";

type Props = {
  data: CounterData;
  isConnected: boolean;
  busy: boolean;
  error: string | null;
  callTool: (name: string, args?: Record<string, unknown>) => Promise<unknown>;
  applyResult: (structuredContent: unknown) => void;
};

export function CounterScreen({
  data,
  isConnected,
  busy,
  error,
  callTool,
  applyResult,
}: Props) {
  const run = async (name: string, args?: Record<string, unknown>) => {
    applyResult(await callTool(name, args));
  };

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
          onClick={() => run("increment_counter", { by: 1 })}
        >
          +1
        </button>
        <button
          type="button"
          className="btn"
          disabled={busy || !isConnected}
          onClick={() => run("increment_counter", { by: 5 })}
        >
          +5
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          disabled={busy || !isConnected}
          onClick={() => run("reset_counter")}
        >
          Reset
        </button>
        <button
          type="button"
          className="btn btn-ghost"
          disabled={busy || !isConnected}
          onClick={() => run("get_counter")}
        >
          Refresh
        </button>
      </section>

      {error && <p className="error">{error}</p>}
    </main>
  );
}
