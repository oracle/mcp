#!/bin/bash
"""
Setup script for lens MCP server
"""

set -e

echo "🚀 Setting up lens MCP server..."

# Create virtual environment if it doesn't exist
if [ ! -d "lens-mcp-env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv lens-mcp-env
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source lens-mcp-env/bin/activate

# Install requirements
echo "📥 Installing requirements..."
pip install -r requirements.txt

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p logs

echo "✅ Setup complete!"
echo ""
echo "To run the server:"
echo "1. Set environment variables:"
echo "   export LENS_API_BASE_URL='http://your-lens-api-url'"
echo "   export LENS_API_KEY='your-api-key'"
echo "2. Activate the environment: source lens-mcp-env/bin/activate"
echo "3. Run the server: python server.py"
