.DEFAULT_GOAL := help
BACKEND := backend
FRONTEND := frontend

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Install backend + frontend dependencies
	cd $(BACKEND) && uv sync
	cd $(FRONTEND) && npm install
	uv run --project $(BACKEND) pre-commit install

dev-api: ## Run the Django dev server
	cd $(BACKEND) && uv run python manage.py runserver

dev-web: ## Run the Vite dev server
	cd $(FRONTEND) && npm run dev

migrate: ## Apply database migrations
	cd $(BACKEND) && uv run python manage.py migrate

seed: ## Load Moroccan holidays from YAML into the database
	cd $(BACKEND) && uv run python manage.py seed_holidays

test: ## Run every test suite
	cd $(BACKEND) && uv run pytest
	cd $(FRONTEND) && npm run test

lint: ## Lint and type-check everything
	cd $(BACKEND) && uv run ruff check . && uv run ruff format --check . && uv run mypy .
	cd $(FRONTEND) && npm run lint && npm run typecheck

format: ## Auto-format everything
	cd $(BACKEND) && uv run ruff check --fix . && uv run ruff format .
	cd $(FRONTEND) && npm run format

types: ## Regenerate frontend API types from the live OpenAPI schema
	cd $(FRONTEND) && npm run api:types

.PHONY: help install dev-api dev-web migrate seed test lint format types
