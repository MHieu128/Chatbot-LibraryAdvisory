#!/usr/bin/env python3
"""
Library Advisory System Web Application
A Flask-based web interface for the Library Advisory System
"""

from flask import Flask, render_template, request, jsonify, session
import os
import json
from datetime import datetime
import re
from library_advisory_bot import LibraryAdvisoryBot, Colors

# Import for speech-to-text
from transformers import pipeline
import tempfile

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Global bot instance
bot = None

# Initialize Hugging Face speech-to-text pipeline globally to avoid reloading
speech_to_text_pipeline = pipeline("automatic-speech-recognition", model="openai/whisper-base")

def init_bot():
    """Initialize the bot instance"""
    global bot
    if bot is None:
        bot = LibraryAdvisoryBot()
    return bot

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
    for lib_key, lib_info in bot.known_libraries.items():
        libraries.append({
            'key': lib_key,
            'name': lib_info['name'],
            'category': lib_info['category'],
            'language': lib_info['language'],
            'description': lib_info['description']
        })
    
    return render_template('index.html', 
                         libraries=libraries,
                         ai_enabled=bot.use_ai,
                         conversation_history=session['conversation_history'])

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
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
        response = bot_instance.process_input(user_message)
        
        if response == "exit":
            response = "Thank you for using Library Advisory System! 👋"
        
        # Clean and format response for web
        formatted_response = format_response_for_web(response) if response else "I'm sorry, I couldn't process your request."
        
        # Add response to bot's conversation history
        if response and response != "exit":
            bot_instance.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'response': response,
                'type': 'assistant'
            })
        
        # Add to session conversation history
        if 'conversation_history' not in session:
            session['conversation_history'] = []
        
        session['conversation_history'].append({
            'user': user_message,
            'bot': formatted_response,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
        
        return jsonify({
            'response': formatted_response,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing message: {str(e)}'}), 500

@app.route('/speech_to_text', methods=['POST'])
def speech_to_text():
    """Endpoint to receive audio file and return transcribed text"""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    
    if audio_file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    temp_file_path = None
    try:
        # Create a dedicated temp directory within the project
        temp_dir = os.path.join(os.getcwd(), 'temp_audio')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
        
        # Generate a unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        temp_filename = f"audio_{timestamp}.wav"
        temp_file_path = os.path.join(temp_dir, temp_filename)
        
        # Save the uploaded audio file
        audio_file.save(temp_file_path)
        
        # Verify file was created and is readable
        if not os.path.exists(temp_file_path):
            raise Exception("Failed to create temporary audio file")
        
        # Try to use the speech-to-text pipeline
        try:
            transcription = speech_to_text_pipeline(temp_file_path)
            text = transcription.get('text', '')
            return jsonify({'transcription': text})
        except Exception as pipeline_error:
            # Check if it's an ffmpeg-related error
            error_str = str(pipeline_error).lower()
            if 'ffmpeg' in error_str or 'audio' in error_str:
                return jsonify({
                    'error': 'Audio processing requires ffmpeg to be installed. Please install ffmpeg and add it to your system PATH, or use a different audio format.',
                    'details': str(pipeline_error),
                    'solution': 'Install ffmpeg from https://ffmpeg.org/download.html and add it to your system PATH'
                }), 500
            else:
                raise pipeline_error
        
    except PermissionError as e:
        return jsonify({
            'error': 'Permission denied accessing temporary files. Please check folder permissions.',
            'details': str(e),
            'solution': 'Try running the application as administrator or check folder permissions'
        }), 500
    except Exception as e:
        return jsonify({'error': f'Error during transcription: {str(e)}'}), 500
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as cleanup_error:
                print(f"Warning: Could not clean up temporary file {temp_file_path}: {cleanup_error}")

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
