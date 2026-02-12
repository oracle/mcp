#!/bin/bash
"""
Run script for lens MCP server
"""

set -e

echo "🚀 Starting lens MCP server..."

# Check if virtual environment exists
if [ ! -d "lens-mcp-env" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source lens-mcp-env/bin/activate

# Check required environment variables
if [ -z "$LENS_API_BASE_URL" ]; then
    echo "⚠️  LENS_API_BASE_URL not set, using default: http://localhost:8000"
    export LENS_API_BASE_URL="http://localhost:8000"
fi

echo "🌐 Lens API Base URL: $LENS_API_BASE_URL"

if [ -n "$LENS_API_KEY" ]; then
    echo "🔑 API Key configured"
else
    echo "⚠️  No API key configured. Set LENS_API_KEY if required."
fi

# Create logs directory if it doesn't exist
mkdir -p logs

echo "▶️  Starting server..."
python server.py
