FROM node:22-alpine AS base
RUN corepack enable
WORKDIR /workspace


FROM base AS dev
# Copy manifests first so the layer is reused when only source changes.
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --no-frozen-lockfile
# Source is bind-mounted at runtime; we still copy here so the image is
# self-contained for one-off `docker run` use.
COPY . .
CMD ["pnpm", "build:watch"]


FROM base AS prod
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --no-frozen-lockfile
COPY . .
RUN pnpm build
