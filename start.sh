#!/bin/bash
# Start script for the Local Docker Compose Agent

set -e

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup first..."
    ./setup.sh
fi

# Activate virtual environment
source venv/bin/activate

# Check if config exists
if [ ! -f "config.yml" ]; then
    echo "Error: config.yml not found!"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Start the agent
echo "Starting Local Docker Compose Agent..."
python agent.py
