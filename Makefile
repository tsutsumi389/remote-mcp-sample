.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

dev: ## Start dev environment (Docker Compose, mcp-server + mcp-app build:watch)
	docker compose up --build

down: ## Stop dev environment
	docker compose down

build: ## Build React MCP App bundle (apps/mcp-app/dist/index.html)
	pnpm -C apps/mcp-app build

serve-app: ## Serve the MCP App bundle on host (build once, watch + preview on :4173)
	pnpm -C apps/mcp-app serve

serve-server: ## Run the MCP server on host, relaying the bundle over HTTP from :4173
	cd apps/mcp-server && MCP_APP_BUNDLE_URL=http://localhost:4173/ \
		uv run uvicorn mcp_server.server:app --host 127.0.0.1 --port 3001 --reload --reload-dir src

install: ## Install Node and Python dependencies on host (for editor / direct runs)
	pnpm install
	uv sync

test: ## Run Python MCP server unit tests
	cd apps/mcp-server && uv run pytest

clean: ## Remove build artifacts and containers / volumes
	docker compose down -v
	rm -rf apps/mcp-app/dist apps/mcp-app/node_modules apps/mcp-server/.venv

.PHONY: help dev down build serve-app serve-server install test clean
