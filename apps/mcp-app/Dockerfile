# Build context is the repository root so the pnpm workspace lockfile is
# reachable. Compose sets `dockerfile: apps/mcp-app/Dockerfile`.
FROM node:22-alpine AS base
RUN corepack enable
WORKDIR /workspace


FROM base AS dev
# Workspace manifests first so the install layer can be reused.
COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY apps/mcp-app/package.json ./apps/mcp-app/
RUN pnpm install --frozen-lockfile --filter mcp-app...
# Source is bind-mounted at runtime; copy here so the image is self-contained.
COPY apps/mcp-app/ ./apps/mcp-app/
WORKDIR /workspace/apps/mcp-app
# Build once, then watch + serve the single-file bundle over HTTP (port 4173).
EXPOSE 4173
CMD ["pnpm", "serve"]


FROM base AS prod
COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY apps/mcp-app/package.json ./apps/mcp-app/
RUN pnpm install --frozen-lockfile --filter mcp-app...
COPY apps/mcp-app/ ./apps/mcp-app/
WORKDIR /workspace/apps/mcp-app
RUN pnpm build
