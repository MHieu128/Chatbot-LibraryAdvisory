#!/usr/bin/env python3
"""
Library Advisory System Web Application
A Flask-based web interface with ChromaDB and TTS integration
"""

from flask import Flask, render_template, request, jsonify, session, send_file
import os
import json
import uuid
import tempfile
import logging
from datetime import datetime
import re
from typing import Optional, Dict, Any
# Try to import the enhanced bot first, fall back to regular bot
try:
    from library_advisory_bot_chromadb import EnhancedLibraryAdvisoryBot as LibraryAdvisoryBot, Colors
    ENHANCED_BOT_AVAILABLE = True
except ImportError:
    try:
        from library_advisory_bot import LibraryAdvisoryBot, Colors
        ENHANCED_BOT_AVAILABLE = False
    except ImportError:
        # Fallback for minimal functionality
        LibraryAdvisoryBot = None
        Colors = None
        ENHANCED_BOT_AVAILABLE = False

# Import our new utilities
try:
    from chromadb_utils import get_chromadb_manager, initialize_chromadb
    from tts_utils import get_tts_manager, initialize_tts, TTSConfig, AudioResult
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Enhanced features not available: {e}")
    ENHANCED_FEATURES_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Configuration from environment variables
app.config.update({
    'CHROMADB_ENABLED': os.environ.get('ENABLE_CHROMADB', 'true').lower() == 'true',
    'TTS_ENABLED': os.environ.get('ENABLE_TTS', 'true').lower() == 'true',
    'AUDIO_AUTOPLAY': os.environ.get('DEFAULT_AUDIO_AUTOPLAY', 'false').lower() == 'true',
    'MAX_CONCURRENT_TTS': int(os.environ.get('MAX_CONCURRENT_TTS_REQUESTS', '3')),
})

# Global instances
bot = None
chromadb_manager = None
tts_manager = None
temp_audio_files = {}  # Store temporary audio file references

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.environ.get('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_bot():
    """Initialize the bot instance"""
    global bot
    if bot is None:
        if LibraryAdvisoryBot is None:
            raise RuntimeError("Bot class not available")
        
        # Initialize based on available bot type
        if ENHANCED_BOT_AVAILABLE and chromadb_ready and chromadb_manager:
            # Enhanced bot expects chromadb_manager parameter
            try:
                bot = LibraryAdvisoryBot(chromadb_manager=chromadb_manager)
            except TypeError:
                # Fallback to regular bot if enhanced bot not available
                bot = LibraryAdvisoryBot()
        else:
            # Regular bot initialization
            bot = LibraryAdvisoryBot()
    return bot

def init_enhanced_features():
    """Initialize ChromaDB and TTS if available"""
    global chromadb_manager, tts_manager
    
    if not ENHANCED_FEATURES_AVAILABLE:
        logger.warning("Enhanced features (ChromaDB/TTS) not available")
        return False, False
    
    chromadb_success = False
    tts_success = False
    
    # Initialize ChromaDB
    if app.config['CHROMADB_ENABLED']:
        try:
            chromadb_manager = get_chromadb_manager()
            chromadb_success = initialize_chromadb()
            if chromadb_success:
                logger.info("ChromaDB initialized successfully")
            else:
                logger.error("Failed to initialize ChromaDB")
        except Exception as e:
            logger.error(f"ChromaDB initialization error: {e}")
    
    # Initialize TTS
    if app.config['TTS_ENABLED']:
        try:
            tts_config = TTSConfig(
                cache_dir=os.environ.get('TTS_CACHE_DIR', './tts_cache'),
                max_cache_size_mb=int(os.environ.get('TTS_MAX_CACHE_SIZE_MB', '500')),
                max_text_length=int(os.environ.get('TTS_MAX_TEXT_LENGTH', '20000')),  # Tăng từ 1000 lên 3000
                device=os.environ.get('TTS_DEVICE', 'auto')
            )
            tts_manager = get_tts_manager(tts_config)
            tts_success = initialize_tts()
            if tts_success:
                logger.info("TTS initialized successfully")
            else:
                logger.error("Failed to initialize TTS")
        except Exception as e:
            logger.error(f"TTS initialization error: {e}")
    
    return chromadb_success, tts_success

# Initialize enhanced features on startup
chromadb_ready, tts_ready = init_enhanced_features()

def clean_ansi_codes(text):
    """Remove ANSI color codes from text"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def format_response_for_web(response):
    """Format bot response for web display"""
    if not response:
        return ""
    
    # Clean ANSI codes
    clean_response = clean_ansi_codes(response)
    
    # Convert markdown-like formatting to HTML
    # Headers
    clean_response = re.sub(r'^# (.+)$', r'<h1>\1</h1>', clean_response, flags=re.MULTILINE)
    clean_response = re.sub(r'^## (.+)$', r'<h2>\1</h2>', clean_response, flags=re.MULTILINE)
    clean_response = re.sub(r'^### (.+)$', r'<h3>\1</h3>', clean_response, flags=re.MULTILINE)
    clean_response = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', clean_response, flags=re.MULTILINE)
    
    # Bold text
    clean_response = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', clean_response)
    
    # Lists
    clean_response = re.sub(r'^  • (.+)$', r'<li>\1</li>', clean_response, flags=re.MULTILINE)
    
    # Add line breaks
    clean_response = clean_response.replace('\n', '<br>')
    
    # Wrap consecutive <li> tags in <ul>
    clean_response = re.sub(r'(<li>.*?</li>(?:<br><li>.*?</li>)*)', r'<ul>\1</ul>', clean_response)
    clean_response = clean_response.replace('</li><br><li>', '</li><li>')
    
    return clean_response

@app.route('/')
def index():
    """Main page"""
    # Initialize session conversation history
    if 'conversation_history' not in session:
        session['conversation_history'] = []
    
    # Initialize bot
    init_bot()
    
    # Get available libraries for the sidebar
    libraries = []
    
    # Handle different bot types
    if hasattr(bot, 'known_libraries'):
        # Regular bot
        for lib_key, lib_info in bot.known_libraries.items():
            libraries.append({
                'key': lib_key,
                'name': lib_info['name'],
                'category': lib_info['category'],
                'language': lib_info['language'],
                'description': lib_info['description']
            })
    elif hasattr(bot, 'chromadb_manager') and bot.chromadb_manager:
        # Enhanced bot - get libraries from ChromaDB
        try:
            stats = bot.chromadb_manager.get_collection_stats()
            if stats.get('libraries', 0) > 0:
                # Get sample libraries for sidebar
                sample_results = bot.chromadb_manager.search_libraries("framework", n_results=10)
                for result in sample_results:
                    metadata = result.metadata
                    libraries.append({
                        'key': metadata.get('name', 'Unknown').lower().replace(' ', '_'),
                        'name': metadata.get('name', 'Unknown'),
                        'category': metadata.get('category', 'Unknown'),
                        'language': metadata.get('language', 'Unknown'),
                        'description': metadata.get('description', 'No description available')
                    })
        except Exception as e:
            logger.warning(f"Failed to load libraries from ChromaDB: {e}")
            # Fallback to default list
            libraries = [
                {'key': 'react', 'name': 'React', 'category': 'Frontend', 'language': 'JavaScript', 'description': 'A JavaScript library for building user interfaces'},
                {'key': 'vue', 'name': 'Vue.js', 'category': 'Frontend', 'language': 'JavaScript', 'description': 'Progressive framework for building user interfaces'},
                {'key': 'django', 'name': 'Django', 'category': 'Backend', 'language': 'Python', 'description': 'High-level Python web framework'},
                {'key': 'flask', 'name': 'Flask', 'category': 'Backend', 'language': 'Python', 'description': 'Lightweight WSGI web application framework'},
                {'key': 'express', 'name': 'Express.js', 'category': 'Backend', 'language': 'JavaScript', 'description': 'Fast, unopinionated web framework for Node.js'}
            ]
    
    return render_template('index.html', 
                         libraries=libraries,
                         ai_enabled=bot.use_ai,
                         conversation_history=session['conversation_history'])

@app.route('/chat', methods=['POST'])
def chat():
    """Enhanced chat endpoint with ChromaDB and TTS support"""
    data = request.get_json()
    user_message = data.get('message', '').strip()
    enable_tts = data.get('enable_tts', app.config['AUDIO_AUTOPLAY'])
    session_id = session.get('session_id', str(uuid.uuid4()))
    
    # Store session ID
    session['session_id'] = session_id
    
    if not user_message:
        return jsonify({'error': 'Empty message'}), 400
    
    # Initialize bot
    bot_instance = init_bot()
    
    # Add user message to bot's conversation history
    bot_instance.conversation_history.append({
        'timestamp': datetime.now().isoformat(),
        'user_input': user_message,
        'type': 'user'
    })
    
    # Process the message
    try:
        # Define similarity threshold for ChromaDB results
        SIMILARITY_THRESHOLD = 0.6  # Minimum similarity score to consider result relevant
        
        # Check if this is a library analysis request
        if user_message.lower().startswith('analyze '):
            library_name = user_message[8:].strip()  # Remove "analyze " prefix
            # Use enhanced method if available, otherwise use regular method
            if hasattr(bot_instance, 'analyze_library_enhanced'):
                response = bot_instance.analyze_library_enhanced(library_name)
            elif hasattr(bot_instance, 'analyze_library'):
                response = bot_instance.analyze_library(library_name)
            else:
                response = f"Library analysis not available for {library_name}"
        else:
            # Try to enhance with ChromaDB if available for other queries
            enhanced_response = None
            use_chromadb_response = False
            
            if chromadb_ready and chromadb_manager:
                try:
                    # Try semantic search for non-analysis queries
                    library_results = chromadb_manager.search_libraries(user_message, n_results=3)
                    faq_results = chromadb_manager.search_faqs(user_message, n_results=2)
                    
                    # Filter results by similarity threshold
                    relevant_library_results = [r for r in library_results if r.score >= SIMILARITY_THRESHOLD]
                    relevant_faq_results = [r for r in faq_results if r.score >= SIMILARITY_THRESHOLD]
                    
                    # Only use ChromaDB response if we have relevant results
                    if relevant_library_results or relevant_faq_results:
                        enhanced_response = format_enhanced_response(user_message, relevant_library_results, relevant_faq_results)
                        use_chromadb_response = True
                        logger.info(f"Using ChromaDB response - Libraries: {len(relevant_library_results)}, FAQs: {len(relevant_faq_results)}")
                    else:
                        logger.info(f"ChromaDB results below threshold - max library score: {max([r.score for r in library_results], default=0):.2f}, max FAQ score: {max([r.score for r in faq_results], default=0):.2f}")
                        
                except Exception as e:
                    logger.error(f"ChromaDB enhancement failed: {e}")
            
            # Use enhanced response if available and relevant, otherwise fallback to bot response
            if use_chromadb_response and enhanced_response:
                response = enhanced_response
            else:
                # Fallback to regular bot analysis functions
                response = bot_instance.process_input(user_message)
        
        if response == "exit":
            response = "Thank you for using Library Advisory System! 👋"
        
        # Clean and format response for web
        formatted_response = format_response_for_web(response) if response else "I'm sorry, I couldn't process your request."
        
        # Store user query in ChromaDB if available
        if chromadb_ready and chromadb_manager:
            try:
                chromadb_manager.store_user_query(
                    query=user_message,
                    response=response,
                    session_id=session_id,
                    user_intent=classify_user_intent(user_message),
                    resolved=True
                )
            except Exception as e:
                logger.error(f"Failed to store user query: {e}")
        
        # Add response to bot's conversation history
        if response and response != "exit":
            bot_instance.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'response': response,
                'type': 'assistant'
            })
        
        # Prepare response data
        response_data = {
            'response': formatted_response,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'has_audio': False,
            'enhanced': use_chromadb_response if 'use_chromadb_response' in locals() else False
        }
        
        # Generate TTS if requested and available
        if enable_tts and tts_ready and tts_manager and response:
            logger.info(f"TTS conditions check - enable_tts: {enable_tts}, tts_ready: {tts_ready}, tts_manager: {tts_manager is not None}, response: {bool(response)}")
            try:
                # Clean response for TTS
                tts_text = clean_response_for_tts(response)
                logger.info(f"TTS text after cleaning - length: {len(tts_text) if tts_text else 0}")
                
                if tts_text and len(tts_text.strip()) > 0:
                    # If text is still too long, create a summary
                    if len(tts_text) > 2500:
                        # Create a very short summary for extremely long text
                        sentences = tts_text.split('. ')
                        summary_parts = []
                        summary_parts.append(sentences[0] if sentences else "")  # First sentence
                        
                        # Add one key point from middle
                        if len(sentences) > 2:
                            summary_parts.append(sentences[len(sentences)//2])
                        
                        # Add conclusion if available
                        if len(sentences) > 1:
                            summary_parts.append(sentences[-1])
                        
                        tts_text = '. '.join(filter(None, summary_parts))
                        logger.info(f"Created summary for TTS - length: {len(tts_text)}")
                    
                    logger.info("Generating TTS audio...")
                    audio_result = tts_manager.generate_audio(tts_text)
                    logger.info(f"TTS result - success: {audio_result.success}")
                    
                    if audio_result.success:
                        # Store audio and provide URL
                        audio_id = store_temporary_audio(audio_result.audio_bytes)
                        logger.info(f"Audio stored with ID: {audio_id}")
                        
                        response_data.update({
                            'has_audio': True,
                            'audio_url': f'/api/tts/audio/{audio_id}',
                            'audio_id': audio_id,
                            'audio_duration': audio_result.duration_seconds,
                            'audio_cache_hit': audio_result.cache_hit,
                            'tts_text_length': len(tts_text)
                        })
                    else:
                        logger.warning(f"TTS generation failed: {audio_result.error_message}")
                else:
                    logger.warning(f"TTS text is empty or too short after cleaning")
            except Exception as e:
                logger.error(f"TTS processing failed: {e}", exc_info=True)
        
        # Add to session conversation history
        if 'conversation_history' not in session:
            session['conversation_history'] = []
        
        session['conversation_history'].append({
            'user': user_message,
            'bot': formatted_response,
            'timestamp': response_data['timestamp'],
            'has_audio': response_data['has_audio'],
            'enhanced': response_data['enhanced']
        })
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        return jsonify({'error': f'Error processing message: {str(e)}'}), 500

def format_enhanced_response(query: str, library_results: list, faq_results: list) -> str:
    """Format enhanced response using ChromaDB results with similarity scores"""
    response_parts = []
    
    # Add relevant libraries
    if library_results:
        response_parts.append("## 📚 Relevant Libraries")
        for result in library_results[:3]:
            metadata = result.metadata
            response_parts.append(f"**{metadata.get('name', 'Unknown')}** - {metadata.get('category', 'Unknown')} ({metadata.get('language', 'Unknown')})")
            response_parts.append(f"*Similarity: {result.score:.1%}*")
            
            # Add description if available
            if metadata.get('description'):
                response_parts.append(f"{metadata['description']}")
            response_parts.append("")
    
    # Add relevant FAQs
    if faq_results:
        response_parts.append("## ❓ Related Information")
        for result in faq_results:
            metadata = result.metadata
            response_parts.append(f"**Q: {metadata.get('question', 'Unknown question')}**")
            # Extract answer from document
            doc_parts = result.document.split("Answer: ")
            if len(doc_parts) > 1:
                answer = doc_parts[1].strip()
                response_parts.append(f"A: {answer}")
            response_parts.append("")
    
    if not response_parts:
        return None
    
    # Add header
    final_response = f"## 🤖 Enhanced Response for: {query}\n\n" + "\n".join(response_parts)
    
    # Add footer with source information
    final_response += "\n---\n*This response was enhanced using semantic search from our knowledge base.*"
    
    return final_response

def classify_user_intent(query: str) -> str:
    """Classify user intent for analytics"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['compare', 'vs', 'versus', 'difference']):
        return 'comparison'
    elif any(word in query_lower for word in ['recommend', 'suggest', 'best', 'good']):
        return 'recommendation'
    elif any(word in query_lower for word in ['analyze', 'tell me about', 'what is']):
        return 'analysis'
    elif any(word in query_lower for word in ['help', 'how', 'tutorial']):
        return 'help'
    else:
        return 'general'

def clean_response_for_tts(response: str) -> str:
    """Clean response text for TTS processing - Enhanced version"""
    if not response:
        return ""
    
    # Remove HTML tags first
    clean_text = re.sub(r'<[^>]+>', '', response)
    
    # Remove markdown headers
    clean_text = re.sub(r'^#+\s+', '', clean_text, flags=re.MULTILINE)
    
    # Remove markdown formatting
    clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_text)
    clean_text = re.sub(r'\*(.*?)\*', r'\1', clean_text)
    
    # Remove code blocks
    clean_text = re.sub(r'```.*?```', '', clean_text, flags=re.DOTALL)
    clean_text = re.sub(r'`(.*?)`', r'\1', clean_text)
    
    # Remove links but keep text
    clean_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean_text)
    
    # Remove emojis and special characters for TTS
    clean_text = re.sub(r'[📚🤖❓⚖️🎯💡📊🔍⭐🚀💰🛡️⚙️👥🔧⚠️✅❌ℹ️→•─]', '', clean_text)
    
    # Remove excessive dashes and underscores
    clean_text = re.sub(r'[─_-]{3,}', '. ', clean_text)
    
    # Clean up extra whitespace and newlines
    clean_text = re.sub(r'\n+', '. ', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    # Remove multiple periods
    clean_text = re.sub(r'\.{2,}', '.', clean_text)
    
    # Limit length for TTS - Intelligent summarization
    max_length = 2500  # Tăng giới hạn
    if len(clean_text) > max_length:
        # Try to find good breaking points
        sentences = clean_text.split('. ')
        
        # Prioritize important sections
        important_parts = []
        current_length = 0
        
        # Always include the first few sentences (overview)
        for i, sentence in enumerate(sentences[:5]):
            if current_length + len(sentence) < max_length * 0.4:  # Use 40% for overview
                important_parts.append(sentence)
                current_length += len(sentence)
            else:
                break
        
        # Add key conclusions if space available
        remaining_length = max_length - current_length
        for sentence in reversed(sentences[-3:]):  # Last 3 sentences often contain conclusions
            if len(sentence) < remaining_length * 0.3:
                important_parts.append(sentence)
                remaining_length -= len(sentence)
                break
        
        # Fill remaining space with middle content
        middle_start = len(important_parts)
        for sentence in sentences[middle_start:-3]:
            if current_length + len(sentence) < max_length:
                important_parts.append(sentence)
                current_length += len(sentence)
            else:
                break
        
        clean_text = '. '.join(important_parts)
        if not clean_text.endswith('.'):
            clean_text += '.'
    
    return clean_text

def store_temporary_audio(audio_bytes: bytes) -> str:
    """Store temporary audio file and return ID"""
    audio_id = str(uuid.uuid4())
    
    try:
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.wav',
            prefix='tts_'
        )
        temp_file.write(audio_bytes)
        temp_file.close()
        
        # Store reference with timestamp for cleanup
        temp_audio_files[audio_id] = {
            'file_path': temp_file.name,
            'created': datetime.now(),
            'size': len(audio_bytes)
        }
        
        # Cleanup old files (keep last 20)
        if len(temp_audio_files) > 20:
            cleanup_old_audio_files()
        
        return audio_id
        
    except Exception as e:
        logger.error(f"Failed to store temporary audio: {e}")
        return ""

def cleanup_old_audio_files():
    """Clean up old temporary audio files"""
    try:
        # Sort by creation time
        sorted_files = sorted(
            temp_audio_files.items(),
            key=lambda x: x[1]['created']
        )
        
        # Remove oldest files, keep 15 most recent
        for audio_id, file_info in sorted_files[:-15]:
            try:
                if os.path.exists(file_info['file_path']):
                    os.remove(file_info['file_path'])
                del temp_audio_files[audio_id]
            except Exception as e:
                logger.warning(f"Failed to cleanup audio file {audio_id}: {e}")
                
    except Exception as e:
        logger.error(f"Audio cleanup failed: {e}")

@app.route('/analyze/<library_name>')
def analyze_library(library_name):
    """Analyze a specific library"""
    bot_instance = init_bot()
    
    try:
        analysis = bot_instance.analyze_library(library_name)
        formatted_analysis = format_response_for_web(analysis)
        
        return jsonify({
            'analysis': formatted_analysis,
            'library_name': library_name
        })
        
    except Exception as e:
        return jsonify({'error': f'Error analyzing library: {str(e)}'}), 500

@app.route('/libraries')
def get_libraries():
    """Get all available libraries"""
    bot_instance = init_bot()
    
    libraries = []
    for lib_key, lib_info in bot_instance.known_libraries.items():
        libraries.append({
            'key': lib_key,
            'name': lib_info['name'],
            'category': lib_info['category'],
            'language': lib_info['language'],
            'description': lib_info['description'],
            'license': lib_info['license'],
            'popularity': lib_info['popularity'],
            'alternatives': lib_info.get('alternatives', [])
        })
    
    return jsonify({'libraries': libraries})

@app.route('/compare')
def compare():
    """Compare libraries page"""
    return render_template('compare.html')

@app.route('/compare_libraries', methods=['POST'])
def compare_libraries():
    """Compare two libraries"""
    data = request.get_json()
    lib1 = data.get('lib1', '').strip()
    lib2 = data.get('lib2', '').strip()
    
    if not lib1 or not lib2:
        return jsonify({'error': 'Both library names are required'}), 400
    
    bot_instance = init_bot()
    
    try:
        comparison = bot_instance.compare_libraries(lib1, lib2)
        formatted_comparison = format_response_for_web(comparison)
        
        return jsonify({
            'comparison': formatted_comparison,
            'lib1': lib1,
            'lib2': lib2
        })
        
    except Exception as e:
        return jsonify({'error': f'Error comparing libraries: {str(e)}'}), 500

@app.route('/recommendations')
def recommendations():
    """Recommendations page"""
    return render_template('recommendations.html')

@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    """Get recommendations for a category"""
    data = request.get_json()
    category = data.get('category', '').strip()
    
    if not category:
        return jsonify({'error': 'Category is required'}), 400
    
    bot_instance = init_bot()
    
    try:
        recommendations = bot_instance.get_recommendations(category)
        formatted_recommendations = format_response_for_web(recommendations)
        
        return jsonify({
            'recommendations': formatted_recommendations,
            'category': category
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting recommendations: {str(e)}'}), 500

@app.route('/save_conversation', methods=['POST'])
def save_conversation():
    """Save conversation to markdown file"""
    bot_instance = init_bot()
    
    if not bot_instance.conversation_history:
        return jsonify({'error': 'No conversation to save'}), 400
    
    try:
        filepath = bot_instance.save_conversation_to_markdown()
        if filepath:
            return jsonify({
                'success': True,
                'filepath': filepath,
                'message': f'Conversation saved to {filepath}'
            })
        else:
            return jsonify({'error': 'Failed to save conversation'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error saving conversation: {str(e)}'}), 500

@app.route('/clear_conversation', methods=['POST'])
def clear_conversation():
    """Clear conversation history"""
    session['conversation_history'] = []
    
    # Also clear bot's history
    bot_instance = init_bot()
    bot_instance.conversation_history = []
    
    return jsonify({'success': True, 'message': 'Conversation cleared'})

@app.route('/help')
def help_page():
    """Help page"""
    bot_instance = init_bot()
    return render_template('help.html', ai_enabled=bot_instance.use_ai)

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


# === TTS API ENDPOINTS ===

@app.route('/api/tts/generate', methods=['POST'])
def generate_tts():
    """Generate TTS audio for given text"""
    if not tts_ready or not tts_manager:
        return jsonify({'error': 'TTS not available'}), 503
    
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        use_cache = data.get('use_cache', True)
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        if len(text) > int(os.environ.get('TTS_MAX_TEXT_LENGTH', '1000')):
            return jsonify({'error': f'Text too long (max {os.environ.get("TTS_MAX_TEXT_LENGTH", "1000")} characters)'}), 400
        
        # Generate audio
        audio_result = tts_manager.generate_audio(text, use_cache=use_cache)
        
        if not audio_result.success:
            return jsonify({'error': f'TTS generation failed: {audio_result.error_message}'}), 500
        
        # Store temporary audio file
        audio_id = store_temporary_audio(audio_result.audio_bytes)
        
        if not audio_id:
            return jsonify({'error': 'Failed to store audio file'}), 500
        
        return jsonify({
            'success': True,
            'audio_id': audio_id,
            'audio_url': f'/api/tts/audio/{audio_id}',
            'duration_seconds': audio_result.duration_seconds,
            'text_length': len(text),
            'cache_hit': audio_result.cache_hit,
            'processing_time': audio_result.processing_time
        })
        
    except Exception as e:
        logger.error(f"TTS generation API error: {e}")
        return jsonify({'error': f'TTS generation failed: {str(e)}'}), 500

@app.route('/api/tts/audio/<audio_id>')
def serve_tts_audio(audio_id):
    """Serve generated TTS audio file"""
    try:
        if audio_id not in temp_audio_files:
            return jsonify({'error': 'Audio file not found'}), 404
        
        file_info = temp_audio_files[audio_id]
        file_path = file_info['file_path']
        
        if not os.path.exists(file_path):
            # Clean up reference if file doesn't exist
            del temp_audio_files[audio_id]
            return jsonify({'error': 'Audio file not found'}), 404
        
        return send_file(
            file_path,
            mimetype='audio/wav',
            as_attachment=False,
            download_name=f'response_{audio_id}.wav'
        )
        
    except Exception as e:
        logger.error(f"Error serving audio file {audio_id}: {e}")
        return jsonify({'error': 'Failed to serve audio file'}), 500

@app.route('/api/tts/status')
def tts_status():
    """Get TTS system status"""
    if not tts_ready or not tts_manager:
        return jsonify({
            'available': False,
            'error': 'TTS system not initialized'
        })
    
    try:
        status = tts_manager.get_status()
        
        # Add temporary file stats
        temp_file_stats = {
            'count': len(temp_audio_files),
            'total_size_mb': sum(f['size'] for f in temp_audio_files.values()) / (1024 * 1024)
        }
        
        status['temp_files'] = temp_file_stats
        status['available'] = True
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"TTS status error: {e}")
        return jsonify({'available': False, 'error': str(e)})

# === CHROMADB API ENDPOINTS ===

@app.route('/api/chromadb/search', methods=['POST'])
def search_chromadb():
    """Search ChromaDB collections"""
    if not chromadb_ready or not chromadb_manager:
        return jsonify({'error': 'ChromaDB not available'}), 503
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        collection_type = data.get('collection', 'libraries')  # libraries, faqs, user_queries
        n_results = min(int(data.get('n_results', 5)), 20)  # Limit to 20
        filters = data.get('filters', {})
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Search appropriate collection
        if collection_type == 'libraries':
            results = chromadb_manager.search_libraries(query, n_results, filters)
        elif collection_type == 'faqs':
            results = chromadb_manager.search_faqs(query, n_results)
        else:
            return jsonify({'error': 'Invalid collection type'}), 400
        
        # Format results for JSON response
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': result.id,
                'document': result.document,
                'metadata': result.metadata,
                'score': result.score,
                'distance': result.distance
            })
        
        return jsonify({
            'success': True,
            'query': query,
            'collection': collection_type,
            'results': formatted_results,
            'total_results': len(formatted_results)
        })
        
    except Exception as e:
        logger.error(f"ChromaDB search error: {e}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/api/chromadb/status')
def chromadb_status():
    """Get ChromaDB system status"""
    if not chromadb_ready or not chromadb_manager:
        return jsonify({
            'available': False,
            'error': 'ChromaDB system not initialized'
        })
    
    try:
        stats = chromadb_manager.get_collection_stats()
        
        return jsonify({
            'available': True,
            'collections': stats,
            'total_documents': sum(stats.values()),
            'embedding_model': chromadb_manager.embedding_model,
            'persist_directory': chromadb_manager.persist_directory
        })
        
    except Exception as e:
        logger.error(f"ChromaDB status error: {e}")
        return jsonify({'available': False, 'error': str(e)})

# === SYSTEM STATUS ENDPOINTS ===

@app.route('/api/status')
def system_status():
    """Get overall system status"""
    return jsonify({
        'system': 'Library Advisory System',
        'version': '2.0.0',
        'enhanced_features': ENHANCED_FEATURES_AVAILABLE,
        'chromadb': {
            'enabled': app.config['CHROMADB_ENABLED'],
            'ready': chromadb_ready
        },
        'tts': {
            'enabled': app.config['TTS_ENABLED'],
            'ready': tts_ready
        },
        'audio_autoplay': app.config['AUDIO_AUTOPLAY'],
        'session_count': len([k for k in session.keys() if k.startswith('session_')]),
        'temp_audio_files': len(temp_audio_files)
    })

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'flask': True,
            'chromadb': chromadb_ready,
            'tts': tts_ready
        }
    }
    
    # Determine overall health
    if not chromadb_ready and app.config['CHROMADB_ENABLED']:
        health_status['status'] = 'degraded'
    if not tts_ready and app.config['TTS_ENABLED']:
        health_status['status'] = 'degraded'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

# === INITIALIZATION ENDPOINT ===

@app.route('/api/initialize', methods=['POST'])
def initialize_system():
    """Reinitialize enhanced features"""
    global chromadb_ready, tts_ready
    
    try:
        chromadb_success, tts_success = init_enhanced_features()
        chromadb_ready, tts_ready = chromadb_success, tts_success
        
        return jsonify({
            'success': True,
            'chromadb_initialized': chromadb_success,
            'tts_initialized': tts_success,
            'message': 'System reinitialized successfully'
        })
        
    except Exception as e:
        logger.error(f"System initialization error: {e}")
        return jsonify({
            'success': False,
            'error': f'Initialization failed: {str(e)}'
        }), 500


if __name__ == '__main__':
    # Create directories if they don't exist
    os.makedirs('./chromadb_data', exist_ok=True)
    os.makedirs('./tts_cache', exist_ok=True)
    os.makedirs('./logs', exist_ok=True)
    
    # Run the application
    app.run(
        debug=os.environ.get('FLASK_DEBUG', 'true').lower() == 'true',
        host=os.environ.get('FLASK_HOST', '0.0.0.0'),
        port=int(os.environ.get('FLASK_PORT', '5001'))
    )
