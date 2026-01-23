#!/bin/bash
# Crusoe Dashboard Startup Script
# This script starts the Flask API server that serves the dashboard

cd "$(dirname "$0")/backend"

echo "========================================"
echo "Crusoe Cloud Dashboard"
echo "========================================"
echo ""
echo "Starting Flask server..."
echo "Dashboard will be available at:"
echo "  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
