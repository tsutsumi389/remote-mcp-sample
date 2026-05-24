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

install: ## Install Node and Python dependencies on host (for editor / direct runs)
	pnpm install
	uv sync

test: ## Run Python MCP server unit tests
	cd apps/mcp-server && uv run pytest

clean: ## Remove build artifacts and containers / volumes
	docker compose down -v
	rm -rf apps/mcp-app/dist apps/mcp-app/node_modules apps/mcp-server/.venv

.PHONY: help dev down build install test clean
