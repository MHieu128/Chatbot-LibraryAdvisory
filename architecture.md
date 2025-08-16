# Library Advisor - System Architecture

## Overview
Library Advisor is a Python-based RAG (Retrieval-Augmented Generation) assistant that helps developers manage libraries and dependencies in React, Vue.js, and .NET projects. The system uses Azure OpenAI, LangChain, and FAISS for semantic search capabilities.

## System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web Interface                             │
│                    (Flask/FastAPI)                              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                 Main Application                                │
│                  (Python Backend)                              │
│  ┌─────────────────┬───────────────────┬─────────────────────┐  │
│  │  Query Handler  │  Project Analyzer │  Response Generator │  │
│  └─────────────────┴───────────────────┴─────────────────────┘  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                   RAG Engine                                   │
│  ┌─────────────────┬───────────────────┬─────────────────────┐  │
│  │ Embedding Model │   FAISS Vector   │   Function Calling  │  │
│  │   (Azure API)   │    Database      │     (LangChain)     │  │
│  └─────────────────┴───────────────────┴─────────────────────┘  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                External Services                               │
│  ┌─────────────────┬───────────────────┬─────────────────────┐  │
│  │  Azure OpenAI   │   File System     │   Package APIs     │  │
│  │  (GPT-4o-mini)  │   Scanner         │   (npm, nuget)     │  │
│  └─────────────────┴───────────────────┴─────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend Framework:** Flask/FastAPI  
**RAG Framework:** LangChain  
**Vector Database:** FAISS  
**AI Models:** Azure OpenAI (GPT-4o-mini + Embedding model)  
**File Processing:** Python standard libraries + custom parsers  
**Web Interface:** HTML/CSS/JavaScript with Bootstrap  

## Core Modules

### 1. Project Scanner Module (`project_scanner.py`)
```python
class ProjectScanner:
    - scan_project_directory()
    - extract_dependencies()
    - parse_config_files()
    - chunk_code_content()
```

### 2. Embedding Manager (`embedding_manager.py`)
```python
class EmbeddingManager:
    - create_embeddings()
    - store_in_faiss()
    - search_similar_content()
    - update_vector_db()
```

### 3. Function Call Handler (`function_handler.py`)
```python
class FunctionHandler:
    - find_library_references()
    - check_compatibility()
    - list_incompatible_libraries()
    - suggest_library_upgrades()
```

### 4. RAG Engine (`rag_engine.py`)
```python
class RAGEngine:
    - process_query()
    - retrieve_context()
    - generate_response()
    - combine_sources()
```

### 5. Web Interface (`app.py`)
```python
class WebApp:
    - handle_file_upload()
    - process_user_query()
    - display_results()
    - project_management()
```

## Data Flow

### 1. Project Initialization
```
User uploads project → Scanner reads files → Content chunking → 
Embedding generation → FAISS storage → Project profile creation
```

### 2. Query Processing
```
User query → Query embedding → FAISS search → Function calls (if needed) → 
Context combination → GPT response generation → Result presentation
```

### 3. Library Management
```
Management request → Project analysis → Compatibility checking → 
Risk assessment → Recommendation generation → Action guidance
```

## API Design

### REST Endpoints
- `POST /api/projects/upload` - Upload and analyze project
- `POST /api/query` - Process user questions
- `GET /api/projects/{id}/profile` - Get project analysis
- `POST /api/libraries/check` - Check library compatibility
- `POST /api/libraries/suggest` - Get library suggestions
- `GET /api/projects/{id}/dependencies` - List dependencies

## Security Considerations

- **API Key Management:** Environment variables for Azure OpenAI keys
- **File Upload Security:** Validate file types and sizes
- **Input Sanitization:** Clean user queries and file content
- **Rate Limiting:** Prevent API abuse
- **Data Privacy:** Local FAISS storage, no data sent to third parties

## Performance Optimizations

- **Caching:** Cache embeddings and frequent queries
- **Batch Processing:** Process multiple files simultaneously
- **Incremental Updates:** Update only changed files
- **Connection Pooling:** Reuse Azure OpenAI connections
- **Lazy Loading:** Load project data on demand

## Deployment Architecture

### Local Development
```
Python Virtual Environment → Local FAISS DB → Azure OpenAI APIs
```

### Production Deployment
```
Docker Container → Persistent Volume (FAISS) → Load Balancer → Azure Services
```

## Configuration

### Environment Variables
```
AZURE_OPENAI_API_KEY_GPT=your_gpt_key
AZURE_OPENAI_API_KEY_EMBEDDING=your_embedding_key
AZURE_OPENAI_ENDPOINT=your_endpoint
FAISS_DB_PATH=./data/faiss_db
MAX_FILE_SIZE=50MB
```

## Error Handling

- **API Failures:** Retry logic with exponential backoff
- **File Processing Errors:** Graceful degradation
- **Vector Search Issues:** Fallback to text-based search
- **Memory Management:** Chunk large projects appropriately

## Monitoring and Logging

- **Query Tracking:** Log user queries and response times
- **Error Logging:** Capture and analyze failures
- **Usage Metrics:** Track API calls and costs
- **Performance Monitoring:** Monitor embedding and search times
