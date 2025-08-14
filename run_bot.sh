#!/bin/bash
# Library Advisory System - Terminal Bot Launcher
echo "🤖 Starting Library Advisory System Terminal Bot..."
echo "================================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Check if required packages are installed
if ! python3 -c "import flask, requests" 2>/dev/null; then
    echo "❌ Required packages not installed. Run: pip3 install -r requirements.txt"
    exit 1
fi

echo "✓ Starting terminal chatbot..."
echo "💡 For web interface, use: ./run_gui.sh"
echo "🛑 Press Ctrl+C to exit"
echo ""

# Start the terminal bot
python3 library_advisory_bot.py
