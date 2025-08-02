#!/bin/bash

# Library Advisory System Launcher
# Easy way to start the chatbot

echo "🔍 Starting Library Advisory System..."
echo "=================================="

# Navigate to the script directory
cd "$(dirname "$0")"

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    python3 library_advisory_bot.py "$@"
elif command -v python &> /dev/null; then
    python library_advisory_bot.py "$@"
else
    echo "❌ Error: Python is not installed or not in PATH"
    echo "Please install Python 3.6+ to run this application"
    exit 1
fi
