#!/usr/bin/env python3
"""
Startup script for Library Advisor
This script starts the Flask application with proper configuration
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Check if the environment is properly set up"""
    # Check if .env file exists
    if not Path('.env').exists():
        print("❌ .env file not found!")
        print("Please copy .env.example to .env and configure your Azure OpenAI credentials")
        return False
    
    # Check if required directories exist
    required_dirs = ['data', 'data/uploads', 'data/faiss_db']
    for directory in required_dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    return True

def main():
    """Main startup function"""
    print("🚀 Starting Library Advisor...")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Import and run the Flask app
    try:
        from app import app
        print("✅ Environment configured successfully")
        print("📡 Starting Flask server...")
        print("🌐 Open your browser and go to: http://localhost:5000")
        print("Press Ctrl+C to stop the server")
        
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed correctly")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
