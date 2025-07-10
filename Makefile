.PHONY: help install install-dev test test-coverage lint format type-check clean build docker-build docker-up docker-down

SHELL := /bin/bash

venv:
	python3 -m venv --prompt "infer" venv

pip-install:
	source venv/bin/activate && pip install -e ".[dev]"

test:
	pytest tests/

dev-setup: venv pip-install
