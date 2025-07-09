.PHONY: help install install-dev test test-coverage lint format type-check clean build docs serve-docs docker-build docker-up docker-down

# Colors
YELLOW := \033[1;33m
NC := \033[0m # No Color

# Default target
help:
	@echo "$(YELLOW)InferLine Development Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Setup:$(NC)"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo ""
	@echo "$(YELLOW)Development:$(NC)"
	@echo "  test         Run tests"
	@echo "  test-cov     Run tests with coverage"
	@echo "  lint         Run linting (flake8)"
	@echo "  format       Format code (black, isort)"
	@echo "  type-check   Run type checking (mypy)"
	@echo "  clean        Clean build artifacts"
	@echo ""
	@echo "$(YELLOW)Build:$(NC)"
	@echo "  build        Build package"
	@echo "  docs         Build documentation"
	@echo "  serve-docs   Serve documentation locally"
	@echo ""
	@echo "$(YELLOW)Docker:$(NC)"
	@echo "  docker-build Build Docker images"
	@echo "  docker-up    Start services with Docker Compose"
	@echo "  docker-down  Stop Docker Compose services"
	@echo ""
	@echo "$(YELLOW)Services:$(NC)"
	@echo "  gateway      Start gateway server"
	@echo "  provider     Start provider client"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev,docs,monitoring]"
	pre-commit install

test:
	pytest tests/

test-cov:
	pytest tests/ --cov=inferline --cov-report=html --cov-report=term

lint:
	flake8 src/inferline tests/
	black --check src/inferline tests/
	isort --check-only src/inferline tests/

format:
	black src/inferline tests/
	isort src/inferline tests/

type-check:
	mypy src/inferline

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

docs:
	mkdocs build

serve-docs:
	mkdocs serve

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

gateway:
	python -m inferline.gateway.app

provider:
	python -m inferline.provider.client

# Development shortcuts
dev-setup: install-dev
	@echo "$(YELLOW)Development environment setup complete!$(NC)"

dev-check: lint type-check test
	@echo "$(YELLOW)All checks passed!$(NC)"