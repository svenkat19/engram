.PHONY: install dev test lint typecheck fmt run dashboard clean

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest -v --tb=short

test-cov:
	pytest -v --cov=engram --cov-report=term-missing

lint:
	ruff check src/ tests/

typecheck:
	mypy src/engram/

fmt:
	ruff format src/ tests/
	ruff check --fix src/ tests/

run:
	uvicorn engram.api.app:create_app --factory --host 127.0.0.1 --port 8741 --reload

dashboard:
	cd dashboard && npm install && npm run build

clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
