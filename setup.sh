#!/bin/bash

# Library Advisory System Setup Script
echo "🔍 Library Advisory System Setup"
echo "================================="

# Check Python version
python_version=$(python3 --version 2>/dev/null | cut -d' ' -f2)
if [ -z "$python_version" ]; then
    echo "❌ Python 3 is not installed. Please install Python 3.7+ to continue."
    exit 1
fi

echo "✓ Python version: $python_version"

# Install dependencies
echo "📦 Installing dependencies..."
if pip3 install -r requirements.txt; then
    echo "✓ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Setup environment file
if [ ! -f ".env" ]; then
    echo "⚙️ Setting up environment configuration..."
    cp .env.example .env
    echo "✓ Created .env file from template"
    echo ""
    echo "📝 Please edit .env file with your Azure OpenAI credentials:"
    echo "   - AZURE_OPENAI_ENDPOINT"
    echo "   - AZURE_OPENAI_API_KEY"
    echo "   - AZURE_OPENAI_DEPLOYMENT_NAME"
    echo ""
    echo "You can run the bot without AI features if you don't configure Azure OpenAI."
else
    echo "✓ Environment file already exists"
fi

# Make scripts executable
chmod +x library_advisory_bot.py
chmod +x run_bot.sh

echo ""
echo "🚀 Setup complete! To start the bot:"
echo "   ./run_bot.sh"
echo "   or"
echo "   python3 library_advisory_bot.py"
echo ""
echo "📖 For more information, see README.md"
