.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	uv sync --all-groups

skills-install: ## Restore agent skills from skills-pack.lock.json
	skills-pack update; skills-pack upgrade

build: ## Type-check the package
	uv run ty check src/

run: ## Run the CLI, for example: make run ARGS="data curate -o data/curated"
	uv run lnp-il $(ARGS)

test: ## Run all tests
	uv run pytest

lint: ## Lint and check formatting
	uv run ruff format --check . && uv run ruff check .

format: ## Format code
	uv run ruff format .

clean: ## Remove caches and coverage output
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov

distclean: clean ## Remove caches and the virtual environment
	rm -rf .venv
