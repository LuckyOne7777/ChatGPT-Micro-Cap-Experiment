# Makefile for ChatGPT Micro Cap Experiment Report Generator

# Default target
.PHONY: help
help:
	@echo "ChatGPT Micro Cap Experiment Report Generator"
	@echo "=========================================="
	@echo "Available targets:"
	@echo "  run              - Generate report for today"
	@echo "  run-date DATE=   - Generate report for specific date"
	@echo "  test             - Run unit tests"
	@echo "  test-imports     - Test module imports"
	@echo "  clean            - Clean generated reports"
	@echo "  install-deps     - Install dependencies"
	@echo "  help             - Show this help message"

# Run report for today
.PHONY: run
run:
	python3 run_report.py

# Run report for specific date
.PHONY: run-date
run-date:
	python3 run_report.py --date $(DATE)

# Run unit tests
.PHONY: test
test:
	python3 -m unittest discover tests

# Test module imports
.PHONY: test-imports
test-imports:
	python3 test_modules.py

# Clean generated reports
.PHONY: clean
clean:
	rm -rf Reports/*

# Install dependencies
.PHONY: install-deps
install-deps:
	pip install -r requirements.txt

# Show help by default
.DEFAULT_GOAL := help