import os
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from flask import Flask, request, jsonify, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from config.settings import get_config
from core.project_scanner import ProjectScanner
from core.embedding_manager import EmbeddingManager, EmbeddingDocument
from core.rag_engine import RAGEngine

# Initialize Flask app
app = Flask(__name__)

# Load configuration
config = get_config()
app.config.from_object(config)

# Validate configuration
try:
    config.validate_config()
except ValueError as e:
    print(f"Configuration error: {e}")
    exit(1)

# Initialize core components
embedding_manager = EmbeddingManager(
    api_key=config.AZURE_OPENAI_API_KEY_EMBEDDING,
    endpoint=config.AZURE_OPENAI_ENDPOINT,
    deployment=config.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    faiss_db_path=config.FAISS_DB_PATH,
    embedding_dimension=config.EMBEDDING_DIMENSION
)

rag_engine = RAGEngine(
    gpt_api_key=config.AZURE_OPENAI_API_KEY_GPT,
    gpt_endpoint=config.AZURE_OPENAI_ENDPOINT,
    gpt_deployment=config.AZURE_OPENAI_GPT_DEPLOYMENT,
    embedding_manager=embedding_manager
)

project_scanner = ProjectScanner(config.SUPPORTED_EXTENSIONS)

# In-memory storage for projects (in production, use a database)
projects_store: Dict[str, any] = {}

def allowed_file(filename: str) -> bool:
    """Check if file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in [ext.lstrip('.') for ext in config.SUPPORTED_EXTENSIONS]

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', 
                         projects=list(projects_store.values()),
                         index_info=embedding_manager.get_index_info())

@app.route('/api/projects/upload', methods=['POST'])
def upload_project():
    """Upload and analyze a project"""
    try:
        if 'project' not in request.files and 'project_path' not in request.form:
            return jsonify({'error': 'No project file or path provided'}), 400
        
        project_id = str(uuid.uuid4())
        project_path = None
        
        # Handle file upload
        if 'project' in request.files:
            file = request.files['project']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            if file:
                # Save uploaded file
                filename = secure_filename(file.filename)
                project_dir = Path(config.UPLOAD_FOLDER) / project_id
                project_dir.mkdir(parents=True, exist_ok=True)
                
                file_path = project_dir / filename
                file.save(file_path)
                
                # Extract if it's a zip file
                if filename.endswith('.zip'):
                    import zipfile
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(project_dir)
                    os.remove(file_path)
                
                project_path = str(project_dir)
        
        # Handle project path
        elif 'project_path' in request.form:
            project_path = request.form['project_path']
            if not os.path.exists(project_path):
                return jsonify({'error': 'Project path does not exist'}), 400
        
        # Scan and analyze project
        print(f"Scanning project at: {project_path}")
        project_profile = project_scanner.scan_project_directory(project_path)
        
        # Create embeddings for project files
        documents = []
        for file in project_profile.files:
            if file.chunks:
                for i, chunk in enumerate(file.chunks):
                    metadata = {
                        'project_id': project_profile.project_id,
                        'file_path': file.path,
                        'file_type': file.file_type,
                        'chunk_index': i,
                        'total_chunks': len(file.chunks)
                    }
                    
                    doc = EmbeddingDocument(
                        id=f"{project_profile.project_id}_{file.path}_{i}",
                        content=chunk,
                        metadata=metadata
                    )
                    documents.append(doc)
        
        print(f"Creating embeddings for {len(documents)} document chunks...")
        
        # Create embeddings
        embedding_docs = embedding_manager.create_embeddings(
            [doc.content for doc in documents],
            [doc.metadata for doc in documents]
        )
        
        # Store in FAISS
        success = embedding_manager.update_vector_db(project_profile.project_id, embedding_docs)
        
        if not success:
            return jsonify({'error': 'Failed to store embeddings'}), 500
        
        # Store project in memory
        projects_store[project_profile.project_id] = {
            'id': project_profile.project_id,
            'name': project_profile.name,
            'framework': project_profile.framework,
            'languages': project_profile.languages,
            'total_files': project_profile.total_files,
            'total_size': project_profile.total_size,
            'dependencies': dict(list(project_profile.dependencies.items())[:20]),  # Limit for display
            'upload_time': datetime.now().isoformat(),
            'profile': project_profile
        }
        
        return jsonify({
            'success': True,
            'project_id': project_profile.project_id,
            'message': f'Project "{project_profile.name}" analyzed successfully',
            'stats': {
                'files_processed': len(project_profile.files),
                'chunks_created': len(documents),
                'embeddings_stored': len(embedding_docs),
                'framework': project_profile.framework,
                'languages': project_profile.languages
            }
        })
    
    except RequestEntityTooLarge:
        return jsonify({'error': 'File too large. Maximum size is 50MB'}), 413
    except Exception as e:
        print(f"Error uploading project: {e}")
        return jsonify({'error': f'Failed to process project: {str(e)}'}), 500

@app.route('/api/query', methods=['POST'])
def process_query():
    """Process user query"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400
        
        query = data['query']
        project_id = data.get('project_id')
        
        # Get project if specified
        project = None
        if project_id and project_id in projects_store:
            project = projects_store[project_id]['profile']
        
        # Process query with RAG engine
        response = rag_engine.process_query(query, project)
        
        # Format sources for JSON response
        sources = []
        for source in response.sources:
            sources.append({
                'file_path': source.document.metadata.get('file_path', 'unknown'),
                'content': source.document.content[:300] + '...',
                'score': source.score,
                'rank': source.rank
            })
        
        return jsonify({
            'success': True,
            'answer': response.answer,
            'sources': sources,
            'function_calls': response.function_calls,
            'confidence': response.confidence,
            'project_context': response.project_context
        })
    
    except Exception as e:
        print(f"Error processing query: {e}")
        return jsonify({'error': f'Failed to process query: {str(e)}'}), 500

@app.route('/api/projects/<project_id>/profile')
def get_project_profile(project_id):
    """Get project profile"""
    if project_id not in projects_store:
        return jsonify({'error': 'Project not found'}), 404
    
    project_data = projects_store[project_id]
    
    # Get embedding statistics
    embedding_stats = embedding_manager.get_project_statistics(project_id)
    
    return jsonify({
        'success': True,
        'project': {
            'id': project_data['id'],
            'name': project_data['name'],
            'framework': project_data['framework'],
            'languages': project_data['languages'],
            'total_files': project_data['total_files'],
            'total_size': project_data['total_size'],
            'dependencies': project_data['dependencies'],
            'upload_time': project_data['upload_time'],
            'embedding_stats': embedding_stats
        }
    })

@app.route('/api/libraries/check', methods=['POST'])
def check_library_compatibility():
    """Check library compatibility"""
    try:
        data = request.get_json()
        if not data or 'library' not in data or 'project_id' not in data:
            return jsonify({'error': 'Library name and project ID required'}), 400
        
        library = data['library']
        project_id = data['project_id']
        
        if project_id not in projects_store:
            return jsonify({'error': 'Project not found'}), 404
        
        project = projects_store[project_id]['profile']
        
        # Use function handler to check compatibility
        result = rag_engine.function_handler.check_compatibility(project.dependencies, library)
        
        return jsonify({
            'success': True,
            'library': result.library,
            'is_compatible': result.is_compatible,
            'conflicts': result.conflicts,
            'warnings': result.warnings,
            'recommendations': result.recommendations
        })
    
    except Exception as e:
        print(f"Error checking compatibility: {e}")
        return jsonify({'error': f'Failed to check compatibility: {str(e)}'}), 500

@app.route('/api/libraries/suggest', methods=['POST'])
def suggest_libraries():
    """Get library suggestions"""
    try:
        data = request.get_json()
        if not data or 'project_id' not in data:
            return jsonify({'error': 'Project ID required'}), 400
        
        project_id = data['project_id']
        category = data.get('category', 'general')
        
        if project_id not in projects_store:
            return jsonify({'error': 'Project not found'}), 404
        
        project = projects_store[project_id]['profile']
        
        # Generate suggestions using RAG
        query = f"Suggest useful {category} libraries for this {project.framework} project"
        response = rag_engine.process_query(query, project)
        
        return jsonify({
            'success': True,
            'suggestions': response.answer,
            'confidence': response.confidence
        })
    
    except Exception as e:
        print(f"Error generating suggestions: {e}")
        return jsonify({'error': f'Failed to generate suggestions: {str(e)}'}), 500

@app.route('/api/projects/<project_id>/dependencies')
def get_project_dependencies(project_id):
    """Get project dependencies"""
    if project_id not in projects_store:
        return jsonify({'error': 'Project not found'}), 404
    
    project = projects_store[project_id]['profile']
    
    return jsonify({
        'success': True,
        'dependencies': project.dependencies,
        'total_count': len(project.dependencies),
        'framework': project.framework
    })

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'index_info': embedding_manager.get_index_info(),
        'projects_loaded': len(projects_store)
    })

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 50MB'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("Starting Library Advisor...")
    print(f"FAISS DB Path: {config.FAISS_DB_PATH}")
    print(f"Upload Folder: {config.UPLOAD_FOLDER}")
    print(f"Supported Extensions: {config.SUPPORTED_EXTENSIONS}")
    
    # Create necessary directories
    Path(config.UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
    Path(config.FAISS_DB_PATH).mkdir(parents=True, exist_ok=True)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=config.FLASK_DEBUG
    )
