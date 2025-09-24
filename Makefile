# Makefile for ChatGPT Micro Cap Experiment Report Generator

# Default target
.PHONY: help
help:
	@echo "ChatGPT Micro Cap Experiment Report Generator"
	@echo "=========================================="
	@echo "Available targets:"
	@echo "  venv             - Create virtual environment"
	@echo "  activate         - Activate virtual environment"
	@echo "  setup            - Setup project (create venv and install dependencies)"
	@echo "  install-deps     - Install dependencies"
	@echo "  trade            - Run the trading script"
	@echo "  graph            - Run the graph script"
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

# Virtual environment setup
.PHONY: venv
venv:
	python3 -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

# Install dependencies
.PHONY: install-deps
install-deps:
	pip install -r requirements.txt

# Setup project (create venv and install dependencies)
.PHONY: setup
setup: venv activate
	@echo "Activating virtual environment and installing dependencies..."
	pip install -r requirements.txt
	@echo "Setup complete! Activate the environment with: source venv/bin/activate"

# Activate virtual environment (shows activation command)
.PHONY: activate
activate:
	@echo "To activate the virtual environment, run:"
	@echo "source venv/bin/activate"
	@echo ""
	@echo "To deactivate later, simply run: deactivate"

# Run the trading script
.PHONY: trade
trade: activate
	python trading_script.py $(ARGS)

.PHONY: graph
graph: activate
	python "Start Your Own/Generate_Graph.py" $(ARGS) 

# Clean up virtual environment
clean:
	rm -rf venv
	@echo "Virtual environment removed"
	rm -rf Reports/*

# .PHONY: venv install setup activate trade clean

# Show help by default
.DEFAULT_GOAL := help
