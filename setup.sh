#!/bin/bash
# Quick start script for the Local Docker Compose Agent

set -e

echo "=== Local Docker Compose Agent Setup ==="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Check if config exists
if [ ! -f "config.yml" ]; then
    echo ""
    echo "⚠ Config file not found!"
    echo "Creating config.yml from config.example.yml..."
    cp config.example.yml config.yml
    
    # Generate a secure token
    TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Update the token in config.yml (basic sed replacement)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your-secret-token-here/$TOKEN/" config.yml
    else
        # Linux
        sed -i "s/your-secret-token-here/$TOKEN/" config.yml
    fi
    
    echo "✓ Config file created with generated token"
    echo ""
    echo "⚠ IMPORTANT: Please edit config.yml and update:"
    echo "  - docker.working_directory (path to your docker-compose.yml directory)"
    echo ""
    echo "Your generated authentication token: $TOKEN"
    echo "Save this token securely - you'll need it for API requests!"
    echo ""
else
    echo "✓ Config file exists"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To start the agent, run:"
echo "  source venv/bin/activate"
echo "  python agent.py"
echo ""
echo "Or simply run: ./start.sh"
echo ""
