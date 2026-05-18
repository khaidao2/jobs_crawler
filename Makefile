.PHONY: help generate-dags check-dags

PYTHONPATH := $(shell pwd)
export PYTHONPATH

help:
	@echo "Available commands:"
	@echo "  make generate-dags  - Generate DAG Python files from YAML configs"
	@echo "  make check-dags     - Validate YAML configs without writing"

generate-dags:
	@echo "Generating DAG files..."
	python -m src.airflow.generator.cli --write

check-dags:
	@echo "Validating DAG configs..."
	python -m src.airflow.generator.cli --check