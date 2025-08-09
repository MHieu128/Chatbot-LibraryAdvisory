# 🤖 Library Advisory System 2.0

## Enhanced with ChromaDB Semantic Search & HuggingFace Text-to-Speech

A powerful AI-powered library recommendation system with advanced semantic search capabilities and real-time audio responses.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![ChromaDB](https://img.shields.io/badge/ChromaDB-0.4+-orange.svg)
![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-yellow.svg)
![Azure OpenAI](https://img.shields.io/badge/Azure-OpenAI-purple.svg)

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env with your Azure OpenAI credentials

# 3. Initialize the system
python3 migrate_to_chromadb.py

# 4. Start the application
python3 app.py
```

Visit http://localhost:5001 to access the web interface!

## ✨ Key Features

### 🔍 **Semantic Search with ChromaDB**
- Vector database with sentence-transformer embeddings
- Context-aware library and framework matching
- Intelligent FAQ retrieval based on similarity
- User query storage for personalized recommendations

### 🎤 **Text-to-Speech Integration**
- High-quality audio generation with Microsoft SpeechT5
- Real-time response playback in web interface
- Smart audio caching for performance optimization
- HTML5 audio controls with play/pause functionality

### 🤖 **Enhanced AI Capabilities**
- Azure OpenAI GPT-4 integration with function calling
- Semantic search functions for enhanced responses
- Multi-modal output (text + audio)
- Context-aware library analysis and recommendations

### 🌐 **Modern Web Interface**
- Responsive Bootstrap 5 design
- Interactive chat with audio controls
- Library browsing sidebar with semantic search
- Real-time TTS status and controls

## 📋 What's New in 2.0

| Feature | Status | Description |
|---------|--------|-------------|
| **ChromaDB Integration** | ✅ Complete | Vector database with semantic search |
| **TTS Audio Generation** | ✅ Complete | HuggingFace SpeechT5 models |
| **Enhanced Bot Logic** | ✅ Complete | Semantic search + AI integration |
| **Web Audio Controls** | ✅ Complete | Interactive TTS in browser |
| **API Endpoints** | ✅ Complete | RESTful APIs for TTS & search |
| **Data Migration** | ✅ Complete | JSON to ChromaDB migration |
| **Production Ready** | ✅ Complete | Comprehensive deployment guide |

## 🏗️ Architecture

```
┌─────────────────┬─────────────────┬─────────────────┐
│   Frontend      │    Backend      │    AI/ML        │
├─────────────────┼─────────────────┼─────────────────┤
│ Bootstrap 5     │ Flask 2.3+      │ Azure OpenAI    │
│ HTML5 Audio     │ ChromaDB 0.4+   │ GPT-4 Turbo     │
│ JavaScript ES6  │ REST APIs       │ Function Calling│
│ CSS3 Animations │ Session Mgmt    │ Embeddings      │
├─────────────────┼─────────────────┼─────────────────┤
│                 │ TTS Pipeline    │ HuggingFace     │
│                 │ Audio Caching   │ SpeechT5        │
│                 │ Vector Search   │ Transformers    │
│                 │ Data Storage    │ Sentence-BERT   │
└─────────────────┴─────────────────┴─────────────────┘
```

## 📁 Project Structure

```
Chatbot-LibraryAdvisory/
├── 📱 Web Application
│   ├── app.py                          # Main Flask application
│   ├── templates/                      # HTML templates
│   │   ├── base.html                   # Base template with TTS styles
│   │   ├── index.html                  # Chat interface with audio
│   │   └── ...                         # Other pages
│   └── static/                         # CSS, JS, assets
│
├── 🤖 Enhanced Bot Logic
│   ├── library_advisory_bot_chromadb.py # Enhanced bot with ChromaDB
│   ├── library_advisory_bot.py          # Original bot (fallback)
│   └── migrate_to_chromadb.py           # Data migration script
│
├── 🔍 ChromaDB Integration
│   ├── chromadb_utils.py               # Vector database utilities
│   ├── chromadb_data/                  # Persistent storage
│   └── chromadb_implementation_guide.md # Technical documentation
│
├── 🎤 TTS Integration
│   ├── tts_utils.py                    # Text-to-speech utilities
│   ├── tts_cache/                      # Audio cache directory
│   └── tts_implementation_guide.md     # TTS documentation
│
├── 📚 Documentation
│   ├── README.md                       # This file
│   ├── DEPLOYMENT_GUIDE.md             # Complete deployment guide
│   ├── implementation_roadmap.md       # Development roadmap
│   └── .env.example                    # Environment configuration
│
└── 🧪 Testing & Utilities
    ├── test_implementations.py         # System tests
    ├── requirements.txt                # Python dependencies
    └── logs/                           # Application logs
```

## 🎯 Use Cases

### For Developers
- **Framework Selection**: Get AI-powered recommendations for your project
- **Technology Comparison**: Semantic comparison of libraries and frameworks  
- **Learning Path**: Discover related technologies and concepts
- **Audio Learning**: Listen to explanations while coding

### For Teams
- **Technical Decisions**: Data-driven technology choices
- **Knowledge Sharing**: Audio explanations for team meetings
- **Documentation**: Generate spoken documentation
- **Training**: Interactive learning with audio feedback

### For Educators
- **Teaching Tool**: Audio explanations of programming concepts
- **Student Interaction**: Engaging Q&A sessions
- **Accessibility**: Audio content for different learning styles
- **Demonstration**: Live coding with spoken explanations

## 🔧 Configuration Options

### ChromaDB Settings
```env
ENABLE_CHROMADB=true                    # Enable semantic search
CHROMADB_PERSIST_DIR=./chromadb_data   # Database storage location
```

### TTS Configuration
```env
ENABLE_TTS=true                        # Enable text-to-speech
TTS_CACHE_DIR=./tts_cache             # Audio cache location
TTS_MAX_CACHE_SIZE_MB=500             # Cache size limit
TTS_MAX_TEXT_LENGTH=1000              # Maximum text length
TTS_DEVICE=auto                       # CPU/GPU selection
```

### Azure OpenAI
```env
AZURE_OPENAI_API_KEY=your_key         # Your API key
AZURE_OPENAI_ENDPOINT=your_endpoint   # Your endpoint URL
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4    # Model deployment
```

## 📊 Performance Metrics

| Component | Metric | Performance |
|-----------|---------|-------------|
| **ChromaDB Search** | Query Time | <100ms typical |
| **TTS Generation** | Audio Generation | 2-5s first time, <1s cached |
| **Web Interface** | Page Load | <2s |
| **AI Response** | End-to-end | 3-8s including audio |
| **Memory Usage** | Runtime | ~1.5GB with models loaded |
| **Storage** | Model Cache | ~1GB for TTS models |

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9 or higher
- 4GB+ RAM (for TTS models)
- Azure OpenAI access (optional but recommended)
- Internet connection for model downloads

### 2. Installation
```bash
# Clone the repository
git clone <repository-url>
cd Chatbot-LibraryAdvisory

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration (required for full functionality)
nano .env
```

### 4. Initialize Data
```bash
# Migrate existing data to ChromaDB
python migrate_to_chromadb.py

# Test the enhanced bot (optional)
python library_advisory_bot_chromadb.py
```

### 5. Launch Application
```bash
# Start the web server
python app.py

# Access the application
open http://localhost:5001
```

## 🧪 Testing

### Quick Tests
```bash
# Test all components
python test_implementations.py

# Test TTS generation
curl -X POST http://localhost:5001/api/tts/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test"}'

# Test semantic search
curl -X POST http://localhost:5001/api/chromadb/search \
  -H "Content-Type: application/json" \
  -d '{"query": "react framework", "collection": "libraries"}'
```

### Interactive Testing
1. Open web interface at http://localhost:5001
2. Toggle TTS on/off using the audio button
3. Try queries like:
   - "analyze React"
   - "compare Vue vs Angular"
   - "recommend Python frameworks"
4. Listen to generated audio responses

## 📈 Roadmap

### Phase 1: Core Enhancement ✅
- [x] ChromaDB integration with semantic search
- [x] HuggingFace TTS implementation
- [x] Enhanced web interface with audio controls
- [x] Data migration and testing

### Phase 2: Advanced Features 🔄
- [ ] Multi-language TTS support
- [ ] Voice selection and customization
- [ ] Advanced analytics and user tracking
- [ ] Mobile app development

### Phase 3: Enterprise Features 📋
- [ ] API rate limiting and authentication
- [ ] Microservices architecture
- [ ] Kubernetes deployment
- [ ] Multi-tenant support

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit changes** (`git commit -m 'Add amazing feature'`)
4. **Push to branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Code formatting
black .
flake8 .
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Complete deployment and usage guide |
| [chromadb_implementation_guide.md](chromadb_implementation_guide.md) | ChromaDB technical details |
| [tts_implementation_guide.md](tts_implementation_guide.md) | TTS integration guide |
| [implementation_roadmap.md](implementation_roadmap.md) | Development roadmap |

## 🆘 Support

### Common Issues
- **Models not downloading**: Check internet connection and disk space
- **Audio not playing**: Verify browser permissions and TTS status
- **ChromaDB errors**: Check data directory permissions
- **Memory issues**: Reduce TTS cache size or use CPU mode

### Getting Help
1. Check the [Deployment Guide](DEPLOYMENT_GUIDE.md)
2. Review logs in the `logs/` directory
3. Test individual components with `test_implementations.py`
4. Open an issue with detailed error information

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **ChromaDB** for vector database capabilities
- **HuggingFace** for state-of-the-art TTS models
- **Azure OpenAI** for advanced AI integration
- **Flask** for the robust web framework
- **Bootstrap** for responsive UI components

---

## 🎉 Ready to Go!

Your Library Advisory System 2.0 is now equipped with:
- 🔍 **Semantic Search** powered by ChromaDB
- 🎤 **Text-to-Speech** with HuggingFace models
- 🤖 **Enhanced AI** with Azure OpenAI integration
- 🌐 **Modern Web Interface** with audio controls

Start exploring libraries and frameworks with the power of AI and audio! 🚀

```bash
python app.py
# Visit http://localhost:5001 and enjoy!
