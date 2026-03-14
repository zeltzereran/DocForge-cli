.PHONY: help install install-dev test lint format type-check clean

help:
	@echo "DocForge Development Commands"
	@echo "============================="
	@echo "make install         - Install package in editable mode"
	@echo "make install-dev     - Install with dev dependencies"
	@echo "make test            - Run tests with coverage"
	@echo "make lint            - Run linting checks"
	@echo "make format          - Auto-format code"
	@echo "make type-check      - Run type checking"
	@echo "make clean           - Clean build artifacts"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest --cov=docforge --cov-report=html

test-fast:
	pytest -x -v

lint:
	ruff check docforge tests
	black --check docforge tests

format:
	black docforge tests
	ruff check --fix docforge tests

type-check:
	mypy docforge

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	rm -rf build dist htmlcov .coverage .pytest_cache .mypy_cache
