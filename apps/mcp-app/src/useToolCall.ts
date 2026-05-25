import { useCallback, useState } from "react";
import type { useApp } from "@modelcontextprotocol/ext-apps/react";

type AppLike = ReturnType<typeof useApp>["app"];

// Screen-agnostic tool calling: invokes a server tool and returns the raw
// `structuredContent`, leaving the caller to route/validate it. Both the
// Counter and Tasks screens share this `busy`/`error` machinery.
export function useToolCall(app: AppLike) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const callTool = useCallback(
    async (
      name: string,
      args: Record<string, unknown> = {},
    ): Promise<unknown> => {
      if (!app) return undefined;
      setBusy(true);
      setError(null);
      try {
        const result = await app.callServerTool({ name, arguments: args });
        return result?.structuredContent;
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        return undefined;
      } finally {
        setBusy(false);
      }
    },
    [app],
  );

  return { callTool, busy, error, setError };
}
