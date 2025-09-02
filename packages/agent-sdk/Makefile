# Makefile for Agent SDK Testing

.PHONY: test test-unit test-integration test-watch test-cov test-fast help clean lint lint-fix typecheck

# Default target
help:
	@echo "Available targets:"
	@echo "  test         - Run all tests"
	@echo "  test-unit    - Run only unit tests" 
	@echo "  test-unit-single - Run single unit test by pattern"
	@echo "  test-integration - Run only integration tests"
	@echo "  test-fast    - Run fast tests (exclude slow tests)"
	@echo "  test-watch   - Run tests in watch mode"
	@echo "  test-cov     - Run tests with coverage report"
	@echo "  test-html    - Run tests with HTML coverage report"
	@echo "  lint         - Run linting checks"
	@echo "  lint-fix     - Run linting with auto-fix"
	@echo "  typecheck    - Run type checking with mypy"
	@echo "  clean        - Clean test artifacts"

# Run all tests
test:
	uv run python3 -m pytest tests/

# Run only unit tests
test-unit:
	uv run python3 -m pytest tests/unit/ -m "unit" --no-cov

# Run single unit test by pattern
test-unit-single:
	@if [ -z "$(PATTERN)" ]; then echo "Usage: make test-unit-single PATTERN=test_name_pattern"; exit 1; fi
	LOG_LEVEL=DEBUG uv run python3 -m pytest tests/unit/ -m "unit" --no-cov -k "$(PATTERN)" -v

# Run only integration tests  
test-integration:
	uv run python3 -m pytest tests/integration/ -m "integration"

# Run fast tests (exclude slow ones)
test-fast:
	uv run python3 -m pytest tests/ -m "not slow"

# Run tests in watch mode (requires pytest-watch)
test-watch:
	uv run pytest-watch --clear

# Run tests with coverage
test-cov:
	uv run python3 -m pytest --cov=siili_ai_sdk --cov-report=term-missing

# Run tests with HTML coverage report
test-html:
	uv run python3 -m pytest --cov=siili_ai_sdk --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

# Run specific test file
test-file:
	@if [ -z "$(FILE)" ]; then echo "Usage: make test-file FILE=path/to/test_file.py"; exit 1; fi
	uv run python3 -m pytest $(FILE) -v

# Run tests matching a pattern
test-pattern:
	@if [ -z "$(PATTERN)" ]; then echo "Usage: make test-pattern PATTERN=test_name_pattern"; exit 1; fi
	uv run python3 -m pytest -k "$(PATTERN)" -v

# Run linting checks
lint:
	uv run ruff check .

# Run linting with auto-fix
lint-fix:
	uv run ruff check --fix --unsafe-fixes .
	uv run ruff format .

# Run type checking
typecheck:
	uv run ty check siili_ai_sdk tests

# Clean test artifacts
clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Debug tests (run with verbose output and no capture)
test-debug:
	uv run python3 -m pytest tests/ -v -s --tb=long

# Run tests and generate JUnit XML (for CI)
test-ci:
	uv run python3 -m pytest tests/ --junitxml=test-results.xml --cov=siili_ai_sdk --cov-report=xml 