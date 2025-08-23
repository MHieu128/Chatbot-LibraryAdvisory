# Library Advisor

A Python-based RAG (Retrieval-Augmented Generation) assistant that helps developers manage libraries and dependencies in React, Vue.js, and .NET projects.

## Features

- **Project Analysis**: Automatically scans and analyzes project directories
- **Semantic Search**: Uses FAISS vector database for intelligent code search
- **Library Management**: Check compatibility, suggest upgrades, and manage dependencies
- **Multi-Framework Support**: React, Vue.js, and .NET projects
- **AI-Powered Recommendations**: Powered by Azure OpenAI GPT-4o-mini

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your Azure OpenAI credentials
```

### 3. Run the Application

```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

## API Endpoints

- `POST /api/projects/upload` - Upload and analyze project
- `POST /api/query` - Process user questions
- `GET /api/projects/{id}/profile` - Get project analysis
- `POST /api/libraries/check` - Check library compatibility
- `POST /api/libraries/suggest` - Get library suggestions

## Project Structure

```
library-advisor/
├── app.py                 # Main Flask application
├── config/               # Configuration management
├── core/                 # Core RAG functionality
├── utils/                # Utility functions
├── templates/            # HTML templates
├── static/              # CSS, JS, images
├── data/                # FAISS storage and uploads
└── tests/               # Unit tests
```

## License

MIT License
