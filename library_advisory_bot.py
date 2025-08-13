#!/usr/bin/env python3
"""
Library Advisory System Terminal Chatbot
A comprehensive library evaluation and recommendation system with Azure OpenAI integration
"""

import os
import sys
import json
import re
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import argparse
import html

# Import required packages for Azure OpenAI
try:
    from openai import AzureOpenAI
    from dotenv import load_dotenv
    AZURE_OPENAI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Azure OpenAI dependencies not installed. Run: pip install -r requirements.txt")
    print(f"Error: {e}")
    # Provide a no-op fallback for load_dotenv so the app can run without python-dotenv
    def load_dotenv():
        return None
    AZURE_OPENAI_AVAILABLE = False

# Consolidated styling system
class Style:
    """Unified styling system for terminal output"""
    
    # Colors
    PRIMARY, SUCCESS, WARNING, ERROR, INFO = '\033[38;5;33m', '\033[38;5;46m', '\033[38;5;220m', '\033[38;5;196m', '\033[38;5;117m'
    HEADER, ACCENT, MUTED = '\033[38;5;99m', '\033[38;5;208m', '\033[38;5;244m'
    BOLD, RESET = '\033[1m', '\033[0m'
    
    # Icons
    LIBRARY, ANALYSIS, SUCCESS_ICON, WARNING_ICON, ERROR_ICON = "📚", "🔍", "✅", "⚠️", "❌"
    INFO_ICON, STAR, ARROW, CHECK, CROSS = "ℹ️", "⭐", "→", "✓", "✗"
    GEAR, SHIELD, MONEY, CHART, TARGET, LIGHTBULB, COMPARE = "⚙️", "🛡️", "💰", "📊", "🎯", "💡", "⚖️"
    
    @staticmethod
    def colorize(text: str, color: str) -> str:
        """Apply color to text"""
        return f"{color}{text}{Style.RESET}"
    
    @staticmethod
    def badge(text: str, color: str = PRIMARY) -> str:
        """Create a colored badge"""
        return f"{color}{Style.BOLD}[{text}]{Style.RESET}"
    
    @staticmethod
    def card(title: str, content: str, icon: str = "", color: str = PRIMARY) -> str:
        """Create a simple card layout"""
        width = min(80, os.get_terminal_size().columns - 4) if hasattr(os, 'get_terminal_size') else 76
        header = f"{color}{Style.BOLD}{icon} {title}{Style.RESET}"
        separator = f"{color}{'─' * width}{Style.RESET}"
        formatted_content = "\n".join(f"  {line}" for line in content.split('\n') if line.strip())
        return f"{header}\n{separator}\n{formatted_content}\n"
    
    @staticmethod
    def strip_ansi(text: str) -> str:
        """Remove ANSI escape sequences"""
        return re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])').sub('', text)

@dataclass
class LibraryData:
    """Optimized library data structure"""
    name: str
    category: str
    language: str
    description: str
    license: str
    popularity: str
    alternatives: List[str]
    
    # Analysis data - consolidated into dictionaries
    advantages: Dict[str, str] = None
    disadvantages: Dict[str, str] = None
    technical: Dict[str, any] = None
    
    def __post_init__(self):
        if self.advantages is None:
            self.advantages = self._get_advantages()
        if self.disadvantages is None:
            self.disadvantages = self._get_disadvantages()
        if self.technical is None:
            self.technical = self._get_technical_data()
    
    def _get_advantages(self) -> Dict[str, str]:
        """Get advantages based on library name"""
        advantages_db = {
            "React": {
                "Community": "Massive ecosystem with 200M+ weekly downloads",
                "Performance": "Virtual DOM enables efficient rendering",
                "Architecture": "Component-based design promotes reusability",
                "Enterprise": "Backed by Meta with guaranteed support"
            },
            "Vue.js": {
                "Learning": "Gentle progression from beginner to advanced",
                "Adoption": "Progressive framework - integrate incrementally",
                "Performance": "Efficient reactivity system",
                "Bundle Size": "Smaller footprint compared to competitors"
            },
            "Django": {
                "Batteries": "ORM, admin panel, auth out of the box",
                "Security": "Built-in CSRF, XSS, SQL injection protection",
                "Development": "DRY principle enables fast prototyping",
                "Scale": "Powers Instagram, Pinterest, other large platforms"
            },
            "Flask": {
                "Minimalism": "Lightweight core with modular extensions",
                "Flexibility": "Full control over application architecture",
                "Learning": "Simple to understand and quick to prototype",
                "Microservices": "Perfect for distributed architectures"
            },
            "Express.js": {
                "Performance": "Fast, lightweight with minimal overhead",
                "Middleware": "Extensive middleware ecosystem",
                "APIs": "Excellent for RESTful services and GraphQL",
                "Community": "Huge Node.js ecosystem support"
            }
        }
        return advantages_db.get(self.name, {
            "Popularity": f"Established choice in {self.category}",
            "Community": f"Active {self.language} ecosystem support",
            "License": f"Open source with {self.license} license"
        })
    
    def _get_disadvantages(self) -> Dict[str, str]:
        """Get disadvantages based on library name"""
        disadvantages_db = {
            "React": {
                "Learning": "Complex concepts like hooks and state management",
                "Fragmentation": "Too many choices can cause decision paralysis",
                "Dependencies": "Requires multiple libraries for full functionality"
            },
            "Vue.js": {
                "Market": "Smaller job market compared to React",
                "Enterprise": "Less widespread in large enterprises",
                "Resources": "Fewer third-party resources and tutorials"
            },
            "Django": {
                "Overkill": "Heavy for simple applications and APIs",
                "Monolithic": "Opinionated structure limits flexibility",
                "Real-time": "Not ideal for WebSocket applications"
            },
            "Flask": {
                "Setup": "Requires many decisions and configuration",
                "Batteries": "No built-in ORM, admin, or authentication",
                "Security": "Manual security feature implementation"
            },
            "Express.js": {
                "Minimalism": "Requires extensive setup for production",
                "Security": "No built-in security features",
                "Structure": "No opinionated structure can cause inconsistency"
            }
        }
        return disadvantages_db.get(self.name, {
            "Learning": "May vary based on developer background",
            "Maintenance": "Dependent on community for updates",
            "Compatibility": "Potential integration issues"
        })
    
    def _get_technical_data(self) -> Dict[str, any]:
        """Get technical data based on library name"""
        technical_db = {
            "React": {"complexity": 4, "performance": 4, "learning": 4},
            "Vue.js": {"complexity": 2, "performance": 5, "learning": 2},
            "Django": {"complexity": 3, "performance": 4, "learning": 3},
            "Flask": {"complexity": 2, "performance": 5, "learning": 2},
            "Express.js": {"complexity": 2, "performance": 5, "learning": 3}
        }
        return technical_db.get(self.name, {"complexity": 3, "performance": 3, "learning": 3})

class LibraryAdvisoryBot:
    """Optimized main chatbot class with caching"""
    
    def __init__(self):
        load_dotenv()
        self.conversation_history = []
        self.known_libraries = self._load_library_database()
        self.system_prompt = self._get_system_prompt()
        self.azure_client = None
        self.use_ai = False
        self._init_azure_openai()
        self.function_tools = self._get_function_tools()
        # Add caching for expensive operations
        self._analysis_cache = {}
        self._registry_cache = {}
    
    def _init_azure_openai(self):
        """Initialize Azure OpenAI client"""
        if not AZURE_OPENAI_AVAILABLE:
            print(f"{Style.WARNING}Azure OpenAI not available. Running in basic mode.{Style.RESET}")
            return
            
        try:
            endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            api_key = os.getenv('AZURE_OPENAI_API_KEY')
            api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
            
            if not endpoint or not api_key:
                print(f"{Style.WARNING}Azure OpenAI credentials not configured.{Style.RESET}")
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
            print(f"{Style.SUCCESS}✓ Azure OpenAI initialized successfully{Style.RESET}")
            
        except Exception as e:
            print(f"{Style.ERROR}Error initializing Azure OpenAI: {e}{Style.RESET}")
            self.use_ai = False
    
    def _get_system_prompt(self) -> str:
        """Condensed system prompt"""
        return """You are an expert library consultant providing comprehensive analysis of software libraries.

When analyzing libraries, provide detailed insights on:
- Technical advantages/disadvantages with specific examples
- Cost analysis including licensing and implementation costs
- Risk assessment covering security, maintenance, and business risks
- Technical considerations: complexity, performance, learning curve
- Comparison with similar libraries including actual metrics
- Recommendations for specific use cases

Always use function calls to check package registries (check_nuget_package for .NET, check_npm_package for JavaScript) to get current version info, download statistics, and metadata.

Format responses with clear sections: Overview, Registry Info, Advantages, Disadvantages, Cost & Licensing, Risk Assessment, Technical Considerations, Similar Libraries Comparison, and Recommendations."""
    
    def _get_function_tools(self) -> List[Dict]:
        """Get function tools for OpenAI"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "check_nuget_package",
                    "description": "Check NuGet package information",
                    "parameters": {
                        "type": "object",
                        "properties": {"package_name": {"type": "string"}},
                        "required": ["package_name"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "check_npm_package",
                    "description": "Check npm package information",
                    "parameters": {
                        "type": "object",
                        "properties": {"package_name": {"type": "string"}},
                        "required": ["package_name"]
                    }
                }
            }
        ]
    
    def _load_library_database(self) -> Dict[str, LibraryData]:
        """Load library database with optimized structure"""
        database_file = "library_database.json"
        raw_data = {}
        
        if os.path.exists(database_file):
            try:
                with open(database_file, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                raw_data = self._get_default_data()
        else:
            raw_data = self._get_default_data()
        
        # Convert to LibraryData objects
        libraries = {}
        for key, data in raw_data.items():
            libraries[key] = LibraryData(**data)
        
        return libraries
    
    def _get_default_data(self) -> Dict:
        """Default library data"""
        return {
            "react": {
                "name": "React", "category": "Frontend Framework", "language": "JavaScript",
                "description": "A JavaScript library for building user interfaces",
                "license": "MIT", "popularity": "Very High",
                "alternatives": ["Vue.js", "Angular", "Svelte", "Solid.js"]
            },
            "vue": {
                "name": "Vue.js", "category": "Frontend Framework", "language": "JavaScript",
                "description": "Progressive JavaScript framework for building UIs",
                "license": "MIT", "popularity": "High",
                "alternatives": ["React", "Angular", "Svelte", "Alpine.js"]
            },
            "django": {
                "name": "Django", "category": "Web Framework", "language": "Python",
                "description": "High-level Python web framework",
                "license": "BSD", "popularity": "High",
                "alternatives": ["Flask", "FastAPI", "Pyramid", "Tornado"]
            },
            "flask": {
                "name": "Flask", "category": "Web Framework", "language": "Python",
                "description": "Lightweight WSGI web application framework",
                "license": "BSD", "popularity": "High",
                "alternatives": ["Django", "FastAPI", "Bottle", "CherryPy"]
            },
            "express": {
                "name": "Express.js", "category": "Web Framework", "language": "JavaScript/Node.js",
                "description": "Fast, unopinionated web framework for Node.js",
                "license": "MIT", "popularity": "Very High",
                "alternatives": ["Koa.js", "Hapi.js", "Fastify", "NestJS"]
            }
        }
    
    def _check_package_registry(self, package_name: str, registry_type: str) -> Dict:
        """Generic package registry checker with caching"""
        # Check cache first
        cache_key = f"{registry_type}:{package_name.lower()}"
        if cache_key in self._registry_cache:
            return self._registry_cache[cache_key]
        
        try:
            if registry_type == "nuget":
                url = f"https://api.nuget.org/v3-flatcontainer/{package_name.lower()}/index.json"
                meta_url = f"https://api.nuget.org/v3/registration5-semver1/{package_name.lower()}/index.json"
                pkg_url = f"https://www.nuget.org/packages/{package_name}"
            else:  # npm
                url = f"https://registry.npmjs.org/{package_name}"
                meta_url = f"https://api.npmjs.org/downloads/point/last-week/{package_name}"
                pkg_url = f"https://www.npmjs.com/package/{package_name}"
            
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return {"status": "not_found", "package_name": package_name, "registry": registry_type.title()}
            
            data = response.json()
            
            if registry_type == "nuget":
                latest_version = data.get('versions', ['Unknown'])[-1]
                versions_count = len(data.get('versions', []))
                
                # Get NuGet metadata
                meta_response = requests.get(meta_url, timeout=10)
                metadata = {}
                if meta_response.status_code == 200:
                    meta_data = meta_response.json()
                    if 'items' in meta_data and meta_data['items']:
                        catalog = meta_data['items'][-1]['items'][-1]['catalogEntry']
                        metadata = {
                            "description": catalog.get('description', 'No description'),
                            "authors": catalog.get('authors', 'Unknown'),
                            "license": catalog.get('licenseExpression', 'Unknown'),
                            "published": catalog.get('published', 'Unknown')
                        }
            else:  # npm
                latest_version = data.get('dist-tags', {}).get('latest', 'Unknown')
                versions_count = len(data.get('versions', {}))
                
                # Get npm download stats
                downloads_response = requests.get(meta_url, timeout=5)
                weekly_downloads = "Unknown"
                if downloads_response.status_code == 200:
                    weekly_downloads = downloads_response.json().get('downloads', 'Unknown')
                
                metadata = {
                    "description": data.get('description', 'No description'),
                    "author": str(data.get('author', 'Unknown')),
                    "license": data.get('license', 'Unknown'),
                    "weekly_downloads": weekly_downloads,
                    "created": data.get('time', {}).get('created', 'Unknown')
                }
            
            result = {
                "status": "found", "package_name": package_name,
                "latest_version": latest_version, "registry": registry_type.title(),
                "metadata": metadata, "versions_count": versions_count,
                "registry_url": pkg_url
            }
            
            # Cache successful results
            self._registry_cache[cache_key] = result
            return result
            
        except Exception as e:
            result = {"status": "error", "package_name": package_name, "registry": registry_type.title(), "error": str(e)}
            # Don't cache errors
            return result
    
    def check_nuget_package(self, package_name: str) -> Dict:
        """Check NuGet package information"""
        return self._check_package_registry(package_name, "nuget")
    
    def check_npm_package(self, package_name: str) -> Dict:
        """Check npm package information"""
        return self._check_package_registry(package_name, "npm")
    
    def _execute_function_call(self, function_name: str, arguments: Dict) -> str:
        """Execute function calls from OpenAI"""
        try:
            if function_name == "check_nuget_package":
                return json.dumps(self.check_nuget_package(arguments.get("package_name")), indent=2)
            elif function_name == "check_npm_package":
                return json.dumps(self.check_npm_package(arguments.get("package_name")), indent=2)
            return f"Unknown function: {function_name}"
        except Exception as e:
            return f"Error executing {function_name}: {str(e)}"
    
    def _call_azure_openai(self, user_query: str, context: str = "") -> Optional[str]:
        """Call Azure OpenAI with function calling support"""
        if not self.use_ai or not self.azure_client:
            return None
            
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Context: {context}\n\nUser Query: {user_query}"}
            ]
            
            # Add recent conversation context
            for entry in self.conversation_history[-4:]:
                if entry['type'] == 'user':
                    messages.append({"role": "user", "content": entry['user_input']})
                elif entry['type'] == 'assistant' and 'response' in entry:
                    if not entry['response'].startswith('exit'):
                        messages.append({"role": "assistant", "content": entry['response'][:500]})
            
            # Initial API call
            response = self.azure_client.chat.completions.create(
                model=self.deployment_name, messages=messages,
                temperature=self.temperature, max_tokens=self.max_tokens,
                tools=self.function_tools, tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            if tool_calls:
                messages.append(response_message)
                
                for tool_call in tool_calls:
                    function_response = self._execute_function_call(
                        tool_call.function.name,
                        json.loads(tool_call.function.arguments)
                    )
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": function_response
                    })
                
                final_response = self.azure_client.chat.completions.create(
                    model=self.deployment_name, messages=messages,
                    temperature=self.temperature, max_tokens=self.max_tokens
                )
                
                return final_response.choices[0].message.content
            else:
                return response_message.content
                
        except Exception as e:
            print(f"{Style.ERROR}Error calling Azure OpenAI: {e}{Style.RESET}")
            return None
    
    def display_welcome(self):
        """Display welcome message"""
        print(f"\n{Style.HEADER}{Style.BOLD}")
        print("┌" + "─" * 76 + "┐")
        print(f"│{' ' * 22}{Style.LIBRARY} Library Advisory System {Style.ANALYSIS}{' ' * 22}│")
        print("└" + "─" * 76 + "┘")
        print(f"{Style.RESET}\n")
        
        # Status and capabilities
        ai_status = "ENABLED (Azure OpenAI)" if self.use_ai else "DISABLED (Basic mode)"
        status_color = Style.SUCCESS if self.use_ai else Style.WARNING
        
        print(Style.card("System Status", f"🤖 AI-Enhanced Analysis: {ai_status}", Style.INFO_ICON, status_color))
        
        capabilities = [
            f"{Style.ANALYSIS} Library analysis and comparison",
            f"{Style.GEAR} Technical evaluation and recommendations",
            f"{Style.MONEY} Cost and licensing analysis",
            f"{Style.SHIELD} Risk assessment and security evaluation",
            f"{Style.COMPARE} Finding alternatives and migration paths"
        ]
        
        if self.use_ai:
            capabilities.append(f"{Style.LIGHTBULB} AI-powered intelligent insights")
        
        print(Style.card("I can help you with", "\n".join(capabilities), Style.STAR, Style.PRIMARY))
        
        # Commands
        commands = [
            f"{Style.ACCENT}analyze <library>{Style.RESET} - Detailed library analysis",
            f"{Style.ACCENT}compare <lib1> vs <lib2>{Style.RESET} - Side-by-side comparison",
            f"{Style.ACCENT}recommend <category>{Style.RESET} - Get recommendations",
            f"{Style.ACCENT}list{Style.RESET} - Browse available libraries",
            f"{Style.ACCENT}help{Style.RESET} - Detailed instructions",
            f"{Style.ACCENT}save{Style.RESET} - Export conversation to markdown",
            f"{Style.ACCENT}exit{Style.RESET} - Exit application"
        ]
        
        if self.use_ai:
            commands.insert(-2, f"{Style.ACCENT}ai <question>{Style.RESET} - AI-powered analysis")
        
        print(Style.card("Available Commands", "\n".join(commands), Style.GEAR, Style.INFO))
        
        print(f"{Style.MUTED}💡 Quick start: Try 'analyze React' or 'compare Vue.js vs Angular'{Style.RESET}\n")
    
    def analyze_library(self, library_name: str) -> str:
        """Analyze a library with optimized output"""
        library_name_lower = library_name.lower()
        
        # Find library data
        lib_data = None
        for key, data in self.known_libraries.items():
            if key == library_name_lower or data.name.lower() == library_name_lower:
                lib_data = data
                break
        
        if lib_data:
            analysis = self._generate_analysis(lib_data)
        else:
            analysis = self._generate_unknown_analysis(library_name)
        
        # Enhance with AI if available
        if self.use_ai:
            ai_response = self._call_azure_openai(f"analyze {library_name}")
            if ai_response:
                return f"{analysis}\n\n{Style.card('AI-Enhanced Analysis', ai_response, '🤖', Style.ACCENT)}"
        
        return analysis
    
    def _generate_analysis(self, lib_data: LibraryData) -> str:
        """Generate optimized analysis"""
        sections = []
        
        # Header
        sections.append(f"\n{Style.HEADER}{Style.BOLD}{Style.ANALYSIS} Library Analysis: {lib_data.name}{Style.RESET}\n")
        
        # Overview
        overview = f"{lib_data.description}\n\n{Style.GEAR} Language: {Style.colorize(lib_data.language, Style.ACCENT)}\n{Style.LIBRARY} Category: {Style.colorize(lib_data.category, Style.ACCENT)}\n{Style.SHIELD} License: {Style.colorize(lib_data.license, Style.ACCENT)}\n{Style.STAR} Popularity: {Style.colorize(lib_data.popularity, Style.ACCENT)}"
        sections.append(Style.card("Overview", overview, Style.INFO_ICON, Style.PRIMARY))
        
        # Advantages
        adv_text = "\n".join(f"{Style.CHECK} {Style.BOLD}{k}{Style.RESET}: {v}" for k, v in lib_data.advantages.items())
        sections.append(Style.card("Advantages", adv_text, Style.SUCCESS_ICON, Style.SUCCESS))
        
        # Disadvantages
        dis_text = "\n".join(f"{Style.CROSS} {Style.BOLD}{k}{Style.RESET}: {v}" for k, v in lib_data.disadvantages.items())
        sections.append(Style.card("Disadvantages", dis_text, Style.WARNING_ICON, Style.WARNING))
        
        # Technical considerations
        tech = lib_data.technical
        complexity_desc = ["Very Easy", "Easy", "Moderate", "Hard", "Very Hard"][tech['complexity']]
        perf_desc = ["Poor", "Fair", "Good", "Very Good", "Excellent"][tech['performance']]
        learn_desc = ["Very Easy", "Easy", "Moderate", "Hard", "Very Hard"][tech['learning']]
        
        tech_text = f"{Style.GEAR} Complexity: {Style.colorize(complexity_desc, Style.ACCENT)}\n{Style.CHART} Performance: {Style.colorize(perf_desc, Style.ACCENT)}\n{Style.LIGHTBULB} Learning Curve: {Style.colorize(learn_desc, Style.ACCENT)}"
        sections.append(Style.card("Technical Considerations", tech_text, Style.GEAR, Style.INFO))
        
        # Alternatives
        if lib_data.alternatives:
            alt_text = "\n".join(f"{Style.ARROW} {alt}" for alt in lib_data.alternatives[:5])
            sections.append(Style.card("Similar Libraries", alt_text, Style.COMPARE, Style.MUTED))
        
        return "\n".join(sections)
    
    def _generate_unknown_analysis(self, library_name: str) -> str:
        """Generate analysis for unknown libraries"""
        return Style.card(
            f"Analysis: {library_name}",
            f"{Style.WARNING}This library is not in our database.{Style.RESET}\n\nResearch checklist:\n{Style.CHECK} Check GitHub repository\n{Style.CHECK} Review documentation quality\n{Style.CHECK} Verify license compatibility\n{Style.CHECK} Assess security and maintenance\n{Style.CHECK} Test integration complexity",
            Style.WARNING_ICON,
            Style.WARNING
        )
    
    def compare_libraries(self, lib1: str, lib2: str) -> str:
        """Compare two libraries"""
        header = f"\n{Style.HEADER}{Style.BOLD}{Style.COMPARE} Library Comparison: {lib1} vs {lib2}{Style.RESET}\n"
        
        analysis1 = self.analyze_library(lib1)
        analysis2 = self.analyze_library(lib2)
        
        comparison = header + analysis1 + "\n" + analysis2
        
        # Add AI comparison if available
        if self.use_ai:
            ai_comparison = self._call_azure_openai(f"Compare {lib1} and {lib2} libraries in detail")
            if ai_comparison:
                comparison += "\n" + Style.card("AI-Powered Detailed Comparison", ai_comparison, "🤖", Style.ACCENT)
        
        return comparison
    
    def get_recommendations(self, category: str) -> str:
        """Get recommendations for a category"""
        category_lower = category.lower()
        matching_libs = [
            lib for lib in self.known_libraries.values()
            if category_lower in lib.category.lower()
        ]
        
        if not matching_libs:
            available = "\n".join(f"  • {cat}" for cat in set(lib.category for lib in self.known_libraries.values()))
            return Style.card(
                "Category Not Found",
                f"{Style.WARNING}No libraries found for: {category}{Style.RESET}\n\nAvailable categories:\n{available}",
                Style.WARNING_ICON,
                Style.WARNING
            )
        
        # Generate recommendations
        sections = [f"\n{Style.HEADER}{Style.BOLD}{Style.TARGET} Recommendations: {category.title()}{Style.RESET}\n"]
        
        for lib in matching_libs[:5]:
            lib_content = f"{lib.description}\n\n{Style.GEAR} Language: {Style.colorize(lib.language, Style.ACCENT)}\n{Style.STAR} Popularity: {Style.badge(lib.popularity, Style.PRIMARY)}\n{Style.SHIELD} License: {Style.badge(lib.license, Style.INFO)}\n\n{Style.ARROW} For analysis: {Style.colorize(f'analyze {lib.name}', Style.ACCENT)}"
            sections.append(Style.card(lib.name, lib_content, Style.LIBRARY, Style.PRIMARY))
        
        return "\n".join(sections)
    
    def list_known_libraries(self):
        """Display known libraries"""
        print(f"\n{Style.HEADER}{Style.BOLD}{Style.LIBRARY} Known Libraries Database{Style.RESET}\n")
        
        # Group by category
        categories = {}
        for lib in self.known_libraries.values():
            if lib.category not in categories:
                categories[lib.category] = []
            categories[lib.category].append(lib)
        
        # Display each category
        for category, libs in categories.items():
            lib_items = []
            for lib in libs:
                popularity_color = Style.SUCCESS if 'high' in lib.popularity.lower() else Style.INFO
                lib_line = f"{Style.ARROW} {Style.BOLD}{lib.name}{Style.RESET} ({Style.colorize(lib.language, Style.ACCENT)}) {Style.badge(lib.popularity, popularity_color)}"
                lib_items.append(lib_line)
                lib_items.append(f"   {Style.colorize(lib.description, Style.MUTED)}")
            
            print(Style.card(f"{category} ({len(libs)} libraries)", "\n".join(lib_items), Style.GEAR, Style.PRIMARY))
        
        # Quick actions
        actions = f"{Style.ANALYSIS} {Style.colorize('analyze <library>', Style.ACCENT)} - Detailed analysis\n{Style.COMPARE} {Style.colorize('compare <lib1> vs <lib2>', Style.ACCENT)} - Compare libraries\n{Style.TARGET} {Style.colorize('recommend <category>', Style.ACCENT)} - Get recommendations"
        print(Style.card("What's next?", actions, Style.LIGHTBULB, Style.INFO))
    
    def display_help(self):
        """Display help information"""
        ai_help = f"\n{Style.SUCCESS}AI Commands:{Style.RESET}\n• \"ai What are security considerations for React?\"\n• \"ai Compare Django vs FastAPI\"" if self.use_ai else ""
        
        help_text = f"""
{Style.HEADER}{Style.BOLD}Library Advisory System - Help{Style.RESET}

{Style.SUCCESS}Example Queries:{Style.RESET}
• "analyze React"
• "compare React vs Vue.js"  
• "recommend JavaScript frameworks"
• "tell me about Django"
{ai_help}

{Style.INFO}Features:{Style.RESET}
• Comprehensive technical analysis
• Cost and licensing evaluation
• Security and risk assessment
• Performance comparisons
• Migration guidance
• Save conversations to markdown
{f"• AI-enhanced insights" if self.use_ai else ""}
"""
        print(help_text)
    
    def save_conversation_to_markdown(self, filename: Optional[str] = None) -> str:
        """Save conversation to markdown file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"library_analysis_{timestamp}.md"
        
        try:
            reports_dir = "reports"
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)
            
            filepath = os.path.join(reports_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("# Library Advisory System - Analysis Report\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"AI Enhanced: {'Yes' if self.use_ai else 'No'}\n\n---\n\n")
                
                if not self.conversation_history:
                    f.write("## No Conversation History\n\n")
                else:
                    query_count = 0
                    for i, entry in enumerate(self.conversation_history):
                        if entry['type'] == 'user':
                            query_count += 1
                            f.write(f"## Query {query_count}: {entry['user_input']}\n\n")
                            f.write(f"Timestamp: {entry['timestamp']}\n\n")
                            
                            if i + 1 < len(self.conversation_history):
                                next_entry = self.conversation_history[i + 1]
                                if next_entry['type'] == 'assistant' and 'response' in next_entry:
                                    clean_response = Style.strip_ansi(next_entry['response'])
                                    f.write(f"{clean_response}\n\n---\n\n")
                
                f.write("## Session Summary\n\n")
                f.write(f"- Total Queries: {len([e for e in self.conversation_history if e['type'] == 'user'])}\n")
                f.write(f"- Libraries in Database: {len(self.known_libraries)}\n")
                f.write(f"- AI Features Used: {'Yes' if self.use_ai else 'No'}\n\n")
                f.write("---\n\n*Generated by Library Advisory System*\n")
            
            print(f"{Style.SUCCESS}✓ Conversation saved to: {filepath}{Style.RESET}")
            return filepath
            
        except Exception as e:
            print(f"{Style.ERROR}Error saving conversation: {e}{Style.RESET}")
            return None
    
    def process_input(self, user_input: str) -> str:
        """Process user input and return response"""
        original_input = user_input.strip()
        user_input = user_input.strip().lower()
        
        # Command handlers mapping
        command_handlers = {
            ('exit', 'quit', 'bye', 'goodbye'): lambda: "exit",
            ('help', '?'): lambda: self.display_help() or "",
            ('list', 'libraries'): lambda: self.list_known_libraries() or "",
            ('save', 'export'): self._handle_save_command,
        }
        
        # Check direct commands
        for commands, handler in command_handlers.items():
            if user_input in commands:
                return handler()
        
        # Handle prefixed commands
        prefix_handlers = [
            ('ai ', lambda x: self._handle_ai_command(x)),
            ('analyze ', lambda x: self.analyze_library(x)),
            ('recommend ', lambda x: self.get_recommendations(x)),
        ]
        
        for prefix, handler in prefix_handlers:
            if user_input.startswith(prefix):
                return handler(original_input[len(prefix):].strip())
        
        # Handle comparisons
        for separator in [' vs ', ' versus ']:
            if separator in user_input:
                parts = user_input.split(separator)
                if len(parts) == 2:
                    lib1 = parts[0].replace('compare ', '').strip()
                    lib2 = parts[1].strip()
                    return self.compare_libraries(lib1, lib2)
        
        # Handle general queries
        for keyword in ['what is ', 'tell me about ', 'about ']:
            if keyword in user_input:
                library = user_input.split(keyword)[1].strip()
                return self.analyze_library(library)
        
        # Handle recommendation requests
        if any(word in user_input for word in ['suggest', 'recommend', 'best']):
            categories = {
                'javascript': 'Frontend Framework', 'js': 'Frontend Framework',
                'frontend': 'Frontend Framework', 'web framework': 'Web Framework',
                'python': 'Web Framework', 'backend': 'Web Framework'
            }
            for keyword, category in categories.items():
                if keyword in user_input:
                    return self.get_recommendations(category)
        
        # Try AI for unmatched queries
        if self.use_ai and len(original_input.strip()) > 3:
            ai_response = self._call_azure_openai(original_input)
            if ai_response:
                return f"{Style.HEADER}🤖 AI Response:{Style.RESET}\n{ai_response}"
        
        # Default response
        ai_tip = f"• ai <question> (for AI analysis)\n" if self.use_ai else ""
        return f"""
{Style.WARNING}I'm not sure how to help with that.{Style.RESET}

{Style.INFO}Try these commands:{Style.RESET}
• analyze <library_name>
• compare <lib1> vs <lib2>
• recommend <category>
• list (see available libraries)
• help (detailed instructions)
• save (save conversation)
{ai_tip}
{Style.SUCCESS}Examples:{Style.RESET}
• "What is React?"
• "Tell me about Django"
• "Recommend JavaScript frameworks"
"""
    
    def _handle_save_command(self) -> str:
        """Handle save command"""
        if not self.conversation_history:
            return f"{Style.WARNING}No conversation to save yet.{Style.RESET}"
        filepath = self.save_conversation_to_markdown()
        return f"{Style.SUCCESS}✓ Conversation saved to: {filepath}{Style.RESET}" if filepath else f"{Style.ERROR}Failed to save conversation.{Style.RESET}"
    
    def _handle_ai_command(self, query: str) -> str:
        """Handle AI command"""
        if not self.use_ai:
            return f"{Style.ERROR}AI features not available.{Style.RESET}"
        response = self._call_azure_openai(query)
        return f"{Style.HEADER}🤖 AI Response:{Style.RESET}\n{response}" if response else f"{Style.ERROR}Couldn't process AI request.{Style.RESET}"
    
    def run(self):
        """Main chat loop"""
        self.display_welcome()
        
        try:
            while True:
                print(f"\n{Style.PRIMARY}🤖 Library Advisor:{Style.RESET} ", end="")
                user_input = input().strip()
                
                if not user_input:
                    continue
                
                # Add to history
                self.conversation_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'user_input': user_input,
                    'type': 'user'
                })
                
                response = self.process_input(user_input)
                
                if response == "exit":
                    if self.conversation_history:
                        save_prompt = input(f"\n{Style.INFO}Save conversation? (y/n): {Style.RESET}")
                        if save_prompt.lower().strip() in ['y', 'yes']:
                            self.save_conversation_to_markdown()
                    
                    print(f"\n{Style.SUCCESS}Thank you for using Library Advisory System! 👋{Style.RESET}")
                    break
                
                if response:
                    print(response)
                    self.conversation_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'response': response,
                        'type': 'assistant'
                    })
        
        except KeyboardInterrupt:
            if self.conversation_history:
                try:
                    save_prompt = input(f"\n\n{Style.INFO}Save conversation? (y/n): {Style.RESET}")
                    if save_prompt.lower().strip() in ['y', 'yes']:
                        self.save_conversation_to_markdown()
                except:
                    pass
            print(f"\n{Style.SUCCESS}Thank you for using Library Advisory System! 👋{Style.RESET}\n")
        
        except Exception as e:
            print(f"\n{Style.ERROR}An error occurred: {e}{Style.RESET}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Library Advisory System - Terminal Chatbot')
    parser.add_argument('--version', action='version', version='Library Advisory System 1.0.0')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    if args.debug:
        print("Debug mode enabled")
    
    bot = LibraryAdvisoryBot()
    bot.run()

if __name__ == "__main__":
    main()
