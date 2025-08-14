#!/usr/bin/env python3
"""
Library Advisory System Web Application
A Flask-based web interface for the Library Advisory System
"""

from flask import Flask, render_template, request, jsonify, session
import os
import json
import re
import html
import logging
from datetime import datetime
from functools import wraps
from library_advisory_bot import LibraryAdvisoryBot

app = Flask(__name__)
# Prefer a stable secret key via env var; fallback to random for local dev
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or os.urandom(24)

# Configure logging for Flask app
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global bot instance
bot = None

def handle_api_errors(func):
    """Decorator for API error handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"API error in {func.__name__}: {str(e)}")
            return jsonify({'error': f'Internal server error: {str(e)}'}), 500
    return wrapper

def init_bot():
    """Initialize the bot instance"""
    global bot
    if bot is None:
        bot = LibraryAdvisoryBot()
    return bot

def clean_ansi_codes(text):
    """Remove ANSI color codes from text"""
    return re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])').sub('', text)

def format_response_for_web(response):
    """Format bot response for web display with enhanced formatting and security"""
    if not response:
        return ""
    
    # Clean ANSI codes and escape HTML to prevent XSS
    clean_response = html.escape(clean_ansi_codes(response))
    
    # Convert box drawing characters and borders to styled HTML
    clean_response = re.sub(r'^┌[─]+┐$', '<div class="analysis-card-border-top"></div>', clean_response, flags=re.MULTILINE)
    clean_response = re.sub(r'^└[─]+┘$', '<div class="analysis-card-border-bottom"></div>', clean_response, flags=re.MULTILINE)
    clean_response = re.sub(r'^│(.*)│$', r'<div class="analysis-card-content">\1</div>', clean_response, flags=re.MULTILINE)
    
    # Convert section headers with improved styling
    clean_response = re.sub(r'^═+$', '<hr class="section-divider">', clean_response, flags=re.MULTILINE)
    clean_response = re.sub(r'^[\-\u2500─]{3,}$', '<hr class="content-divider">', clean_response, flags=re.MULTILINE)
    
    # Enhanced markdown-like formatting
    clean_response = re.sub(r'^# (.+)$', r'<h1 class="analysis-title"><i class="fas fa-search me-2"></i>\1</h1>', clean_response, flags=re.MULTILINE)
    clean_response = re.sub(r'^## (.+)$', r'<h2 class="analysis-section">\1</h2>', clean_response, flags=re.MULTILINE)
    clean_response = re.sub(r'^### (.+)$', r'<h3 class="analysis-subsection">\1</h3>', clean_response, flags=re.MULTILINE)
    clean_response = re.sub(r'^#### (.+)$', r'<h4 class="analysis-subheading">\1</h4>', clean_response, flags=re.MULTILINE)
    
    # Convert emojis and special characters to better web display
    emoji_map = {
        '📚': '<i class="fas fa-book text-primary"></i>',
        '🔍': '<i class="fas fa-search text-info"></i>',
        '✅': '<i class="fas fa-check-circle text-success"></i>',
        '⚠️': '<i class="fas fa-exclamation-triangle text-warning"></i>',
        '❌': '<i class="fas fa-times-circle text-danger"></i>',
        'ℹ️': '<i class="fas fa-info-circle text-info"></i>',
        '⭐': '<i class="fas fa-star text-warning"></i>',
        '→': '<i class="fas fa-arrow-right text-muted"></i>',
        '✓': '<i class="fas fa-check text-success"></i>',
        '✗': '<i class="fas fa-times text-danger"></i>',
        '⚙️': '<i class="fas fa-cog text-secondary"></i>',
        '🛡️': '<i class="fas fa-shield-alt text-primary"></i>',
        '💰': '<i class="fas fa-dollar-sign text-success"></i>',
        '📊': '<i class="fas fa-chart-bar text-info"></i>',
        '🎯': '<i class="fas fa-bullseye text-primary"></i>',
        '💡': '<i class="fas fa-lightbulb text-warning"></i>',
        '⚖️': '<i class="fas fa-balance-scale text-secondary"></i>',
        '🤖': '<i class="fas fa-robot text-primary"></i>',
        '★': '<i class="fas fa-star text-warning"></i>',
        '☆': '<i class="far fa-star text-muted"></i>'
    }
    
    for emoji, icon in emoji_map.items():
        clean_response = clean_response.replace(emoji, icon)
    
    # Enhanced text formatting
    clean_response = re.sub(r'\*\*(.+?)\*\*', r'<strong class="text-primary">\1</strong>', clean_response)
    clean_response = re.sub(r'\*(.+?)\*', r'<em>\1</em>', clean_response)
    
    # Better list handling with improved styling
    clean_response = re.sub(r'^\s*•\s+(.*)$', r'<li class="analysis-list-item">\1</li>', clean_response, flags=re.MULTILINE)
    clean_response = re.sub(r'^\s*(\d+)\.\s+(.*)$', r'<li class="analysis-numbered-item"><span class="item-number">\1</span>\2</li>', clean_response, flags=re.MULTILINE)
    
    # Handle key-value pairs with better styling
    clean_response = re.sub(r'(\w+):\s*([^<\n]+)', r'<span class="key-value-pair"><strong class="kv-key">\1:</strong> <span class="kv-value">\2</span></span>', clean_response)
    
    # Add line breaks
    clean_response = clean_response.replace('\n', '<br>')
    
    # Wrap consecutive <li> tags in appropriate lists
    clean_response = re.sub(r'(<li class="analysis-list-item">.*?</li>(?:<br><li class="analysis-list-item">.*?</li>)*)', r'<ul class="analysis-list">\1</ul>', clean_response)
    clean_response = re.sub(r'(<li class="analysis-numbered-item">.*?</li>(?:<br><li class="analysis-numbered-item">.*?</li>)*)', r'<ol class="analysis-numbered-list">\1</ol>', clean_response)
    clean_response = clean_response.replace('</li><br><li class="analysis-list-item">', '</li><li class="analysis-list-item">')
    clean_response = clean_response.replace('</li><br><li class="analysis-numbered-item">', '</li><li class="analysis-numbered-item">')
    
    # Clean up card structures
    clean_response = re.sub(r'<div class="analysis-card-border-top"></div><br><div class="analysis-card-content">', '<div class="analysis-card"><div class="analysis-card-content">', clean_response)
    clean_response = re.sub(r'</div><br><div class="analysis-card-border-bottom"></div>', '</div></div>', clean_response)
    
    # Clean up extra breaks around elements
    clean_response = clean_response.replace('<br><hr class="section-divider"><br>', '<hr class="section-divider">')
    clean_response = clean_response.replace('<br><hr class="content-divider"><br>', '<hr class="content-divider">')
    clean_response = clean_response.replace('<hr class="section-divider"><br>', '<hr class="section-divider">')
    clean_response = clean_response.replace('<hr class="content-divider"><br>', '<hr class="content-divider">')
    
    return clean_response

def handle_api_request(func, *args, **kwargs):
    """Generic API request handler with error handling"""
    try:
        result = func(*args, **kwargs)
        if isinstance(result, str):
            return jsonify({'response': format_response_for_web(result)})
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

def update_conversation_history(user_message, bot_response):
    """Update session conversation history safely"""
    if 'conversation_history' not in session:
        session['conversation_history'] = []
    
    # Reassign to ensure Flask detects the session change
    history = list(session['conversation_history'])
    history.append({
        'user': user_message,
        'bot': format_response_for_web(bot_response),
        'timestamp': datetime.now().strftime('%H:%M:%S')
    })
    session['conversation_history'] = history

@app.route('/')
def index():
    """Main page"""
    if 'conversation_history' not in session:
        session['conversation_history'] = []
    
    bot_instance = init_bot()
    
    # Get libraries for sidebar
    libraries = [
        {
            'key': key,
            'name': lib.name,
            'category': lib.category,
            'language': lib.language,
            'description': lib.description
        }
        for key, lib in bot_instance.known_libraries.items()
    ]
    
    return render_template('index.html', 
                         libraries=libraries,
                         ai_enabled=bot_instance.use_ai,
                         conversation_history=session['conversation_history'])

@app.route('/chat', methods=['POST'])
@handle_api_errors
def chat():
    """Handle chat messages"""
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'Empty message'}), 400
    
    bot_instance = init_bot()
    
    # Add to bot's conversation history
    bot_instance.conversation_history.append({
        'timestamp': datetime.now().isoformat(),
        'user_input': user_message,
        'type': 'user'
    })
    
    def process_chat():
        response = bot_instance.process_input(user_message)
        if response == "exit":
            response = "Thank you for using Library Advisory System! 👋"
        
        formatted_response = format_response_for_web(response) if response else "I'm sorry, I couldn't process your request."
        
        # Add to bot's history
        if response and response != "exit":
            bot_instance.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'response': response,
                'type': 'assistant'
            })
        
        # Update session
        update_conversation_history(user_message, response)
        
        return {
            'response': formatted_response,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
    
    return handle_api_request(process_chat)

@app.route('/analyze/<library_name>')
@handle_api_errors
def analyze_library(library_name):
    """Analyze a specific library"""
    bot_instance = init_bot()
    
    def analyze():
        analysis = bot_instance.analyze_library(library_name)
        return {
            'analysis': format_response_for_web(analysis),
            'library_name': library_name
        }
    
    return handle_api_request(analyze)

@app.route('/libraries')
def get_libraries():
    """Get all available libraries"""
    bot_instance = init_bot()
    
    libraries = [
        {
            'key': key,
            'name': lib.name,
            'category': lib.category,
            'language': lib.language,
            'description': lib.description,
            'license': lib.license,
            'popularity': lib.popularity,
            'alternatives': lib.alternatives
        }
        for key, lib in bot_instance.known_libraries.items()
    ]
    
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
    
    def compare():
        comparison = bot_instance.compare_libraries(lib1, lib2)
        return {
            'comparison': format_response_for_web(comparison),
            'lib1': bot_instance.get_canonical_display_name(lib1),
            'lib2': bot_instance.get_canonical_display_name(lib2)
        }
    
    return handle_api_request(compare)

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
    
    def get_recs():
        recommendations = bot_instance.get_recommendations(category)
        return {
            'recommendations': format_response_for_web(recommendations),
            'category': category
        }
    
    return handle_api_request(get_recs)

@app.route('/save_conversation', methods=['POST'])
def save_conversation():
    """Save conversation to markdown file"""
    bot_instance = init_bot()
    
    if not bot_instance.conversation_history:
        return jsonify({'error': 'No conversation to save'}), 400
    
    def save():
        filepath = bot_instance.save_conversation_to_markdown()
        if filepath:
            return {
                'success': True,
                'filepath': filepath,
                'message': f'Conversation saved to {filepath}'
            }
        else:
            raise Exception('Failed to save conversation')
    
    return handle_api_request(save)

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
