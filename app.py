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

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Global bot instance
bot = None

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
    clean_response = re.sub(r'^\s*•\s+(.*)$', r'<li>\1</li>', clean_response, flags=re.MULTILINE)
    
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
