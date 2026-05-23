# Build context is the repository root so the uv workspace lockfile is
# reachable. Compose sets `dockerfile: apps/mcp-server/Dockerfile`.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/root/.local/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

WORKDIR /workspace


FROM base AS dev
# Workspace lock + member manifest first so the install layer can be reused.
COPY pyproject.toml uv.lock ./
COPY apps/mcp-server/pyproject.toml ./apps/mcp-server/
WORKDIR /workspace/apps/mcp-server
RUN uv sync --frozen
# Source is bind-mounted at runtime; copy here so the image is self-contained.
COPY apps/mcp-server/src ./src
COPY apps/mcp-server/tests ./tests
CMD ["uv", "run", "uvicorn", "mcp_server.server:app", "--host", "0.0.0.0", "--port", "3001", "--reload", "--reload-dir", "/workspace/apps/mcp-server/src"]


FROM base AS prod
COPY pyproject.toml uv.lock ./
COPY apps/mcp-server/pyproject.toml ./apps/mcp-server/
WORKDIR /workspace/apps/mcp-server
RUN uv sync --frozen --no-dev
COPY apps/mcp-server/src ./src
EXPOSE 3001
CMD ["uv", "run", "uvicorn", "mcp_server.server:app", "--host", "0.0.0.0", "--port", "3001"]
