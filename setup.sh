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
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✓ Created .env file from template"
    else
        echo "⚠️ .env.example not found, creating basic .env file..."
        cat > .env << 'EOF'
# Azure OpenAI Configuration (Optional - for AI features)
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=GPT-4o-mini

# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-here-change-in-production

# Application Settings
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000
CACHE_MAX_SIZE=100
LOG_LEVEL=INFO
EOF
        echo "✓ Created basic .env file"
    fi
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
