# Virtual environment setup
venv:
	python3 -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

# Install dependencies
install:
	pip install -r requirements.txt

# Setup project (create venv and install dependencies)
setup: venv activate
	@echo "Activating virtual environment and installing dependencies..."
	pip install -r requirements.txt
	@echo "Setup complete! Activate the environment with: source venv/bin/activate"

# Activate virtual environment (shows activation command)
activate: 
	@echo "To activate the virtual environment, run:"
	@echo "source venv/bin/activate"
	@echo ""
	@echo "To deactivate later, simply run: deactivate"

# Run the trading script
trade: activate
	python trading_script.py $(ARGS)

graph: activate
	python "Start Your Own/Generate_Graph.py" $(ARGS) 


# Clean up virtual environment
clean:
	rm -rf venv
	@echo "Virtual environment removed"

.PHONY: venv install setup activate trade clean

