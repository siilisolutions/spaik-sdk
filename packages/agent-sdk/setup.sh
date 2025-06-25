#!/bin/bash

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

echo "Setup complete! To start the server, run:"
echo "source venv/bin/activate && python main.py" 