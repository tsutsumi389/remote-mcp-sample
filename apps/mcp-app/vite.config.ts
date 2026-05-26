import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig({
  plugins: [react(), viteSingleFile()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
    cssCodeSplit: false,
    assetsInlineLimit: 100_000_000,
    chunkSizeWarningLimit: 100_000,
  },
  preview: {
    host: "0.0.0.0", // bind all interfaces so the mcp-server container can reach it
    port: 4173,
    strictPort: true, // fail fast instead of silently picking another port
    // Vite 6 rejects requests whose Host header is not allowlisted. The
    // mcp-server fetches via the compose service name "mcp-app", so allow it
    // alongside the host-dev names.
    allowedHosts: ["mcp-app", "localhost", "127.0.0.1"],
  },
});
