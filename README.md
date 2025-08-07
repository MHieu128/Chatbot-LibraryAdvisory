# Library Advisory System

A comprehensive terminal chatbot for software library evaluation and recommendation, powered by Azure OpenAI.

## Features

- **AI-Enhanced Analysis**: Powered by Azure OpenAI for intelligent insights and recommendations
- **Real-time Package Registry Integration**: Live data from NuGet and npm registries using function calling
- **Comprehensive Library Analysis**: Technical evaluation, cost analysis, risk assessment
- **Library Comparison**: Side-by-side comparison of multiple libraries with AI insights
- **Intelligent Recommendations**: Context-aware suggestions based on requirements
- **Risk & Security Assessment**: Security evaluation and vulnerability analysis
- **Cost & Licensing Analysis**: Total cost of ownership and licensing compliance
- **Migration Guidance**: Path planning for library transitions
- **Conversation Context**: Maintains conversation history for better AI responses
- **Function Calling**: Real-time package information from official registries

## Installation

1. Clone or download the project
2. Ensure Python 3.7+ is installed
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up Azure OpenAI credentials (see Configuration section)

## Configuration

### Azure OpenAI Setup

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Fill in your Azure OpenAI credentials in `.env`:
   ```env
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_API_KEY=your-api-key-here
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
   OPENAI_TEMPERATURE=0.7
   OPENAI_MAX_TOKENS=2000
   DEBUG=false
   ```

3. To get these values:
   - **Endpoint**: From your Azure OpenAI resource in Azure Portal
   - **API Key**: From Keys and Endpoint section in Azure Portal
   - **Deployment Name**: The name you gave your model deployment
   - **Model**: The model you deployed (e.g., gpt-4, gpt-35-turbo)

### Running Without AI

The system can run in basic mode without Azure OpenAI if credentials are not configured. You'll still get structured analysis but without AI-enhanced insights.

## Usage

### Basic Commands

```bash
# Run the chatbot
python library_advisory_bot.py

# Run with debug mode
python library_advisory_bot.py --debug

# Show version
python library_advisory_bot.py --version
```

### Interactive Commands

Once the chatbot is running, you can use these commands:

- `help` - Show detailed help information
- `list` - Display available libraries in database
- `analyze <library>` - Perform detailed analysis of a specific library
- `compare <lib1> vs <lib2>` - Compare two libraries side by side
- `recommend <category>` - Get recommendations for a specific category
- `ai <your question>` - Ask AI for intelligent analysis (requires Azure OpenAI)
- `save` - Save current conversation to markdown file
- `exit` or `quit` - Exit the chatbot (offers to save conversation)

### Example Queries

```
🤖 Library Advisor: analyze React
🤖 Library Advisor: compare React vs Vue.js
🤖 Library Advisor: recommend JavaScript frameworks
🤖 Library Advisor: what is Django?
🤖 Library Advisor: suggest Python web frameworks
🤖 Library Advisor: tell me about Express.js
🤖 Library Advisor: ai What are the security considerations for React applications?
🤖 Library Advisor: ai Compare the learning curves of Django vs FastAPI
🤖 Library Advisor: ai Check the latest version of Newtonsoft.Json
🤖 Library Advisor: ai How popular is the Express package on npm?
🤖 Library Advisor: save
```

## Function Calling Features

The system now includes advanced function calling capabilities that provide real-time package information:

### Supported Registries

- **NuGet (.NET packages)**: Real-time version information, download statistics, licensing, and metadata
- **npm (JavaScript/Node.js packages)**: Current versions, weekly downloads, repository links, and package details

### Automatic Registry Integration

When you ask about packages, the AI automatically:
1. **Checks Package Registries**: Fetches current version and download statistics
2. **Validates Existence**: Confirms packages exist and are actively maintained
3. **Extracts Metadata**: Gets licensing, authorship, and repository information
4. **Includes in Analysis**: Incorporates real-time data into recommendations

### Function Calling Demo

Run the included demonstration script:
```bash
python examples/function_calling_demo.py
```

This will show:
- NuGet package checking (e.g., Newtonsoft.Json)
- npm package checking (e.g., Express)
- Error handling for non-existent packages
- AI-enhanced analysis with live registry data

## Report Generation

The system automatically generates comprehensive markdown reports of your analysis sessions:

- **Automatic Timestamping**: Each report is saved with a timestamp for easy organization
- **Complete Analysis**: Includes all queries, responses, and AI insights
- **Clean Formatting**: Color codes are removed and content is properly formatted for markdown
- **Session Summaries**: Provides statistics about your analysis session
- **Export on Exit**: Option to save conversation when exiting the application

Reports are saved in the `reports/` directory with filenames like `library_analysis_20250726_143022.md`.

## AI-Enhanced Features

When Azure OpenAI is configured, the system provides:

- **Intelligent Analysis**: AI-powered insights beyond basic template responses
- **Context-Aware Responses**: Maintains conversation history for better recommendations
- **Natural Language Processing**: Handle complex, conversational queries
- **Real-time Insights**: Current information and trends in the library ecosystem
- **Custom Recommendations**: Tailored advice based on specific requirements
- **Report Generation**: Save complete analysis sessions to markdown files

## Analysis Framework

The system evaluates libraries across multiple dimensions:

### Technical Analysis
- **Advantages**: Key strengths, performance benefits, community support
- **Disadvantages**: Limitations, compatibility issues, learning curve
- **Complexity**: Implementation difficulty and integration requirements

### Economic & Legal Assessment
- **Cost Analysis**: Total cost of ownership, licensing fees, implementation costs
- **License Terms**: Detailed licensing analysis and compliance requirements
- **Pricing Structure**: Enterprise vs. open-source options

### Risk & Security Evaluation
- **Risk Assessment**: Technical risks, vendor lock-in, discontinuation risk
- **Security Analysis**: Vulnerability history, update frequency, security practices
- **Patching & Updates**: Maintenance lifecycle and backward compatibility

### Operational Considerations
- **Flexibility**: Customization options and extensibility
- **Integration**: Compatibility with existing systems and ecosystem

## Library Database

The system includes a built-in database of popular libraries including:

- **Frontend Frameworks**: React, Vue.js, Angular, Svelte
- **Web Frameworks**: Django, Flask, Express.js, FastAPI
- **And more categories as the database expands**

The database is automatically saved to `library_database.json` and can be extended.

## System Prompt Integration

The chatbot implements the comprehensive system prompt requirements:

### Core Capabilities
- Technical analysis across all dimensions
- Economic and legal assessment
- Risk and security evaluation
- Operational considerations
- Comparative analysis with feature matrices

### Response Format
- Structured markdown output with clear sections
- Consistent formatting with emojis and color coding
- Comprehensive comparison tables
- Actionable recommendations

### Interaction Style
- Objective analysis without bias
- Data-driven recommendations
- Context-aware advice
- Practical, actionable insights

## File Structure

```
LibraryAdvisory/
├── library_advisory_bot.py    # Main chatbot application
├── library_database.json      # Auto-generated library database
├── requirements.txt           # Python dependencies (minimal)
└── README.md                  # This file
```

## Extending the System

### Adding New Libraries

The system automatically saves and loads a JSON database. You can extend it by:

1. Adding entries to the `library_database.json` file
2. Following the existing schema:

```json
{
  "library_key": {
    "name": "Library Name",
    "category": "Category",
    "language": "Programming Language",
    "description": "Brief description",
    "license": "License Type",
    "popularity": "High/Medium/Low",
    "alternatives": ["Alt1", "Alt2", "Alt3"]
  }
}
```

### Customizing Analysis

Modify the analysis methods in the `LibraryAdvisoryBot` class:

- `_get_advantages()` - Customize advantage analysis
- `_get_disadvantages()` - Customize disadvantage analysis
- `_get_cost_analysis()` - Modify cost evaluation logic
- `_get_risk_assessment()` - Adjust risk analysis criteria

## Advanced Features

### Command Line Arguments

```bash
python library_advisory_bot.py --help
python library_advisory_bot.py --version
python library_advisory_bot.py --debug
```

### Conversation History

The system maintains conversation history during the session for context-aware responses.

### Color-Coded Output

- 🔍 **Blue**: System messages and headers
- ✅ **Green**: Positive information and advantages
- ❌ **Red**: Warnings, disadvantages, and risks
- ⚠️ **Yellow**: Important notes and cautions
- 💡 **Cyan**: Helpful tips and recommendations

## Best Practices

1. **Start with Analysis**: Use `analyze <library>` to understand individual libraries
2. **Compare Alternatives**: Use `compare` to evaluate options side by side
3. **Consider Context**: Provide specific requirements for better recommendations
4. **Verify Information**: Always verify current information and test in your environment
5. **Update Database**: Keep the library database current with latest information

## Limitations

- Analysis based on general knowledge and built-in database
- Real-time information requires external API integration (not included)
- Recommendations should be verified against current documentation
- Database needs manual updates for latest library information

## Future Enhancements

- Integration with GitHub API for real-time data
- NPM/PyPI/Maven repository integration
- Automated vulnerability scanning
- Performance benchmarking integration
- Machine learning-based recommendations
- Web interface version
- Plugin system for custom analyzers

## Contributing

To contribute to the library database or improve analysis algorithms:

1. Fork the project
2. Add new library entries to the database
3. Enhance analysis methods
4. Submit pull requests with improvements

## License

MIT License - Feel free to use and modify for your projects.

## Support

For issues or questions:
1. Check the built-in help system: `help`
2. Review this documentation
3. Submit issues or feature requests

---

**Happy Library Hunting! 🚀**
