#!/usr/bin/env python3
"""
Enhanced Library Advisory System Terminal Chatbot with ChromaDB integration
A comprehensive library evaluation and recommendation system with semantic search
"""

import os
import sys
import json
import re
import requests
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import argparse

# Import required packages for Azure OpenAI
try:
    from openai import AzureOpenAI
    from dotenv import load_dotenv
    AZURE_OPENAI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Azure OpenAI dependencies not installed. Run: pip install -r requirements.txt")
    print(f"Error: {e}")
    AZURE_OPENAI_AVAILABLE = False

# Import ChromaDB utilities
try:
    from chromadb_utils import ChromaDBManager, get_chromadb_manager, SearchResult
    CHROMADB_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ChromaDB dependencies not installed. Run: pip install -r requirements.txt")
    print(f"Error: {e}")
    CHROMADB_AVAILABLE = False

# Modern color scheme for terminal output
class Colors:
    # Primary colors - Modern and accessible
    PRIMARY = '\033[38;5;33m'      # Modern blue
    SUCCESS = '\033[38;5;46m'      # Bright green
    WARNING = '\033[38;5;220m'     # Amber yellow
    ERROR = '\033[38;5;196m'       # Bright red
    INFO = '\033[38;5;117m'        # Light cyan
    
    # Semantic colors
    HEADER = '\033[38;5;99m'       # Purple
    ACCENT = '\033[38;5;208m'      # Orange
    MUTED = '\033[38;5;244m'       # Gray
    
    # Text styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    STRIKETHROUGH = '\033[9m'
    
    # Reset
    ENDC = '\033[0m'
    RESET = '\033[0m'
    
    # Legacy compatibility
    OKBLUE = '\033[38;5;33m'
    OKCYAN = '\033[38;5;117m'
    OKGREEN = '\033[38;5;46m'
    FAIL = '\033[38;5;196m'

class ModernFormatter:
    """Modern terminal formatter with enhanced visual design"""
    
    @staticmethod
    def get_terminal_width() -> int:
        """Get terminal width, default to 80 if unable to detect"""
        try:
            import shutil
            return shutil.get_terminal_size().columns
        except:
            return 80
    
    @staticmethod
    def create_box(content: str, title: str = "", style: str = "single") -> str:
        """Create a modern box around content"""
        width = min(ModernFormatter.get_terminal_width() - 4, 100)
        
        # Box drawing characters
        if style == "double":
            top_left, top_right = "╔", "╗"
            bottom_left, bottom_right = "╚", "╝"
            horizontal, vertical = "═", "║"
            title_left, title_right = "╡", "╞"
        else:  # single
            top_left, top_right = "┌", "┐"
            bottom_left, bottom_right = "└", "┘"
            horizontal, vertical = "─", "│"
            title_left, title_right = "┤", "├"
        
        lines = content.split('\n')
        
        # Top border
        if title:
            title_len = len(title) + 2
            remaining = width - title_len - 2
            left_border = horizontal * (remaining // 2)
            right_border = horizontal * (remaining - remaining // 2)
            top = f"{top_left}{left_border}{title_left} {title} {title_right}{right_border}{top_right}"
        else:
            top = f"{top_left}{horizontal * width}{top_right}"
        
        # Content lines
        content_lines = []
        for line in lines:
            clean_line = ModernFormatter.strip_ansi(line)
            if len(clean_line) > width - 2:
                # Word wrap
                words = clean_line.split()
                current_line = ""
                for word in words:
                    if len(current_line + word + " ") <= width - 2:
                        current_line += word + " "
                    else:
                        if current_line:
                            content_lines.append(f"{vertical} {current_line.ljust(width-2)} {vertical}")
                        current_line = word + " "
                if current_line:
                    content_lines.append(f"{vertical} {current_line.ljust(width-2)} {vertical}")
            else:
                content_lines.append(f"{vertical} {line.ljust(width-2)} {vertical}")
        
        # Bottom border
        bottom = f"{bottom_left}{horizontal * width}{bottom_right}"
        
        return f"{top}\n" + "\n".join(content_lines) + f"\n{bottom}"
    
    @staticmethod
    def strip_ansi(text: str) -> str:
        """Remove ANSI escape sequences from text"""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    @staticmethod
    def create_badge(text: str, color: str = Colors.PRIMARY, bg_color: str = "") -> str:
        """Create a modern badge"""
        if bg_color:
            return f"{bg_color}{Colors.BOLD} {text} {Colors.RESET}"
        return f"{color}{Colors.BOLD}[{text}]{Colors.RESET}"
    
    @staticmethod
    def create_card(title: str, content: str, icon: str = "", color: str = Colors.PRIMARY) -> str:
        """Create a modern card layout"""
        width = min(ModernFormatter.get_terminal_width() - 4, 80)
        
        # Header
        header_icon = f"{icon} " if icon else ""
        header = f"{color}{Colors.BOLD}{header_icon}{title}{Colors.RESET}"
        
        # Separator
        separator = f"{color}{'─' * width}{Colors.RESET}"
        
        # Content
        content_lines = content.split('\n')
        formatted_content = []
        for line in content_lines:
            if line.strip():
                formatted_content.append(f"  {line}")
            else:
                formatted_content.append("")
        
        return f"{header}\n{separator}\n" + "\n".join(formatted_content) + "\n"

class Icons:
    """Modern Unicode icons for better visual design"""
    LIBRARY = "📚"
    ANALYSIS = "🔍"
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    INFO = "ℹ️"
    STAR = "⭐"
    ARROW_RIGHT = "→"
    ARROW_DOWN = "↓"
    BULLET = "•"
    CHECK = "✓"
    CROSS = "✗"
    GEAR = "⚙️"
    SHIELD = "🛡️"
    MONEY = "💰"
    CHART = "📊"
    TARGET = "🎯"
    ROCKET = "🚀"
    LIGHTBULB = "💡"
    COMPARE = "⚖️"
    DOWNLOAD = "📥"
    LICENSE = "📋"
    SECURITY = "🔒"
    PERFORMANCE = "⚡"
    COMMUNITY = "👥"
    MAINTENANCE = "🔧"
    RISK = "⚠️"
    SEMANTIC = "🧠"
    DATABASE = "🗄️"

@dataclass
class LibraryAnalysis:
    """Data structure for library analysis results"""
    name: str
    overview: str
    advantages: List[str]
    disadvantages: List[str]
    license_info: Dict[str, str]
    cost_analysis: Dict[str, str]
    risk_assessment: Dict[str, str]
    technical_info: Dict[str, str]
    similar_libraries: List[Dict[str, str]]
    recommendations: Dict[str, str]

class EnhancedLibraryAdvisoryBot:
    """Enhanced chatbot class with ChromaDB and semantic search capabilities"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        self.conversation_history = []
        self.session_id = str(uuid.uuid4())[:8]
        self.system_prompt = self._get_system_prompt()
        
        # Initialize ChromaDB manager
        self.chromadb_manager = None
        self.use_chromadb = False
        self._init_chromadb()
        
        # Initialize Azure OpenAI client
        self.azure_client = None
        self.use_ai = False
        self._init_azure_openai()
        
        # Define function tools for OpenAI function calling
        self.function_tools = [
            {
                "type": "function",
                "function": {
                    "name": "check_nuget_package",
                    "description": "Check package information from NuGet registry including version, downloads, and metadata",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "package_name": {
                                "type": "string",
                                "description": "The name of the NuGet package to check"
                            }
                        },
                        "required": ["package_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_npm_package",
                    "description": "Check package information from npm registry including version, downloads, and metadata",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "package_name": {
                                "type": "string",
                                "description": "The name of the npm package to check"
                            }
                        },
                        "required": ["package_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "semantic_library_search",
                    "description": "Search libraries using semantic similarity to find the most relevant matches",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query for finding relevant libraries"
                            },
                            "n_results": {
                                "type": "integer",
                                "description": "Number of results to return (default: 5)"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_faqs",
                    "description": "Search FAQ database for relevant questions and answers",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query for finding relevant FAQs"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        
    def _init_chromadb(self):
        """Initialize ChromaDB manager"""
        if not CHROMADB_AVAILABLE:
            print(f"{Colors.WARNING}ChromaDB not available. Running in basic mode.{Colors.ENDC}")
            return
            
        try:
            self.chromadb_manager = get_chromadb_manager()
            self.use_chromadb = True
            print(f"{Colors.SUCCESS}✓ ChromaDB initialized with semantic search{Colors.ENDC}")
            
            # Show collection stats
            stats = self.chromadb_manager.get_collection_stats()
            print(f"{Colors.INFO}Database: {stats.get('libraries', 0)} libraries, {stats.get('faqs', 0)} FAQs{Colors.ENDC}")
            
        except Exception as e:
            print(f"{Colors.FAIL}Error initializing ChromaDB: {e}{Colors.ENDC}")
            print(f"{Colors.WARNING}Running in basic mode without semantic search.{Colors.ENDC}")
            self.use_chromadb = False
        
    def _init_azure_openai(self):
        """Initialize Azure OpenAI client"""
        if not AZURE_OPENAI_AVAILABLE:
            print(f"{Colors.WARNING}Azure OpenAI not available. Running in basic mode.{Colors.ENDC}")
            return
            
        try:
            # Get configuration from environment variables
            endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            api_key = os.getenv('AZURE_OPENAI_API_KEY')
            api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
            
            if not endpoint or not api_key:
                print(f"{Colors.WARNING}Azure OpenAI credentials not configured. Check your .env file.{Colors.ENDC}")
                print(f"{Colors.OKCYAN}Running in basic mode without AI analysis.{Colors.ENDC}")
                return
                
            self.azure_client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version
            )
            
            self.deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'GPT-4o-mini')
            self.temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
            self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
            
            self.use_ai = True
            print(f"{Colors.OKGREEN}✓ Azure OpenAI initialized successfully{Colors.ENDC}")
            
        except Exception as e:
            print(f"{Colors.FAIL}Error initializing Azure OpenAI: {e}{Colors.ENDC}")
            print(f"{Colors.WARNING}Running in basic mode without AI analysis.{Colors.ENDC}")
            self.use_ai = False
        
    def _get_system_prompt(self) -> str:
        """Returns the enhanced system prompt for the library advisory system"""
        return """You are an expert library consultant and technical advisor specializing in software library evaluation and recommendation. Your role is to provide comprehensive analysis and advisory services for software libraries across all programming languages and domains.

## Enhanced Capabilities

You now have access to a semantic search database powered by ChromaDB that contains:
- Comprehensive library information with enhanced metadata
- Frequently asked questions with intelligent matching
- User interaction history for personalized recommendations

## Your Core Capabilities

When a user provides information about a library or asks for library recommendations, you must analyze and provide detailed insights on the following dimensions:

### Semantic Search Integration
- Use semantic_library_search to find the most relevant libraries for user queries
- Use search_faqs to find relevant frequently asked questions
- Leverage vector similarity to understand user intent beyond exact keyword matches
- Provide context-aware recommendations based on semantic understanding

### Technical Analysis
- Advantages (Ưu điểm): Identify key strengths, unique features, performance benefits, community support, documentation quality, and technical superiority
- Disadvantages (Nhược điểm): Highlight limitations, known issues, compatibility problems, learning curve, maintenance concerns, and technical debt risks
- Complexity: Evaluate implementation difficulty, learning curve, configuration requirements, and integration complexity

### Economic & Legal Assessment
- Cost Analysis (Giá thành): Break down total cost of ownership including licensing fees, implementation costs, training, and maintenance
- License Terms: Detailed analysis of licensing model (MIT, Apache, GPL, commercial, etc.) from actual registry data
- Pricing Structure: Compare different pricing tiers, enterprise vs. open-source options, and cost-benefit analysis

### Risk & Security Evaluation
- Risk Assessment: Identify technical risks, vendor lock-in, discontinuation risk, compatibility issues, and migration challenges
- Security Analysis: Evaluate security track record, vulnerability history, update frequency, and security best practices
- Patching & Updates: Assess update frequency from registry data, backward compatibility, security patch timeline, and maintenance lifecycle
- **Popularity Metrics**: Use actual download statistics and community engagement metrics from package registries

### Enhanced Function Usage

1. **Semantic Library Search**: Always use semantic_library_search for finding relevant libraries. This provides better results than simple keyword matching.
2. **FAQ Integration**: Use search_faqs to find relevant questions that users commonly ask about similar topics.
3. **Registry Checks**: When analyzing .NET packages, use check_nuget_package. For JavaScript/Node.js packages, use check_npm_package.
4. **Contextual Recommendations**: Combine semantic search results with registry data for comprehensive analysis.

## Response Format

Structure your responses as follows:

# Library Analysis: [Library Name]

## Overview
[Brief description and primary use cases]

## Semantic Search Results 🧠
[Include relevant results from semantic search showing similar libraries and related FAQs]

## Registry Information 📊
- **Latest Version**: [From registry check]
- **Download Statistics**: [Weekly/total downloads from registry]
- **Maintenance Status**: [Based on version release frequency]
- **License**: [From registry metadata]
- **Repository**: [From registry metadata]

## Advantages ✅
- [List key strengths with specific examples]
- [Include popularity metrics from registry data]

## Disadvantages ❌
- [List limitations and concerns]
- [Include any version/maintenance concerns from registry data]

## Cost & Licensing 💰
- License: [License type from registry data and key terms]
- Pricing: [Cost structure and options]
- Total Cost of Ownership: [Implementation and maintenance costs]

## Risk Assessment ⚠️
- Security: [Security posture and track record]
- Maintenance: [Update frequency and long-term viability from registry data]
- Business Risk: [Vendor stability and community health based on registry metrics]

## Technical Considerations 🔧
- Complexity: [Implementation difficulty rating: Low/Medium/High]
- Flexibility: [Customization and extension capabilities]
- Integration: [Compatibility and ecosystem support]

## Similar Libraries Comparison 📊
[Use semantic search results to show similar libraries with comparison]

## Related FAQs 💡
[Include relevant FAQs from the search results]

## Recommendations 🎯
- Best for: [Ideal use cases and scenarios]
- Avoid if: [Situations where this library isn't suitable]
- Migration path: [If switching from another solution]

Always leverage the semantic search capabilities to provide more relevant and context-aware recommendations than traditional keyword-based systems."""

    def semantic_library_search(self, query: str, n_results: int = 5) -> str:
        """Search libraries using semantic similarity"""
        if not self.use_chromadb:
            return "Semantic search not available - ChromaDB not initialized"
        
        try:
            results = self.chromadb_manager.search_libraries(query, n_results)
            
            if not results:
                return f"No libraries found for query: {query}"
            
            # Format results
            formatted_results = []
            for i, result in enumerate(results, 1):
                metadata = result.metadata
                formatted_results.append({
                    "rank": i,
                    "name": metadata.get('name', 'Unknown'),
                    "category": metadata.get('category', 'Unknown'),
                    "language": metadata.get('language', 'Unknown'),
                    "description": metadata.get('description', 'No description'),
                    "similarity_score": f"{result.score:.3f}",
                    "license": metadata.get('license', 'Unknown')
                })
            
            return json.dumps(formatted_results, indent=2)
            
        except Exception as e:
            return f"Error during semantic search: {e}"
    
    def search_faqs(self, query: str) -> str:
        """Search FAQ database"""
        if not self.use_chromadb:
            return "FAQ search not available - ChromaDB not initialized"
        
        try:
            results = self.chromadb_manager.search_faqs(query, n_results=3)
            
            if not results:
                return f"No relevant FAQs found for query: {query}"
            
            # Format results
            formatted_results = []
            for i, result in enumerate(results, 1):
                metadata = result.metadata
                formatted_results.append({
                    "rank": i,
                    "question": metadata.get('question', 'Unknown question'),
                    "category": metadata.get('category', 'Unknown'),
                    "similarity_score": f"{result.score:.3f}",
                    "document": result.document
                })
            
            return json.dumps(formatted_results, indent=2)
            
        except Exception as e:
            return f"Error during FAQ search: {e}"

    def check_nuget_package(self, package_name: str) -> Dict:
        """Check package information from NuGet registry"""
        try:
            # NuGet API endpoint for package information
            url = f"https://api.nuget.org/v3-flatcontainer/{package_name.lower()}/index.json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    versions_data = response.json()
                    if isinstance(versions_data, dict) and 'versions' in versions_data:
                        latest_version = versions_data['versions'][-1] if versions_data['versions'] else "Unknown"
                        versions_count = len(versions_data['versions'])
                    else:
                        latest_version = "Unknown"
                        versions_count = 0
                except (json.JSONDecodeError, KeyError, IndexError):
                    latest_version = "Unknown"
                    versions_count = 0
                
                # Get package metadata using NuGet V3 API
                metadata_url = f"https://api.nuget.org/v3/registration5-semver1/{package_name.lower()}/index.json"
                metadata_response = requests.get(metadata_url, timeout=10)
                
                metadata = {}
                if metadata_response.status_code == 200:
                    try:
                        meta_data = metadata_response.json()
                        if isinstance(meta_data, dict) and 'items' in meta_data and meta_data['items']:
                            latest_item = meta_data['items'][-1]
                            if isinstance(latest_item, dict) and 'items' in latest_item and latest_item['items']:
                                latest_package = latest_item['items'][-1]
                                if isinstance(latest_package, dict):
                                    catalog_entry = latest_package.get('catalogEntry', {})
                                    if isinstance(catalog_entry, dict):
                                        metadata = {
                                            "description": catalog_entry.get('description', 'No description available'),
                                            "authors": catalog_entry.get('authors', 'Unknown'),
                                            "license": catalog_entry.get('licenseExpression', catalog_entry.get('licenseUrl', 'Unknown')),
                                            "project_url": catalog_entry.get('projectUrl', ''),
                                            "tags": catalog_entry.get('tags', []),
                                            "published": catalog_entry.get('published', 'Unknown')
                                        }
                    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                        pass
                
                return {
                    "status": "found",
                    "package_name": package_name,
                    "latest_version": latest_version,
                    "registry": "NuGet",
                    "metadata": metadata,
                    "versions_count": versions_count,
                    "registry_url": f"https://www.nuget.org/packages/{package_name}"
                }
            else:
                return {
                    "status": "not_found",
                    "package_name": package_name,
                    "registry": "NuGet",
                    "error": f"Package not found (HTTP {response.status_code})"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "package_name": package_name,
                "registry": "NuGet",
                "error": str(e)
            }
    
    def check_npm_package(self, package_name: str) -> Dict:
        """Check package information from npm registry"""
        try:
            # npm API endpoint for package information
            url = f"https://registry.npmjs.org/{package_name}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract key information
                latest_version = data.get('dist-tags', {}).get('latest', 'Unknown')
                description = data.get('description', 'No description available')
                
                # Get version information
                versions = data.get('versions', {})
                latest_version_info = versions.get(latest_version, {})
                
                # Get download statistics (weekly downloads)
                downloads_url = f"https://api.npmjs.org/downloads/point/last-week/{package_name}"
                downloads_response = requests.get(downloads_url, timeout=5)
                weekly_downloads = "Unknown"
                if downloads_response.status_code == 200:
                    downloads_data = downloads_response.json()
                    weekly_downloads = downloads_data.get('downloads', 'Unknown')
                
                metadata = {
                    "description": description,
                    "author": data.get('author', {}).get('name', 'Unknown') if isinstance(data.get('author'), dict) else str(data.get('author', 'Unknown')),
                    "license": latest_version_info.get('license', data.get('license', 'Unknown')),
                    "homepage": data.get('homepage', ''),
                    "repository": data.get('repository', {}).get('url', '') if isinstance(data.get('repository'), dict) else str(data.get('repository', '')),
                    "keywords": data.get('keywords', []),
                    "weekly_downloads": weekly_downloads,
                    "maintainers": len(data.get('maintainers', [])),
                    "created": data.get('time', {}).get('created', 'Unknown'),
                    "modified": data.get('time', {}).get('modified', 'Unknown')
                }
                
                return {
                    "status": "found",
                    "package_name": package_name,
                    "latest_version": latest_version,
                    "registry": "npm",
                    "metadata": metadata,
                    "versions_count": len(versions),
                    "registry_url": f"https://www.npmjs.com/package/{package_name}"
                }
            else:
                return {
                    "status": "not_found",
                    "package_name": package_name,
                    "registry": "npm",
                    "error": f"Package not found (HTTP {response.status_code})"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "package_name": package_name,
                "registry": "npm",
                "error": str(e)
            }
    
    def _execute_function_call(self, function_name: str, arguments: Dict) -> str:
        """Execute function calls from OpenAI"""
        try:
            if function_name == "check_nuget_package":
                package_name = arguments.get("package_name")
                result = self.check_nuget_package(package_name)
                return json.dumps(result, indent=2)
            elif function_name == "check_npm_package":
                package_name = arguments.get("package_name")
                result = self.check_npm_package(package_name)
                return json.dumps(result, indent=2)
            elif function_name == "semantic_library_search":
                query = arguments.get("query")
                n_results = arguments.get("n_results", 5)
                result = self.semantic_library_search(query, n_results)
                return result
            elif function_name == "search_faqs":
                query = arguments.get("query")
                result = self.search_faqs(query)
                return result
            else:
                return f"Unknown function: {function_name}"
        except Exception as e:
            return f"Error executing function {function_name}: {str(e)}"

    def _call_azure_openai(self, user_query: str, context: str = "") -> Optional[str]:
        """Call Azure OpenAI for intelligent analysis with enhanced function calling support"""
        if not self.use_ai or not self.azure_client:
            return None
            
        try:
            # Prepare the messages for the API call
            messages = [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user", 
                    "content": f"Context: {context}\n\nUser Query: {user_query}"
                }
            ]
            
            # Add recent conversation history for context
            for entry in self.conversation_history[-4:]:  # Last 4 exchanges
                if entry['type'] == 'user':
                    messages.append({
                        "role": "user",
                        "content": entry['user_input']
                    })
                elif entry['type'] == 'assistant' and 'response' in entry:
                    # Only add text responses, not control responses
                    if not entry['response'].startswith('exit'):
                        messages.append({
                            "role": "assistant", 
                            "content": entry['response'][:500]  # Truncate long responses
                        })
            
            # Initial API call with enhanced function tools
            response = self.azure_client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                tools=self.function_tools,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            # If the model wants to call functions
            if tool_calls:
                # Add the assistant's response to messages
                messages.append(response_message)
                
                # Process each function call
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Execute the function
                    function_response = self._execute_function_call(function_name, function_args)
                    
                    # Add function response to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": function_response
                    })
                
                # Get the final response from the model
                final_response = self.azure_client.chat.completions.create(
                    model=self.deployment_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                
                return final_response.choices[0].message.content
            else:
                # No function calls, return the regular response
                return response_message.content
            
        except Exception as e:
            print(f"{Colors.FAIL}Error calling Azure OpenAI: {e}{Colors.ENDC}")
            return None

    def display_welcome(self):
        """Display enhanced welcome message with ChromaDB features"""
        width = ModernFormatter.get_terminal_width()
        
        # Main header with enhanced design
        print(f"\n{Colors.HEADER}{Colors.BOLD}")
        print("┌" + "─" * (width - 2) + "┐")
        print(f"│{' ' * ((width - 38) // 2)}{Icons.LIBRARY} Enhanced Library Advisory System {Icons.SEMANTIC}{' ' * ((width - 38) // 2)}│")
        print("└" + "─" * (width - 2) + "┘")
        print(f"{Colors.RESET}\n")
        
        # System Status Card
        features = []
        
        # AI Status
        ai_status = "ENABLED" if self.use_ai else "DISABLED"
        ai_icon = "🤖" if self.use_ai else "🔧"
        ai_color = Colors.SUCCESS if self.use_ai else Colors.WARNING
        features.append(f"{ai_icon} AI Analysis: {ai_status}")
        
        # ChromaDB Status
        db_status = "ENABLED" if self.use_chromadb else "DISABLED"
        db_icon = Icons.DATABASE if self.use_chromadb else "📁"
        db_color = Colors.SUCCESS if self.use_chromadb else Colors.WARNING
        features.append(f"{db_icon} Semantic Search: {db_status}")
        
        if self.use_chromadb:
            stats = self.chromadb_manager.get_collection_stats()
            features.append(f"{Icons.LIBRARY} Database: {stats.get('libraries', 0)} libraries, {stats.get('faqs', 0)} FAQs")
        
        status_text = "\n".join(features)
        
        print(ModernFormatter.create_card(
            "System Status",
            status_text,
            Icons.INFO,
            Colors.PRIMARY
        ))
        
        # Enhanced Capabilities Section
        capabilities = [
            f"{Icons.SEMANTIC} Semantic library search with vector similarity",
            f"{Icons.ANALYSIS} Intelligent FAQ matching and recommendations", 
            f"{Icons.GEAR} Technical evaluation with enhanced metadata",
            f"{Icons.MONEY} Cost and licensing analysis",
            f"{Icons.SHIELD} Risk assessment and security evaluation",
            f"{Icons.COMPARE} Advanced comparison with similarity scoring"
        ]
        
        if self.use_ai:
            capabilities.append(f"{Icons.LIGHTBULB} AI-powered intelligent insights with function calling")
        
        capabilities_text = "\n".join(capabilities)
        print(ModernFormatter.create_card(
            "Enhanced Capabilities",
            capabilities_text,
            Icons.ROCKET,
            Colors.PRIMARY
        ))
        
        # Commands Section
        commands = [
            f"{Colors.ACCENT}help{Colors.RESET} - Detailed instructions and examples",
            f"{Colors.ACCENT}list{Colors.RESET} - Browse available libraries with semantic search",
            f"{Colors.ACCENT}analyze <library>{Colors.RESET} - Enhanced library analysis with similarity",
            f"{Colors.ACCENT}compare <lib1> vs <lib2>{Colors.RESET} - Semantic comparison analysis",
            f"{Colors.ACCENT}recommend <category>{Colors.RESET} - Get intelligent recommendations",
            f"{Colors.ACCENT}search <query>{Colors.RESET} - Semantic search across libraries and FAQs"
        ]
        
        if self.use_ai:
            commands.append(f"{Colors.ACCENT}ai <question>{Colors.RESET} - AI-powered analysis with enhanced functions")
        
        commands.extend([
            f"{Colors.ACCENT}save{Colors.RESET} - Export conversation to markdown",
            f"{Colors.ACCENT}stats{Colors.RESET} - Show database statistics",
            f"{Colors.ACCENT}exit{Colors.RESET} or {Colors.ACCENT}quit{Colors.RESET} - Exit application"
        ])
        
        commands_text = "\n".join(commands)
        print(ModernFormatter.create_card(
            "Available Commands",
            commands_text,
            Icons.GEAR,
            Colors.INFO
        ))
        
        # Quick start tip
        print(f"{Colors.MUTED}{Colors.ITALIC}")
        print(f"💡 Try semantic search: 'search fast javascript framework' or 'analyze React'")
        print(f"{Colors.RESET}\n")

    def display_help(self):
        """Display enhanced help information"""
        ai_help = ""
        if self.use_ai:
            ai_help = f"""
{Colors.OKGREEN}7. AI-Powered Analysis with Enhanced Functions:{Colors.ENDC}
   • "ai What are the security considerations for React?"
   • "ai Compare Django vs FastAPI for microservices" 
   • "ai Best practices for choosing a frontend framework"
   • AI automatically uses semantic search and registry data
"""

        semantic_help = ""
        if self.use_chromadb:
            semantic_help = f"""
{Colors.OKGREEN}6. Semantic Search Capabilities:{Colors.ENDC}
   • "search modern javascript framework"
   • "search python web framework for beginners"
   • "search database orm with good performance"
   • Advanced similarity matching beyond keywords
"""

        help_text = f"""
{Colors.HEADER}{Colors.BOLD}📚 Enhanced Library Advisory System - Detailed Help{Colors.ENDC}

{Colors.OKCYAN}Example Queries:{Colors.ENDC}

{Colors.OKGREEN}1. Enhanced Library Analysis:{Colors.ENDC}
   • "analyze React" - Get comprehensive analysis with similarity data
   • "tell me about Django" - Enhanced analysis with semantic context
   • "evaluate Vue.js for enterprise use" - Detailed evaluation

{Colors.OKGREEN}2. Semantic Library Comparison:{Colors.ENDC}
   • "compare React vs Vue.js" - Enhanced comparison with similarity scores
   • "React vs Angular for large applications" - Context-aware comparison
   • "Django vs Flask for API development" - Semantic understanding

{Colors.OKGREEN}3. Intelligent Recommendations:{Colors.ENDC}
   • "recommend JavaScript frameworks" - Semantic search results
   • "best Python web frameworks" - Enhanced recommendations
   • "suggest testing libraries for Node.js" - Context-aware suggestions
   • "find alternatives to jQuery" - Similarity-based alternatives

{Colors.OKGREEN}4. Natural Language Queries:{Colors.ENDC}
   • "I need a lightweight Python web framework" - Natural language understanding
   • "What's the best database ORM for Python?" - Intelligent matching
   • "Recommend UI libraries with good TypeScript support" - Enhanced search

{Colors.OKGREEN}5. Context-Specific Questions:{Colors.ENDC}
   • "Best framework for a startup with limited budget" - Contextual analysis
   • "Enterprise-grade libraries with commercial support" - Targeted search
   • "Open source alternatives to commercial solutions" - Alternative finding
{semantic_help}{ai_help}
{Colors.WARNING}Enhanced Features:{Colors.ENDC}
• Semantic search with vector similarity
• Intelligent FAQ matching and recommendations
• Enhanced metadata and similarity scoring
• Context-aware natural language understanding
• Advanced comparison with semantic analysis
• Comprehensive technical analysis with ChromaDB data
• Save conversations to markdown files
{f"• AI-enhanced insights with function calling{Colors.ENDC}" if self.use_ai else ""}

{Colors.FAIL}Note:{Colors.ENDC} This system provides analysis based on semantic understanding{" and AI insights" if self.use_ai else ""}. 
Always verify current information and test libraries in your specific environment.
"""
        print(help_text)

    def show_stats(self):
        """Display database statistics"""
        if not self.use_chromadb:
            print(f"{Colors.WARNING}ChromaDB not available. No statistics to display.{Colors.ENDC}")
            return
        
        try:
            stats = self.chromadb_manager.get_collection_stats()
            
            stats_content = f"""
{Icons.LIBRARY} Libraries Collection: {Colors.ACCENT}{stats.get('libraries', 0)}{Colors.RESET}
{Icons.INFO} FAQs Collection: {Colors.ACCENT}{stats.get('faqs', 0)}{Colors.RESET}
{Icons.CHART} User Queries: {Colors.ACCENT}{stats.get('user_queries', 0)}{Colors.RESET}

{Icons.DATABASE} Database Type: {Colors.ACCENT}ChromaDB with Persistence{Colors.RESET}
{Icons.SEMANTIC} Embedding Model: {Colors.ACCENT}all-MiniLM-L6-v2{Colors.RESET}
{Icons.GEAR} Session ID: {Colors.ACCENT}{self.session_id}{Colors.RESET}
            """.strip()
            
            print(ModernFormatter.create_card(
                "Database Statistics",
                stats_content,
                Icons.CHART,
                Colors.INFO
            ))
            
        except Exception as e:
            print(f"{Colors.FAIL}Error retrieving statistics: {e}{Colors.ENDC}")

    def semantic_search_command(self, query: str) -> str:
        """Handle semantic search command"""
        if not self.use_chromadb:
            return f"{Colors.WARNING}Semantic search not available. ChromaDB not initialized.{Colors.ENDC}"
        
        try:
            # Search libraries
            library_results = self.chromadb_manager.search_libraries(query, n_results=5)
            
            # Search FAQs
            faq_results = self.chromadb_manager.search_faqs(query, n_results=3)
            
            # Format results
            result_content = f"""
{Icons.SEMANTIC} Query: "{Colors.ACCENT}{query}{Colors.RESET}"

{Icons.LIBRARY} {Colors.BOLD}Library Results:{Colors.RESET}
            """.strip()
            
            if library_results:
                for i, result in enumerate(library_results, 1):
                    metadata = result.metadata
                    result_content += f"""
{i}. {Colors.BOLD}{metadata.get('name', 'Unknown')}{Colors.RESET} ({Colors.ACCENT}{result.score:.3f}{Colors.RESET})
   {Colors.DIM}{metadata.get('category', 'Unknown')} | {metadata.get('language', 'Unknown')}{Colors.RESET}
   {metadata.get('description', 'No description')[:80]}...
"""
            else:
                result_content += f"\n   {Colors.MUTED}No relevant libraries found{Colors.RESET}"
            
            result_content += f"\n\n{Icons.INFO} {Colors.BOLD}Related FAQs:{Colors.RESET}"
            
            if faq_results:
                for i, result in enumerate(faq_results, 1):
                    metadata = result.metadata
                    question = metadata.get('question', 'Unknown question')
                    result_content += f"""
{i}. {Colors.ITALIC}{question[:60]}...{Colors.RESET} ({Colors.ACCENT}{result.score:.3f}{Colors.RESET})
   {Colors.DIM}Category: {metadata.get('category', 'Unknown')}{Colors.RESET}
"""
            else:
                result_content += f"\n   {Colors.MUTED}No relevant FAQs found{Colors.RESET}"
            
            return ModernFormatter.create_card(
                "Semantic Search Results",
                result_content,
                Icons.SEMANTIC,
                Colors.PRIMARY
            )
            
        except Exception as e:
            return f"{Colors.FAIL}Semantic search failed: {e}{Colors.ENDC}"

    def analyze_library_enhanced(self, library_name: str) -> str:
        """Enhanced library analysis using ChromaDB semantic search"""
        if not self.use_chromadb:
            return f"{Colors.WARNING}Enhanced analysis not available. Using basic mode.{Colors.ENDC}"
        
        try:
            # Search for the specific library
            results = self.chromadb_manager.search_libraries(library_name, n_results=1)
            
            if not results:
                return f"{Colors.WARNING}Library '{library_name}' not found in database. Try semantic search: 'search {library_name}'{Colors.ENDC}"
            
            library_result = results[0]
            metadata = library_result.metadata
            
            # Find similar libraries
            similar_results = self.chromadb_manager.find_similar_libraries(metadata.get('name', library_name), n_results=3)
            
            # Search for related FAQs
            faq_results = self.chromadb_manager.search_faqs(f"{library_name} framework library", n_results=2)
            
            # Create enhanced analysis
            analysis_content = f"""
{Icons.ANALYSIS} {Colors.BOLD}Enhanced Analysis: {metadata.get('name', library_name)}{Colors.RESET}

{Colors.PRIMARY}{Colors.BOLD}Overview:{Colors.RESET}
{metadata.get('description', 'No description available')}

{Icons.GEAR} Language: {Colors.ACCENT}{metadata.get('language', 'Unknown')}{Colors.RESET}
{Icons.LIBRARY} Category: {Colors.ACCENT}{metadata.get('category', 'Unknown')}{Colors.RESET}
{Icons.LICENSE} License: {Colors.ACCENT}{metadata.get('license', 'Unknown')}{Colors.RESET}
{Icons.STAR} Popularity: {Colors.ACCENT}{metadata.get('popularity', 'Unknown')}{Colors.RESET}

{Colors.SUCCESS}{Colors.BOLD}Similarity Score:{Colors.RESET} {Colors.ACCENT}{library_result.score:.3f}{Colors.RESET}

{Colors.PRIMARY}{Colors.BOLD}Similar Libraries:{Colors.RESET}
            """.strip()
            
            if similar_results:
                for i, similar in enumerate(similar_results, 1):
                    sim_metadata = similar.metadata
                    analysis_content += f"""
{i}. {Colors.BOLD}{sim_metadata.get('name', 'Unknown')}{Colors.RESET} ({Colors.ACCENT}{similar.score:.3f}{Colors.RESET})
   {Colors.DIM}{sim_metadata.get('description', 'No description')[:60]}...{Colors.RESET}
"""
            else:
                analysis_content += f"\n   {Colors.MUTED}No similar libraries found{Colors.RESET}"
            
            if faq_results:
                analysis_content += f"\n\n{Colors.INFO}{Colors.BOLD}Related FAQs:{Colors.RESET}"
                for i, faq in enumerate(faq_results, 1):
                    faq_metadata = faq.metadata
                    question = faq_metadata.get('question', 'Unknown question')
                    analysis_content += f"""
{i}. {Colors.ITALIC}{question}{Colors.RESET} ({Colors.ACCENT}{faq.score:.3f}{Colors.RESET})
"""
            
            # Store user query for learning
            self.chromadb_manager.store_user_query(
                query=f"analyze {library_name}",
                response=f"Enhanced analysis provided for {metadata.get('name', library_name)}",
                session_id=self.session_id,
                user_intent="library_analysis"
            )
            
            # Enhance with AI if available
            if self.use_ai:
                ai_response = self._call_azure_openai(
                    f"Provide detailed analysis for {library_name}",
                    f"Library data: {json.dumps(metadata, indent=2)}"
                )
                if ai_response:
                    analysis_content += f"\n\n{Colors.HEADER}🤖 AI-Enhanced Analysis:{Colors.RESET}\n{ai_response}"
            
            return ModernFormatter.create_card(
                f"Library Analysis: {metadata.get('name', library_name)}",
                analysis_content,
                Icons.ANALYSIS,
                Colors.PRIMARY
            )
            
        except Exception as e:
            return f"{Colors.FAIL}Enhanced analysis failed: {e}{Colors.ENDC}"

    def process_input(self, user_input: str) -> str:
        """Process user input with enhanced ChromaDB capabilities"""
        original_input = user_input.strip()
        user_input = user_input.strip().lower()
        
        # Handle exit commands
        if user_input in ['exit', 'quit', 'bye', 'goodbye']:
            return "exit"
        
        # Handle help command
        if user_input in ['help', '?', 'help me']:
            self.display_help()
            return ""
        
        # Handle stats command
        if user_input in ['stats', 'statistics', 'info']:
            self.show_stats()
            return ""
        
        # Handle semantic search command
        if user_input.startswith('search '):
            query = original_input[7:].strip()
            return self.semantic_search_command(query)
        
        # Handle enhanced analyze command
        if user_input.startswith('analyze '):
            library = original_input[8:].strip()
            return self.analyze_library_enhanced(library)
        
        # Handle save command
        if user_input in ['save', 'save conversation', 'export', 'save to file']:
            if not self.conversation_history:
                return f"{Colors.WARNING}No conversation to save yet. Start by asking questions about libraries!{Colors.ENDC}"
            
            print(f"{Colors.OKCYAN}Saving conversation to markdown file...{Colors.ENDC}")
            filepath = self.save_conversation_to_markdown()
            if filepath:
                return f"{Colors.OKGREEN}✓ Conversation saved successfully to: {filepath}{Colors.ENDC}\n{Colors.OKCYAN}You can open this file in any markdown viewer or text editor.{Colors.ENDC}"
            else:
                return f"{Colors.FAIL}❌ Failed to save conversation. Check error messages above.{Colors.ENDC}"
        
        # Handle AI command with enhanced functions
        if user_input.startswith('ai ') and self.use_ai:
            query = original_input[3:].strip()
            response = self._call_azure_openai(query)
            if response:
                # Store the interaction
                if self.use_chromadb:
                    self.chromadb_manager.store_user_query(
                        query=query,
                        response=response,
                        session_id=self.session_id,
                        user_intent="ai_query"
                    )
                return f"{Colors.HEADER}🤖 AI Response:{Colors.ENDC}\n{response}"
            else:
                return f"{Colors.FAIL}Sorry, I couldn't process your AI request at the moment.{Colors.ENDC}"
        
        # If AI is available, try to handle any unmatched query with AI (enhanced with functions)
        if self.use_ai and len(original_input.strip()) > 3:
            ai_response = self._call_azure_openai(original_input)
            if ai_response:
                # Store the interaction
                if self.use_chromadb:
                    self.chromadb_manager.store_user_query(
                        query=original_input,
                        response=ai_response,
                        session_id=self.session_id,
                        user_intent="general_query"
                    )
                return f"{Colors.HEADER}🤖 AI Response:{Colors.ENDC}\n{ai_response}"
        
        # Try semantic search for unmatched queries
        if self.use_chromadb and len(original_input.strip()) > 3:
            return self.semantic_search_command(original_input)
        
        # Default response for unrecognized input
        ai_tip = f"• ai <your question> (for AI-powered analysis)\n" if self.use_ai else ""
        search_tip = f"• search <query> (for semantic search)\n" if self.use_chromadb else ""
        
        return f"""
{Colors.WARNING}I'm not sure how to help with that specific request.{Colors.ENDC}

{Colors.OKCYAN}Try these enhanced commands:{Colors.ENDC}
• analyze <library_name> (enhanced with semantic data)
• compare <lib1> vs <lib2> (semantic comparison)
• recommend <category> (intelligent recommendations)
{search_tip}• stats (show database statistics)
• help (for detailed instructions)
• save (to save conversation to markdown)
{ai_tip}
{Colors.OKGREEN}Or ask me about specific libraries like:{Colors.ENDC}
• "What is React?"
• "Tell me about Django"
• "search modern javascript framework"
• "Recommend Python web frameworks"
"""

    def save_conversation_to_markdown(self, filename: Optional[str] = None) -> str:
        """Save the current conversation to a markdown file with enhanced metadata"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"library_analysis_enhanced_{timestamp}.md"
        
        try:
            # Ensure reports directory exists
            reports_dir = "reports"
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)
                print(f"{Colors.OKCYAN}Created reports directory: {reports_dir}{Colors.ENDC}")
            
            filepath = os.path.join(reports_dir, filename)
            print(f"{Colors.OKCYAN}Saving to: {filepath}{Colors.ENDC}")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write enhanced header
                f.write("# Enhanced Library Advisory System - Analysis Report\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"AI Enhanced: {'Yes' if self.use_ai else 'No'}\n")
                f.write(f"Semantic Search: {'Yes' if self.use_chromadb else 'No'}\n")
                f.write(f"Session ID: {self.session_id}\n\n")
                
                if self.use_chromadb:
                    stats = self.chromadb_manager.get_collection_stats()
                    f.write(f"Database Stats: {stats.get('libraries', 0)} libraries, {stats.get('faqs', 0)} FAQs\n\n")
                
                f.write("---\n\n")
                
                # Check if we have conversation history
                if not self.conversation_history:
                    f.write("## No Conversation History\n\n")
                    f.write("This session did not contain any queries or responses.\n\n")
                    f.write("---\n\n")
                else:
                    # Write conversation history
                    query_count = 0
                    
                    for i, entry in enumerate(self.conversation_history):
                        if entry['type'] == 'user':
                            query_count += 1
                            user_input = entry['user_input']
                            f.write(f"## Query {query_count}: {user_input}\n\n")
                            f.write(f"Timestamp: {entry['timestamp']}\n\n")
                            
                            # Look for the corresponding response
                            if i + 1 < len(self.conversation_history):
                                next_entry = self.conversation_history[i + 1]
                                if next_entry['type'] == 'assistant' and 'response' in next_entry:
                                    response = next_entry['response']
                                    # Clean up color codes for markdown
                                    clean_response = self._clean_response_for_markdown(response)
                                    f.write(f"{clean_response}\n\n")
                                    f.write("---\n\n")
                
                # Add enhanced summary section
                f.write("## Session Summary\n\n")
                f.write(f"- Total Queries: {len([e for e in self.conversation_history if e['type'] == 'user'])}\n")
                f.write(f"- Enhanced Features Used: {'Semantic Search, ' if self.use_chromadb else ''}{'AI Analysis' if self.use_ai else 'Basic Mode'}\n")
                f.write(f"- Session ID: {self.session_id}\n")
                f.write(f"- Session Duration: {self._calculate_session_duration()}\n\n")
                
                # Add footer
                f.write("---\n\n")
                f.write("*Generated by Enhanced Library Advisory System with ChromaDB*\n")
                f.write("*Featuring semantic search and intelligent recommendations*\n")
            
            print(f"{Colors.OKGREEN}✓ File written successfully: {filepath}{Colors.ENDC}")
            return filepath
            
        except Exception as e:
            print(f"{Colors.FAIL}Error saving to markdown: {e}{Colors.ENDC}")
            return None

    def _clean_response_for_markdown(self, response: str) -> str:
        """Remove color codes and format response for markdown"""
        # Remove ANSI color codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        cleaned = ansi_escape.sub('', response)
        
        # Fix markdown formatting
        cleaned = cleaned.replace('# Library Analysis:', '### Library Analysis:')
        cleaned = cleaned.replace('## Overview', '#### Overview')
        cleaned = cleaned.replace('## Advantages', '#### Advantages')
        cleaned = cleaned.replace('## Disadvantages', '#### Disadvantages')
        cleaned = cleaned.replace('## Cost & Licensing', '#### Cost & Licensing')
        cleaned = cleaned.replace('## Risk Assessment', '#### Risk Assessment')
        cleaned = cleaned.replace('## Technical Considerations', '#### Technical Considerations')
        cleaned = cleaned.replace('## Similar Libraries Comparison', '#### Similar Libraries Comparison')
        cleaned = cleaned.replace('## Recommendations', '#### Recommendations')
        cleaned = cleaned.replace('🤖 AI Response:', '#### 🤖 AI-Enhanced Analysis')
        cleaned = cleaned.replace('🤖 AI-Enhanced Analysis:', '#### 🤖 AI-Enhanced Analysis')
        cleaned = cleaned.replace('🤖 AI-Powered Detailed Comparison:', '#### 🤖 AI-Powered Detailed Comparison')
        
        return cleaned.strip()

    def _calculate_session_duration(self) -> str:
        """Calculate session duration from conversation history"""
        if len(self.conversation_history) < 2:
            return "Less than 1 minute"
        
        try:
            start_time = datetime.fromisoformat(self.conversation_history[0]['timestamp'])
            end_time = datetime.fromisoformat(self.conversation_history[-1]['timestamp'])
            duration = end_time - start_time
            
            minutes = duration.total_seconds() / 60
            if minutes < 1:
                return "Less than 1 minute"
            elif minutes < 60:
                return f"{int(minutes)} minutes"
            else:
                hours = int(minutes / 60)
                remaining_minutes = int(minutes % 60)
                return f"{hours}h {remaining_minutes}m"
        except:
            return "Unknown"

    def run(self):
        """Main chat loop with enhanced capabilities"""
        self.display_welcome()
        
        try:
            while True:
                print(f"\n{Colors.OKBLUE}🤖 Enhanced Advisor:{Colors.ENDC} ", end="")
                user_input = input().strip()
                
                if not user_input:
                    continue
                
                # Add to conversation history
                self.conversation_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'user_input': user_input,
                    'type': 'user'
                })
                
                response = self.process_input(user_input)
                
                if response == "exit":
                    # Offer to save conversation before exit
                    if self.conversation_history:
                        save_prompt = input(f"\n{Colors.OKCYAN}Would you like to save this conversation to a markdown file? (y/n): {Colors.ENDC}")
                        if save_prompt.lower().strip() in ['y', 'yes', 'save']:
                            filepath = self.save_conversation_to_markdown()
                            if filepath:
                                print(f"{Colors.OKGREEN}✓ Conversation saved to: {filepath}{Colors.ENDC}")
                    
                    print(f"\n{Colors.OKGREEN}Thank you for using Enhanced Library Advisory System! 👋{Colors.ENDC}")
                    print(f"{Colors.OKCYAN}Happy coding with semantic intelligence!{Colors.ENDC}\n")
                    break
                
                if response:
                    print(response)
                    
                    # Add response to history
                    self.conversation_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'response': response,
                        'type': 'assistant'
                    })
        
        except KeyboardInterrupt:
            # Offer to save on interrupt
            if self.conversation_history:
                try:
                    save_prompt = input(f"\n\n{Colors.OKCYAN}Session interrupted. Save conversation? (y/n): {Colors.ENDC}")
                    if save_prompt.lower().strip() in ['y', 'yes', 'save']:
                        filepath = self.save_conversation_to_markdown()
                        if filepath:
                            print(f"{Colors.OKGREEN}✓ Conversation saved to: {filepath}{Colors.ENDC}")
                except:
                    pass  # Handle any issues with the save prompt
            
            print(f"\n{Colors.WARNING}Session interrupted by user.{Colors.ENDC}")
            print(f"{Colors.OKGREEN}Thank you for using Enhanced Library Advisory System! 👋{Colors.ENDC}\n")
        
        except Exception as e:
            print(f"\n{Colors.FAIL}An error occurred: {e}{Colors.ENDC}")
            print(f"{Colors.WARNING}Please restart the application.{Colors.ENDC}\n")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Enhanced Library Advisory System - ChromaDB Terminal Chatbot')
    parser.add_argument('--version', action='version', version='Enhanced Library Advisory System 2.0.0')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    if args.debug:
        print("Debug mode enabled")
    
    # Initialize and run the enhanced chatbot
    bot = EnhancedLibraryAdvisoryBot()
    bot.run()

if __name__ == "__main__":
    main()