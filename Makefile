.PHONY: help dev up down logs shell-api shell-db test lint format reset-data clean status

# Load workspace port assignments if present
PORTS_FILE := ../workspace-config/ports/.env.ports
ifneq (,$(wildcard $(PORTS_FILE)))
include $(PORTS_FILE)
export
endif

CANOPY_FRONTEND_PORT ?= 3001
CANOPY_API_PORT      ?= 8001
CANOPY_POSTGRES_PORT ?= 5433
CANOPY_REDIS_PORT    ?= 6380

help: ## Show this help
	@echo "Canopy — available commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "URLs once running:"
	@echo "  Frontend : http://localhost:$(CANOPY_FRONTEND_PORT)"
	@echo "  API docs : http://localhost:$(CANOPY_API_PORT)/docs"
	@echo "  Postgres : localhost:$(CANOPY_POSTGRES_PORT)"

dev: ## Start full dev stack in Docker (hot reload on both sides) and tail logs
	@./scripts/local-dev.sh

up: ## Start full dev stack in the background
	@docker-compose up -d
	@echo ""
	@echo "✅ Canopy is up."
	@echo "   Frontend : http://localhost:$(CANOPY_FRONTEND_PORT)"
	@echo "   API docs : http://localhost:$(CANOPY_API_PORT)/docs"

down: ## Stop the dev stack
	@docker-compose down

logs: ## Tail logs from all services
	@docker-compose logs -f

status: ## Show container status + URLs
	@docker-compose ps
	@echo ""
	@echo "Frontend : http://localhost:$(CANOPY_FRONTEND_PORT)"
	@echo "API docs : http://localhost:$(CANOPY_API_PORT)/docs"

shell-api: ## Shell into the running API container
	@docker-compose exec api bash

shell-db: ## Psql shell into the Postgres container
	@docker-compose exec postgres psql -U postgres -d canopy

test: ## Run backend tests inside the API container
	@docker-compose exec api pytest -q

lint: ## Run ruff + tsc
	@.venv/bin/ruff check backend/ && echo "✅ ruff clean"
	@cd frontend && npx tsc --noEmit && echo "✅ tsc clean"

format: ## Auto-format Python
	@.venv/bin/ruff format backend/
	@.venv/bin/ruff check backend/ --fix

reset-data: ## Delete every row from every data table (schema preserved)
	@docker-compose exec api python -m backend.scripts.reset_data

clean: ## Remove build artifacts and caches (not venv)
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name '*.pyc' -delete
	@rm -rf frontend/.next frontend/tsconfig.tsbuildinfo
	@rm -rf .pytest_cache .ruff_cache
