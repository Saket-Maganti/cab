PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: install test lint smoke help

help:
	@echo "Targets: install, test, lint, smoke"

install:
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

smoke:
	$(PYTHON) -m causal_agent_bench --help
	$(PYTHON) -m causal_agent_bench validate data/sample/instances.jsonl --schema instances
	$(PYTHON) -m causal_agent_bench run --config configs/smoke.yaml
