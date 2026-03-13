#!/bin/bash
# Quick start script for running Puppeteer service locally

cd "$(dirname "$0")"

echo "🚀 Starting Puppeteer service locally..."
echo ""

# Check Node.js version
NODE_VERSION=$(node --version 2>/dev/null | cut -d'v' -f2 | cut -d'.' -f1)
if [ -z "$NODE_VERSION" ]; then
    echo "❌ Error: Node.js is not installed"
    echo "   Install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

if [ "$NODE_VERSION" -lt 18 ]; then
    echo "⚠️  Warning: Node.js version is $NODE_VERSION, recommended: 18+"
fi

echo "✅ Node.js version: $(node --version)"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    echo ""
fi

# Check if browser is installed
CACHE_DIR="${PUPPETEER_CACHE_DIR:-$HOME/.cache/puppeteer}"
if [ ! -d "$CACHE_DIR" ] || [ -z "$(ls -A $CACHE_DIR 2>/dev/null)" ]; then
    echo "🌐 Installing Puppeteer browser (this may take a few minutes)..."
    npx puppeteer install chrome
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install browser"
        exit 1
    fi
    echo ""
fi

# Create profiles directory
PROFILES_DIR="../profiles"
if [ ! -d "$PROFILES_DIR" ]; then
    echo "📁 Creating profiles directory..."
    mkdir -p "$PROFILES_DIR"
    echo ""
fi

# Set default port if not set
export PORT=${PORT:-3000}

echo "✅ Setup complete!"
echo ""
echo "Starting server on port $PORT..."
echo "Health check: http://localhost:$PORT/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start server
node server.js
