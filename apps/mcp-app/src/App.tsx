import { useCallback, useState } from "react";
import { useApp } from "@modelcontextprotocol/ext-apps/react";

import { CounterScreen } from "./CounterScreen";
import { DashboardScreen } from "./DashboardScreen";
import { TasksScreen } from "./TasksScreen";
import {
  isCounterData,
  isDashboard,
  isTaskList,
  type CounterData,
  type Dashboard,
  type TaskList,
} from "./types";
import { useToolCall } from "./useToolCall";

// This single bundle backs three UI resources (ui://counter, ui://tasks,
// ui://dashboard). The host loads one iframe per resource render and delivers
// that tool's result via `ontoolresult`. The notification does not reliably
// carry the resource URI, so we route to a screen by the *shape* of the
// structured content received.
type Screen =
  | { kind: "loading" }
  | { kind: "counter"; data: CounterData }
  | { kind: "tasks"; data: TaskList }
  | { kind: "dashboard"; data: Dashboard };

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
  const [screen, setScreen] = useState<Screen>({ kind: "loading" });
  const [routeError, setRouteError] = useState<string | null>(null);

  // Single source of truth for routing, used by both `ontoolresult` (model-
  // initiated) and each screen's tool-call responses. The three shapes are
  // mutually exclusive; order is defensive (most specific keys first).
  const applyResult = useCallback((structuredContent: unknown) => {
    if (isDashboard(structuredContent)) {
      setRouteError(null);
      setScreen({ kind: "dashboard", data: structuredContent });
    } else if (isTaskList(structuredContent)) {
      setRouteError(null);
      setScreen({ kind: "tasks", data: structuredContent });
    } else if (isCounterData(structuredContent)) {
      setRouteError(null);
      setScreen({ kind: "counter", data: structuredContent });
    } else if (structuredContent !== undefined) {
      setRouteError("Unexpected tool result payload from server");
    }
  }, []);

  const { app, isConnected } = useApp({
    appInfo: { name: "MCP Apps Sample", version: "1.0.0" },
    capabilities: {},
    onAppCreated: (createdApp) => {
      createdApp.ontoolresult = (event) => applyResult(event?.structuredContent);
      // Hook signature only — illustrative, not used in this sample.
      createdApp.ontoolinputpartial = () => {};
      // Theme + safe-area follow the host.
      createdApp.onhostcontextchanged = (ctx) => applyHostContext(ctx);
      createdApp.onteardown = async () => ({});
    },
  });

  const { callTool, busy, error: toolError } = useToolCall(app);
  const error = toolError ?? routeError;

  if (screen.kind === "dashboard") {
    return (
      <DashboardScreen
        data={screen.data}
        isConnected={isConnected}
        busy={busy}
        error={error}
        callTool={callTool}
        applyResult={applyResult}
      />
    );
  }

  if (screen.kind === "tasks") {
    return (
      <TasksScreen
        data={screen.data}
        isConnected={isConnected}
        busy={busy}
        error={error}
        callTool={callTool}
        applyResult={applyResult}
      />
    );
  }

  if (screen.kind === "counter") {
    return (
      <CounterScreen
        data={screen.data}
        isConnected={isConnected}
        busy={busy}
        error={error}
        callTool={callTool}
        applyResult={applyResult}
      />
    );
  }

  return (
    <main className="main">
      <header className="header">
        <h1 className="heading">MCP Apps Sample</h1>
        <span className="muted">{isConnected ? "connected" : "connecting…"}</span>
      </header>
      <section className="value-card">
        <p className="muted">
          Waiting for data — invoke a tool (e.g. <code>get_counter</code>,{" "}
          <code>list_tasks</code>, or <code>get_dashboard</code>) to load a
          screen.
        </p>
      </section>
      {error && <p className="error">{error}</p>}
    </main>
  );
}
