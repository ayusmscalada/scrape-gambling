#!/bin/bash
# Script to start the Python API server

cd "$(dirname "$0")"

echo "Starting Python API server..."
echo "Press Ctrl+C to stop"
echo ""

python3 run_server.py
