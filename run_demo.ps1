#!/usr/bin/env pwsh
# PowerShell script to run the function calling demo
# For Windows users

Write-Host "🔍 Library Advisory System - Function Calling Demo" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to the script directory
Set-Location (Split-Path $MyInvocation.MyCommand.Path)

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.7+ to run this application" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if required dependencies are installed
Write-Host "🔄 Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import requests, openai, dotenv" 2>$null
    Write-Host "✅ Dependencies verified" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Some dependencies may be missing. Installing requirements..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
}

Write-Host ""
Write-Host "🚀 Starting Function Calling Demo..." -ForegroundColor Green
Write-Host ""

# Run the demo
python examples/function_calling_demo.py

Write-Host ""
Write-Host "📝 Demo completed! Press Enter to exit..." -ForegroundColor Cyan
Read-Host
