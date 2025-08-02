# Library Advisory System - Project Structure

```
LibraryAdvisory/
├── library_advisory_bot.py    # Main chatbot application with Azure OpenAI and function calling
├── app.py                     # Flask web application with function calling support
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── .env                      # Environment configuration (configure with your credentials)
├── .gitignore               # Git ignore file
├── README.md                # Main documentation with function calling features
├── EXAMPLES.md              # Usage examples and workflows
├── setup.sh                 # Automated setup script
├── run_bot.sh              # Bot launcher script (Linux/Mac)
├── run_demo.ps1            # Function calling demo launcher (Windows PowerShell)
├── test_installation.py    # Installation verification script
├── examples/               # Example scripts and demos
│   ├── function_calling_demo.py  # Function calling demonstration
│   └── .gitkeep            # Directory placeholder
├── reports/                 # Generated analysis reports
│   ├── .gitkeep            # Directory description and placeholder
│   └── sample_*.md         # Example report format
├── static/                 # Web application assets
│   └── css/
│       └── style.css       # Web interface styling
├── templates/              # Flask HTML templates
│   ├── base.html           # Base template
│   ├── index.html          # Chat interface
│   ├── compare.html        # Library comparison
│   ├── recommendations.html # Recommendations page
│   ├── about.html          # About page
│   └── help.html           # Help documentation
└── library_database.json   # Auto-generated library database (created on first run)
```

## Quick Start

1. **Setup**:
   ```bash
   ./setup.sh
   ```

2. **Configure Azure OpenAI** (edit `.env`):
   ```env
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_API_KEY=your-api-key
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
   ```

3. **Run**:
   ```bash
   ./run_bot.sh
   ```

## Key Features Implemented

✅ **Azure OpenAI Integration**
- Environment-based configuration
- Intelligent analysis and recommendations
- Context-aware conversations
- Fallback to basic mode if AI unavailable

✅ **Comprehensive Library Analysis**
- Technical evaluation framework
- Cost and licensing analysis
- Risk assessment
- Security considerations

✅ **AI-Enhanced Features**
- Natural language query processing
- Intelligent comparisons
- Context-aware follow-up questions
- Real-time insights

✅ **User Experience**
- Color-coded terminal output
- Command-based interface
- Help system and examples
- Error handling and graceful degradation
- Markdown report generation and export

✅ **Development Features**
- Environment variable management
- Logging and debug support
- Extensible library database
- Test and verification scripts
- Conversation history and session management

## System Architecture

```
User Input → Command Parser → Basic Analysis → AI Enhancement → Formatted Output
                ↓
        Library Database ← → Azure OpenAI API ← → Conversation Context
```

The system follows the comprehensive system prompt requirements with:
- Technical analysis across all specified dimensions
- Economic and legal assessment
- Risk and security evaluation
- Operational considerations
- Comparative analysis with feature matrices
- Structured response format with clear sections

## Next Steps

1. Configure your Azure OpenAI credentials in `.env`
2. Run the bot and try different types of queries
3. Extend the library database with additional libraries
4. Customize analysis templates for specific domains
5. Add integration with package managers (npm, pip, etc.)

The chatbot is now ready to provide comprehensive library advisory services with AI-powered insights!
