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
# In dev, source is bind-mounted. We install deps from the project metadata
# so the .venv is pre-warmed inside the image.
COPY pyproject.toml ./
COPY src ./src
RUN uv sync
CMD ["uv", "run", "uvicorn", "mcp_server.server:app", "--host", "0.0.0.0", "--port", "3001", "--reload", "--reload-dir", "/workspace/src"]


FROM base AS prod
COPY pyproject.toml ./
COPY src ./src
RUN uv sync --no-dev
EXPOSE 3001
CMD ["uv", "run", "uvicorn", "mcp_server.server:app", "--host", "0.0.0.0", "--port", "3001"]
