#!/bin/bash
# Library Advisory System - Web GUI Launcher
echo "🌐 Starting Library Advisory System Web Interface..."
echo "=================================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "❌ Flask not installed. Run: pip3 install -r requirements.txt"
    exit 1
fi

echo "✓ Starting Flask web server..."
echo "📱 Open your browser and go to: http://localhost:5001"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Start the Flask application
python3 app.py
