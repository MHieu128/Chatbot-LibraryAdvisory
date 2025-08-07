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

# Import required packages for Azure OpenAI
try:
    from openai import AzureOpenAI
    from dotenv import load_dotenv
    AZURE_OPENAI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Azure OpenAI dependencies not installed. Run: pip install -r requirements.txt")
    print(f"Error: {e}")
    AZURE_OPENAI_AVAILABLE = False

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
    
    # Background colors
    BG_SUCCESS = '\033[48;5;46m'
    BG_WARNING = '\033[48;5;220m'
    BG_ERROR = '\033[48;5;196m'
    BG_INFO = '\033[48;5;117m'
    
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
    def create_progress_bar(value: int, max_value: int = 100, width: int = 20) -> str:
        """Create a visual progress bar"""
        percentage = min(value / max_value, 1.0)
        filled = int(width * percentage)
        bar = "█" * filled + "░" * (width - filled)
        return f"{Colors.SUCCESS}{bar}{Colors.RESET} {value}%"
    
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

class LibraryAdvisoryBot:
    """Main chatbot class for library advisory system with Azure OpenAI integration"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        self.conversation_history = []
        self.known_libraries = self._load_library_database()
        self.system_prompt = self._get_system_prompt()
        
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
            }
        ]
        
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
        """Returns the system prompt for the library advisory system"""
        return """You are an expert library consultant and technical advisor specializing in software library evaluation and recommendation. Your role is to provide comprehensive analysis and advisory services for software libraries across all programming languages and domains.

## Your Core Capabilities

When a user provides information about a library or asks for library recommendations, you must analyze and provide detailed insights on the following dimensions:

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

### Operational Considerations
- Flexibility: Analyze customization options, extensibility, configuration flexibility, and adaptation capabilities
- Integration: Evaluate compatibility with existing systems, API quality, and ecosystem integration
- **Maintenance Status**: Check actual release frequency and version activity from registry data

### Comparative Analysis
- Similar Library Comparison: Automatically identify and compare with 3-5 similar libraries in the same domain
- Feature Matrix: Create detailed comparison tables highlighting key differences
- Use Case Recommendations: Suggest which library is best for specific scenarios
- **Registry Data Comparison**: Include actual statistics like download counts, version frequency, and community size

## Function Usage Guidelines

1. **Always Check Registries**: When analyzing .NET packages, use check_nuget_package. For JavaScript/Node.js packages, use check_npm_package
2. **Include Registry Data**: Incorporate version information, download statistics, license details, and metadata in your analysis
3. **Verify Currency**: Use registry data to assess how actively maintained a package is
4. **Compare Metrics**: When comparing libraries, include actual download statistics and version release patterns

## Response Format

Structure your responses as follows:

```markdown
# Library Analysis: [Library Name]

## Overview
[Brief description and primary use cases]

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
| Feature | [Target Library] | Alternative 1 | Alternative 2 | Alternative 3 |
|---------|------------------|---------------|---------------|---------------|
| [Key features comparison table with registry statistics]

## Recommendations 🎯
- Best for: [Ideal use cases and scenarios]
- Avoid if: [Situations where this library isn't suitable]
- Migration path: [If switching from another solution]
```

## Search and Discovery Guidelines

When users ask for library recommendations:
1. Clarify Requirements: Ask about programming language, use case, performance requirements, budget constraints, and team expertise
2. Check Registries: Use function calls to get current information about suggested packages
3. Provide Multiple Options: Always suggest 3-5 alternatives with different trade-offs, including registry statistics
4. Context-Aware Recommendations: Consider team size, project timeline, and organizational constraints
5. Future-Proofing: Evaluate long-term sustainability and evolution path based on actual registry data

## Interaction Style

- Be Objective: Present balanced analysis without bias toward any particular solution
- Use Current Data: Always use function calls to get the most recent registry information
- Support with Evidence: Use concrete metrics, benchmarks, and registry statistics
- Consider Context: Tailor advice to user's specific situation and constraints
- Stay Current: Leverage real-time registry data to provide up-to-date insights
- Be Practical: Focus on actionable insights and real-world implications based on actual usage statistics"""

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
            else:
                return f"Unknown function: {function_name}"
        except Exception as e:
            return f"Error executing function {function_name}: {str(e)}"

    def _load_library_database(self) -> Dict:
        """Load or initialize the library database"""
        database_file = "library_database.json"
        if os.path.exists(database_file):
            try:
                with open(database_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return self._get_default_library_database()
        return self._get_default_library_database()

    def _get_default_library_database(self) -> Dict:
        """Returns a sample library database with common libraries"""
        return {
            "react": {
                "name": "React",
                "category": "Frontend Framework",
                "language": "JavaScript",
                "description": "A JavaScript library for building user interfaces",
                "license": "MIT",
                "popularity": "Very High",
                "alternatives": ["Vue.js", "Angular", "Svelte", "Solid.js"]
            },
            "vue": {
                "name": "Vue.js",
                "category": "Frontend Framework", 
                "language": "JavaScript",
                "description": "Progressive JavaScript framework for building UIs",
                "license": "MIT",
                "popularity": "High",
                "alternatives": ["React", "Angular", "Svelte", "Alpine.js"]
            },
            "django": {
                "name": "Django",
                "category": "Web Framework",
                "language": "Python",
                "description": "High-level Python web framework",
                "license": "BSD",
                "popularity": "High",
                "alternatives": ["Flask", "FastAPI", "Pyramid", "Tornado"]
            },
            "flask": {
                "name": "Flask",
                "category": "Web Framework",
                "language": "Python", 
                "description": "Lightweight WSGI web application framework",
                "license": "BSD",
                "popularity": "High",
                "alternatives": ["Django", "FastAPI", "Bottle", "CherryPy"]
            },
            "express": {
                "name": "Express.js",
                "category": "Web Framework",
                "language": "JavaScript/Node.js",
                "description": "Fast, unopinionated web framework for Node.js",
                "license": "MIT",
                "popularity": "Very High",
                "alternatives": ["Koa.js", "Hapi.js", "Fastify", "NestJS"]
            }
        }

    def _save_library_database(self):
        """Save the current library database to file"""
        try:
            with open("library_database.json", 'w', encoding='utf-8') as f:
                json.dump(self.known_libraries, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"{Colors.WARNING}Warning: Could not save library database: {e}{Colors.ENDC}")

    def save_conversation_to_markdown(self, filename: Optional[str] = None) -> str:
        """Save the current conversation to a markdown file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"library_analysis_{timestamp}.md"
        
        try:
            # Ensure reports directory exists
            reports_dir = "reports"
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)
                print(f"{Colors.OKCYAN}Created reports directory: {reports_dir}{Colors.ENDC}")
            
            filepath = os.path.join(reports_dir, filename)
            print(f"{Colors.OKCYAN}Saving to: {filepath}{Colors.ENDC}")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write header
                f.write("# Library Advisory System - Analysis Report\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"AI Enhanced: {'Yes' if self.use_ai else 'No'}\n\n")
                f.write("---\n\n")
                
                # Check if we have conversation history
                if not self.conversation_history:
                    f.write("## No Conversation History\n\n")
                    f.write("This session did not contain any queries or responses.\n\n")
                    f.write("---\n\n")
                else:
                    # Write conversation history
                    current_analysis = ""
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
                
                # Add summary section
                f.write("## Session Summary\n\n")
                f.write(f"- Total Queries: {len([e for e in self.conversation_history if e['type'] == 'user'])}\n")
                f.write(f"- Libraries in Database: {len(self.known_libraries)}\n")
                f.write(f"- AI Features Used: {'Yes' if self.use_ai else 'No'}\n")
                f.write(f"- Session Duration: {self._calculate_session_duration()}\n\n")
                
                # Add footer
                f.write("---\n\n")
                f.write("*Generated by Library Advisory System*\n")
                f.write("*Visit our documentation for more information*\n")
            
            print(f"{Colors.OKGREEN}✓ File written successfully: {filepath}{Colors.ENDC}")
            return filepath
            
        except Exception as e:
            print(f"{Colors.FAIL}Error saving to markdown: {e}{Colors.ENDC}")
            print(f"{Colors.WARNING}Debug info: Working directory: {os.getcwd()}{Colors.ENDC}")
            print(f"{Colors.WARNING}Debug info: Reports directory exists: {os.path.exists('reports')}{Colors.ENDC}")
            import traceback
            print(f"{Colors.WARNING}Full error: {traceback.format_exc()}{Colors.ENDC}")
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

    def _call_azure_openai(self, user_query: str, context: str = "") -> Optional[str]:
        """Call Azure OpenAI for intelligent analysis with function calling support"""
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
            
            # Initial API call with function tools
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

    def _enhance_with_ai(self, basic_analysis: str, user_query: str) -> str:
        """Enhance basic analysis with AI insights"""
        if not self.use_ai:
            return basic_analysis
            
        # Get AI enhancement
        ai_response = self._call_azure_openai(
            user_query, 
            f"Basic analysis provided: {basic_analysis[:1000]}"
        )
        
        if ai_response:
            return f"{basic_analysis}\n\n{Colors.HEADER}🤖 AI-Enhanced Analysis:{Colors.ENDC}\n{ai_response}"
        
        return basic_analysis

    def display_welcome(self):
        """Display modern welcome message with enhanced design"""
        width = ModernFormatter.get_terminal_width()
        
        # Main header with gradient effect
        print(f"\n{Colors.HEADER}{Colors.BOLD}")
        print("┌" + "─" * (width - 2) + "┐")
        print(f"│{' ' * ((width - 28) // 2)}{Icons.LIBRARY} Library Advisory System {Icons.ANALYSIS}{' ' * ((width - 28) // 2)}│")
        print("└" + "─" * (width - 2) + "┘")
        print(f"{Colors.RESET}\n")
        
        # AI Status Card
        ai_status = "ENABLED" if self.use_ai else "DISABLED"
        ai_icon = "🤖" if self.use_ai else "🔧"
        ai_color = Colors.SUCCESS if self.use_ai else Colors.WARNING
        status_text = f"{ai_icon} AI-Enhanced Analysis: {ai_status}"
        if self.use_ai:
            status_text += " (Azure OpenAI)"
        else:
            status_text += " (Basic mode)"
        
        print(ModernFormatter.create_card(
            "System Status",
            status_text,
            Icons.INFO,
            ai_color
        ))
        
        # Capabilities Section
        capabilities = [
            f"{Icons.ANALYSIS} Library analysis and comparison",
            f"{Icons.GEAR} Technical evaluation and recommendations", 
            f"{Icons.MONEY} Cost and licensing analysis",
            f"{Icons.SHIELD} Risk assessment and security evaluation",
            f"{Icons.COMPARE} Finding alternatives and migration paths"
        ]
        
        if self.use_ai:
            capabilities.append(f"{Icons.LIGHTBULB} AI-powered intelligent insights")
        
        capabilities_text = "\n".join(capabilities)
        print(ModernFormatter.create_card(
            "I can help you with",
            capabilities_text,
            Icons.ROCKET,
            Colors.PRIMARY
        ))
        
        # Commands Section
        commands = [
            f"{Colors.ACCENT}help{Colors.RESET} - Detailed instructions and examples",
            f"{Colors.ACCENT}list{Colors.RESET} - Browse available libraries",
            f"{Colors.ACCENT}analyze <library>{Colors.RESET} - Detailed library analysis",
            f"{Colors.ACCENT}compare <lib1> vs <lib2>{Colors.RESET} - Side-by-side comparison",
            f"{Colors.ACCENT}recommend <category>{Colors.RESET} - Get recommendations"
        ]
        
        if self.use_ai:
            commands.append(f"{Colors.ACCENT}ai <question>{Colors.RESET} - AI-powered analysis")
        
        commands.extend([
            f"{Colors.ACCENT}save{Colors.RESET} - Export conversation to markdown",
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
        print(f"💡 Quick start: Try 'analyze React' or 'compare Vue.js vs Angular'")
        print(f"{Colors.RESET}\n")

    def display_help(self):
        """Display detailed help information"""
        ai_help = ""
        if self.use_ai:
            ai_help = f"""
{Colors.OKGREEN}6. AI-Powered Analysis:{Colors.ENDC}
   • "ai What are the security considerations for React?"
   • "ai Compare Django vs FastAPI for microservices"
   • "ai Best practices for choosing a frontend framework"
   • "ai Latest trends in JavaScript libraries"
"""

        help_text = f"""
{Colors.HEADER}{Colors.BOLD}📚 Library Advisory System - Detailed Help{Colors.ENDC}

{Colors.OKCYAN}Example Queries:{Colors.ENDC}

{Colors.OKGREEN}1. Library Analysis:{Colors.ENDC}
   • "analyze React"
   • "tell me about Django"
   • "evaluate Vue.js for enterprise use"

{Colors.OKGREEN}2. Library Comparison:{Colors.ENDC}
   • "compare React vs Vue.js"
   • "React vs Angular for large applications"
   • "Django vs Flask for API development"

{Colors.OKGREEN}3. Recommendation Requests:{Colors.ENDC}
   • "recommend JavaScript frameworks"
   • "best Python web frameworks"
   • "suggest testing libraries for Node.js"
   • "find alternatives to jQuery"

{Colors.OKGREEN}4. Specific Requirements:{Colors.ENDC}
   • "I need a lightweight Python web framework"
   • "What's the best database ORM for Python?"
   • "Recommend UI libraries with good TypeScript support"

{Colors.OKGREEN}5. Context-Specific Questions:{Colors.ENDC}
   • "Best framework for a startup with limited budget"
   • "Enterprise-grade libraries with commercial support"
   • "Open source alternatives to commercial solutions"
{ai_help}
{Colors.WARNING}Features:{Colors.ENDC}
• Comprehensive technical analysis
• Cost and licensing evaluation  
• Security and risk assessment
• Performance comparisons
• Migration guidance
• Future-proofing advice
• Save conversations to markdown files
{f"• AI-enhanced intelligent insights{Colors.ENDC}" if self.use_ai else ""}

{Colors.FAIL}Note:{Colors.ENDC} This system provides analysis based on general knowledge{" and AI insights" if self.use_ai else ""}. 
Always verify current information and test libraries in your specific environment.
"""
        print(help_text)

    def list_known_libraries(self):
        """Display modern styled list of known libraries"""
        header = f"\n{Colors.HEADER}{Colors.BOLD}{Icons.LIBRARY} Known Libraries Database{Colors.RESET}\n"
        
        # Group libraries by category
        categories = {}
        for lib_key, lib_info in self.known_libraries.items():
            category = lib_info.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(lib_info)
        
        # Create cards for each category
        category_cards = []
        for category, libs in categories.items():
            
            # Create library list for this category
            lib_items = []
            for lib in libs:
                popularity_badge = ModernFormatter.create_badge(
                    lib['popularity'], 
                    Colors.SUCCESS if 'high' in lib['popularity'].lower() else Colors.INFO
                )
                
                lib_line = (f"{Icons.ARROW_RIGHT} {Colors.BOLD}{lib['name']}{Colors.RESET} "
                           f"({Colors.ACCENT}{lib['language']}{Colors.RESET}) "
                           f"{popularity_badge}")
                lib_items.append(lib_line)
                lib_items.append(f"   {Colors.DIM}{lib['description']}{Colors.RESET}")
                lib_items.append("")  # Empty line for spacing
            
            # Remove last empty line
            if lib_items and lib_items[-1] == "":
                lib_items.pop()
                
            category_content = "\n".join(lib_items)
            
            category_cards.append(ModernFormatter.create_card(
                f"{category} ({len(libs)} libraries)",
                category_content,
                Icons.GEAR,
                Colors.PRIMARY
            ))
        
        # Quick actions
        quick_actions = f"""
{Icons.ANALYSIS} {Colors.ACCENT}analyze <library>{Colors.RESET} - Detailed analysis of any library
{Icons.COMPARE} {Colors.ACCENT}compare <lib1> vs <lib2>{Colors.RESET} - Compare two libraries
{Icons.TARGET} {Colors.ACCENT}recommend <category>{Colors.RESET} - Get category recommendations
        """.strip()
        
        actions_card = ModernFormatter.create_card(
            "What's next?",
            quick_actions,
            Icons.LIGHTBULB,
            Colors.INFO
        )
        
        # Database stats
        stats_content = f"""
{Icons.LIBRARY} Total Libraries: {Colors.ACCENT}{len(self.known_libraries)}{Colors.RESET}
{Icons.GEAR} Categories: {Colors.ACCENT}{len(categories)}{Colors.RESET}
{Icons.COMMUNITY} AI Enhancement: {Colors.SUCCESS if self.use_ai else Colors.WARNING}{'Enabled' if self.use_ai else 'Disabled'}{Colors.RESET}
        """.strip()
        
        stats_card = ModernFormatter.create_card(
            "Database Statistics",
            stats_content,
            Icons.CHART,
            Colors.MUTED
        )
        
        # Combine all parts
        result = header + stats_card + "\n".join(category_cards) + actions_card
        print(result)

    def analyze_library(self, library_name: str) -> str:
        """Analyze a specific library and return detailed analysis"""
        # Simulate comprehensive library analysis
        # In a real implementation, this would integrate with external APIs
        # or databases for current information
        
        library_name_lower = library_name.lower()
        
        # Check if library is in our database
        lib_info = None
        for key, info in self.known_libraries.items():
            if key == library_name_lower or info['name'].lower() == library_name_lower:
                lib_info = info
                break
        
        # Generate basic analysis
        if lib_info:
            basic_analysis = self._generate_detailed_analysis(lib_info)
        else:
            basic_analysis = self._generate_general_analysis(library_name)
        
        # Enhance with AI if available
        if self.use_ai:
            return self._enhance_with_ai(basic_analysis, f"analyze {library_name}")
        
        return basic_analysis

    def _generate_detailed_analysis(self, lib_info: Dict) -> str:
        """Generate modern detailed analysis for a known library"""
        name = lib_info['name']
        
        # Header with modern styling
        header = f"\n{Colors.HEADER}{Colors.BOLD}{Icons.ANALYSIS} Library Analysis: {name}{Colors.RESET}\n"
        
        # Overview card
        overview_content = f"""
{Colors.PRIMARY}{lib_info['description']}{Colors.RESET}

{Icons.GEAR} Language: {Colors.ACCENT}{lib_info['language']}{Colors.RESET}
{Icons.LIBRARY} Category: {Colors.ACCENT}{lib_info['category']}{Colors.RESET}
{Icons.LICENSE} License: {Colors.ACCENT}{lib_info['license']}{Colors.RESET}
{Icons.STAR} Popularity: {Colors.ACCENT}{lib_info['popularity']}{Colors.RESET}
        """.strip()
        
        overview_card = ModernFormatter.create_card(
            "Overview",
            overview_content,
            Icons.INFO,
            Colors.PRIMARY
        )
        
        # Advantages card
        advantages_content = self._get_modern_advantages(lib_info)
        advantages_card = ModernFormatter.create_card(
            "Advantages",
            advantages_content,
            Icons.SUCCESS,
            Colors.SUCCESS
        )
        
        # Disadvantages card
        disadvantages_content = self._get_modern_disadvantages(lib_info)
        disadvantages_card = ModernFormatter.create_card(
            "Disadvantages", 
            disadvantages_content,
            Icons.WARNING,
            Colors.WARNING
        )
        
        # Cost & Licensing card
        cost_content = self._get_modern_cost_analysis(lib_info)
        cost_card = ModernFormatter.create_card(
            "Cost & Licensing",
            cost_content,
            Icons.MONEY,
            Colors.ACCENT
        )
        
        # Risk Assessment card
        risk_content = self._get_modern_risk_assessment(lib_info)
        risk_card = ModernFormatter.create_card(
            "Risk Assessment",
            risk_content,
            Icons.SHIELD,
            Colors.ERROR
        )
        
        # Technical Considerations card
        technical_content = self._get_modern_technical_considerations(lib_info)
        technical_card = ModernFormatter.create_card(
            "Technical Considerations",
            technical_content,
            Icons.GEAR,
            Colors.INFO
        )
        
        # Comparison table
        comparison_content = self._get_modern_comparison_table(lib_info)
        comparison_card = ModernFormatter.create_card(
            "Similar Libraries Comparison",
            comparison_content,
            Icons.COMPARE,
            Colors.PRIMARY
        )
        
        # Recommendations card
        recommendations_content = self._get_modern_recommendations(lib_info)
        recommendations_card = ModernFormatter.create_card(
            "Recommendations",
            recommendations_content,
            Icons.TARGET,
            Colors.SUCCESS
        )
        
        return (header + overview_card + advantages_card + disadvantages_card + 
                cost_card + risk_card + technical_card + comparison_card + recommendations_card)

    def _generate_general_analysis(self, library_name: str) -> str:
        """Generate general analysis template for unknown libraries"""
        return f"""
{Colors.HEADER}{Colors.BOLD}# Library Analysis: {library_name}{Colors.ENDC}

{Colors.WARNING}Note: This library is not in our current database. Here's a general analysis framework:{Colors.ENDC}

{Colors.OKCYAN}## Research Checklist for {library_name}:{Colors.ENDC}

{Colors.OKGREEN}✓ Technical Analysis:{Colors.ENDC}
  • Check GitHub repository (stars, forks, recent commits)
  • Review documentation quality and completeness
  • Analyze performance benchmarks
  • Evaluate community support and ecosystem

{Colors.OKGREEN}✓ Legal & Licensing:{Colors.ENDC}
  • Verify license type and compatibility
  • Check for any usage restrictions
  • Review commercial licensing options if applicable

{Colors.OKGREEN}✓ Security & Maintenance:{Colors.ENDC}
  • Review security vulnerability history
  • Check update frequency and maintenance status
  • Evaluate long-term sustainability

{Colors.OKGREEN}✓ Integration & Compatibility:{Colors.ENDC}
  • Test compatibility with your tech stack
  • Evaluate integration complexity
  • Check for breaking changes in recent versions

{Colors.WARNING}Recommendation:{Colors.ENDC} Please research the current status of {library_name} 
and consider asking about specific aspects you'd like me to analyze.
"""

    def _get_modern_advantages(self, lib_info: Dict) -> str:
        """Generate modern styled advantages"""
        name = lib_info['name']
        category = lib_info['category']
        
        advantages_map = {
            "React": [
                ("Community Support", "Massive ecosystem with 200M+ weekly downloads"),
                ("Performance", "Virtual DOM enables efficient rendering and updates"),
                ("Architecture", "Component-based design promotes code reusability"),
                ("Developer Experience", "Excellent tools like React DevTools and Hot Reload"),
                ("TypeScript", "First-class TypeScript support and type definitions"),
                ("Enterprise Ready", "Backed by Meta with guaranteed long-term support")
            ],
            "Vue.js": [
                ("Learning Curve", "Gentle progression from beginner to advanced concepts"),
                ("Adoption", "Progressive framework - integrate incrementally"),
                ("Performance", "Efficient reactivity system with proxy-based observation"),
                ("Developer Experience", "Intuitive template syntax and SFC architecture"),
                ("Tooling", "Vue CLI, Vite integration, and excellent dev tools"),
                ("Bundle Size", "Smaller footprint compared to React/Angular")
            ],
            "Django": [
                ("Batteries Included", "ORM, admin panel, authentication out of the box"),
                ("Security", "Built-in protection against CSRF, XSS, SQL injection"),
                ("Rapid Development", "DRY principle enables fast prototyping"),
                ("Scalability", "Powers Instagram, Pinterest, and other large platforms"),
                ("Community", "Extensive package ecosystem and active community"),
                ("Documentation", "Comprehensive guides and best practices")
            ],
            "Flask": [
                ("Minimalism", "Lightweight core with modular extensions"),
                ("Flexibility", "Full control over application architecture"),
                ("Learning", "Simple to understand and quick to prototype"),
                ("Microservices", "Perfect for distributed service architectures"),
                ("Ecosystem", "Rich extension library for specific needs"),
                ("Customization", "Zero opinions on project structure")
            ],
            "Express.js": [
                ("Performance", "Fast, lightweight with minimal overhead"),
                ("Middleware", "Extensive middleware ecosystem for all needs"),
                ("APIs", "Excellent for RESTful services and GraphQL"),
                ("Integration", "Seamless database and service integration"),
                ("Community", "Huge Node.js ecosystem support"),
                ("Microservices", "Industry standard for Node.js microservices")
            ]
        }
        
        advantages = advantages_map.get(name, [
            ("Popularity", f"Established choice in {category} category"),
            ("Community", f"Active {lib_info['language']} ecosystem support"), 
            ("License", f"Open source with {lib_info['license']} license")
        ])
        
        formatted_advantages = []
        for title, description in advantages:
            formatted_advantages.append(f"{Icons.CHECK} {Colors.BOLD}{title}{Colors.RESET}: {description}")
        
        return "\n".join(formatted_advantages)

    def _get_modern_disadvantages(self, lib_info: Dict) -> str:
        """Generate modern styled disadvantages"""
        name = lib_info['name']
        
        disadvantages_map = {
            "React": [
                ("Learning Curve", "Complex concepts like hooks, context, and state management"),
                ("Ecosystem Fragmentation", "Too many choices can lead to decision paralysis"),
                ("JSX Syntax", "Additional learning overhead for traditional developers"),
                ("Dependencies", "Requires multiple libraries for complete functionality"),
                ("Bundle Size", "Can become large without proper optimization"),
                ("Build Complexity", "Complex toolchain setup and configuration")
            ],
            "Vue.js": [
                ("Market Share", "Smaller job market compared to React ecosystem"),
                ("Enterprise Adoption", "Less widespread in large enterprise environments"),
                ("Backing Concerns", "Single maintainer dependency vs corporate backing"),
                ("Resources", "Fewer third-party resources and tutorials"),
                ("TypeScript", "While good, TypeScript support trails React")
            ],
            "Django": [
                ("Overkill", "Heavy for simple applications and APIs"),
                ("Monolithic", "Opinionated structure limits architectural flexibility"),
                ("ORM Limitations", "Complex queries can become cumbersome"),
                ("Deployment", "More complex setup compared to simpler frameworks"),
                ("Real-time", "Not ideal for WebSocket/real-time applications"),
                ("Templates", "Template system less flexible than modern alternatives")
            ],
            "Flask": [
                ("Setup Overhead", "Requires many decisions and manual configuration"),
                ("No Batteries", "No built-in ORM, admin, or authentication"),
                ("Structure Variance", "Can lead to inconsistent project architectures"),
                ("Security", "Manual implementation of security features required"),
                ("Dependencies", "May require numerous third-party packages"),
                ("Architecture", "Learning curve for proper application design")
            ],
            "Express.js": [
                ("Minimalism", "Requires extensive setup for production applications"),
                ("Security", "No built-in security features or best practices"),
                ("Async Complexity", "Callback management and error handling challenges"),
                ("Error Handling", "Manual implementation of robust error management"),
                ("Structure", "No opinionated structure can cause inconsistency"),
                ("Vulnerabilities", "Security risks if not properly configured")
            ]
        }
        
        disadvantages = disadvantages_map.get(name, [
            ("Learning Curve", "May vary based on developer background and experience"),
            ("Maintenance", "Dependent on community for updates and long-term support"),
            ("Compatibility", "Potential integration issues with other technologies")
        ])
        
        formatted_disadvantages = []
        for title, description in disadvantages:
            formatted_disadvantages.append(f"{Icons.CROSS} {Colors.BOLD}{title}{Colors.RESET}: {description}")
        
        return "\n".join(formatted_disadvantages)

    def _get_modern_cost_analysis(self, lib_info: Dict) -> str:
        """Generate modern cost analysis"""
        license_type = lib_info['license']
        
        if license_type in ['MIT', 'BSD', 'Apache']:
            cost_items = [
                f"{Icons.LICENSE} License: {Colors.SUCCESS}{license_type}{Colors.RESET} - Free for commercial use",
                f"{Icons.MONEY} Licensing Fees: {Colors.SUCCESS}$0{Colors.RESET} - Open source",
                f"{Icons.GEAR} Development Costs:",
                f"  • Learning curve and training time",
                f"  • Initial setup and configuration",
                f"  • Ongoing maintenance and updates",
                f"{Icons.COMMUNITY} Support Options:",
                f"  • Community forums and documentation (Free)",
                f"  • Professional consulting services (Variable)",
                f"  • Enterprise support contracts (Optional)"
            ]
        else:
            cost_items = [
                f"{Icons.LICENSE} License: {Colors.WARNING}{license_type}{Colors.RESET} - Review terms carefully",
                f"{Icons.MONEY} Pricing: Check vendor pricing model",
                f"{Icons.GEAR} Total Cost: Calculate based on team size and usage scale"
            ]
        
        return "\n".join(cost_items)

    def _get_modern_risk_assessment(self, lib_info: Dict) -> str:
        """Generate modern risk assessment"""
        popularity = lib_info['popularity'].lower()
        
        # Determine risk levels
        security_risk = "Low" if 'high' in popularity else "Medium"
        maintenance_risk = "Low" if 'very high' in popularity else "Medium"
        business_risk = self._get_business_risk_level(lib_info)
        
        # Create risk indicators
        risk_items = [
            f"{Icons.SECURITY} Security Risk: {self._get_risk_badge(security_risk)}",
            f"  • Regular security updates and patches",
            f"  • Active vulnerability monitoring",
            f"  • {popularity.title()} adoption reduces attack surface",
            "",
            f"{Icons.MAINTENANCE} Maintenance Risk: {self._get_risk_badge(maintenance_risk)}",
            f"  • Community-driven development model",
            f"  • Regular release cycle and updates",
            f"  • Long-term support considerations",
            "",
            f"{Icons.CHART} Business Risk: {self._get_risk_badge(business_risk)}",
            f"  • Vendor lock-in assessment",
            f"  • Technology evolution and trends",
            f"  • Skills availability in market",
            "",
            f"{Icons.ARROW_RIGHT} Migration Risk: {self._get_migration_risk_modern(lib_info)}"
        ]
        
        return "\n".join(risk_items)

    def _get_risk_badge(self, risk_level: str) -> str:
        """Create colored risk level badge"""
        if risk_level.lower() == "low":
            return f"{Colors.SUCCESS}{risk_level}{Colors.RESET}"
        elif risk_level.lower() == "medium":
            return f"{Colors.WARNING}{risk_level}{Colors.RESET}"
        else:
            return f"{Colors.ERROR}{risk_level}{Colors.RESET}"

    def _get_migration_risk_modern(self, lib_info: Dict) -> str:
        """Get modern migration risk assessment"""
        name = lib_info['name']
        risk_map = {
            "React": f"{self._get_risk_badge('Medium')} - Large ecosystem but many alternatives available",
            "Vue.js": f"{self._get_risk_badge('Low')} - Excellent migration paths to other frameworks",
            "Django": f"{self._get_risk_badge('Medium')} - Well-established migration patterns",
            "Flask": f"{self._get_risk_badge('Low')} - Lightweight nature simplifies migration",
            "Express.js": f"{self._get_risk_badge('Low')} - Standard patterns transfer easily"
        }
        return risk_map.get(name, f"{self._get_risk_badge('Medium')} - Evaluate based on project complexity")

    def _get_modern_technical_considerations(self, lib_info: Dict) -> str:
        """Generate modern technical considerations"""
        name = lib_info['name']
        
        complexity_map = {
            "React": ("Medium-High", 4),
            "Vue.js": ("Low-Medium", 2),
            "Django": ("Medium", 3),
            "Flask": ("Low-Medium", 2),
            "Express.js": ("Low-Medium", 2)
        }
        
        complexity, complexity_score = complexity_map.get(name, ("Medium", 3))
        performance_score = self._get_performance_score(name)
        learning_score = self._get_learning_score(name)
        
        technical_items = [
            f"{Icons.GEAR} Implementation Complexity: {Colors.ACCENT}{complexity}{Colors.RESET}",
            f"   {ModernFormatter.create_progress_bar(complexity_score * 20, 100, 15)}",
            "",
            f"{Icons.PERFORMANCE} Performance Rating: {self._get_performance_rating_modern(name)}",
            f"   {ModernFormatter.create_progress_bar(performance_score * 20, 100, 15)}",
            "",
            f"{Icons.LIGHTBULB} Learning Curve: {self._get_learning_curve_modern(name)}",
            f"   {ModernFormatter.create_progress_bar(learning_score * 20, 100, 15)}",
            "",
            f"{Icons.ARROW_RIGHT} Flexibility: {self._get_flexibility_rating(name)}",
            f"{Icons.ARROW_RIGHT} Integration: Good compatibility with {Colors.ACCENT}{lib_info['language']}{Colors.RESET} ecosystem",
            f"{Icons.ARROW_RIGHT} Ecosystem: {self._get_ecosystem_rating(name)}"
        ]
        
        return "\n".join(technical_items)

    def _get_performance_score(self, name: str) -> int:
        """Get performance score (1-5)"""
        scores = {
            "React": 4, "Vue.js": 5, "Django": 4,
            "Flask": 5, "Express.js": 5
        }
        return scores.get(name, 3)

    def _get_learning_score(self, name: str) -> int:
        """Get learning difficulty score (1=easy, 5=hard)"""
        scores = {
            "React": 4, "Vue.js": 2, "Django": 3,
            "Flask": 2, "Express.js": 3
        }
        return scores.get(name, 3)

    def _get_performance_rating_modern(self, name: str) -> str:
        """Get modern performance rating"""
        ratings = {
            "React": f"{Colors.SUCCESS}Good with optimization{Colors.RESET}",
            "Vue.js": f"{Colors.SUCCESS}Excellent out of the box{Colors.RESET}",
            "Django": f"{Colors.SUCCESS}Good for complex applications{Colors.RESET}",
            "Flask": f"{Colors.SUCCESS}Excellent for lightweight apps{Colors.RESET}",
            "Express.js": f"{Colors.SUCCESS}Excellent for I/O operations{Colors.RESET}"
        }
        return ratings.get(name, f"{Colors.SUCCESS}Good{Colors.RESET}")

    def _get_learning_curve_modern(self, name: str) -> str:
        """Get modern learning curve assessment"""
        curves = {
            "React": f"{Colors.WARNING}Steep for beginners{Colors.RESET}",
            "Vue.js": f"{Colors.SUCCESS}Gentle and beginner-friendly{Colors.RESET}",
            "Django": f"{Colors.INFO}Moderate for Python developers{Colors.RESET}",
            "Flask": f"{Colors.SUCCESS}Easy to start{Colors.RESET}",
            "Express.js": f"{Colors.INFO}Moderate with Node.js knowledge{Colors.RESET}"
        }
        return curves.get(name, f"{Colors.INFO}Moderate{Colors.RESET}")

    def _get_flexibility_rating(self, name: str) -> str:
        """Get flexibility rating"""
        flexible = ["Flask", "Express.js"]
        if name in flexible:
            return f"{Colors.SUCCESS}High customization options{Colors.RESET}"
        return f"{Colors.INFO}Medium customization options{Colors.RESET}"

    def _get_ecosystem_rating(self, name: str) -> str:
        """Get ecosystem rating"""
        large_ecosystems = ["React", "Django", "Express.js"]
        if name in large_ecosystems:
            return f"{Colors.SUCCESS}Large and mature ecosystem{Colors.RESET}"
        elif name == "Vue.js":
            return f"{Colors.INFO}Growing ecosystem{Colors.RESET}"
        return f"{Colors.INFO}Good ecosystem support{Colors.RESET}"

    def _get_business_risk_level(self, lib_info: Dict) -> str:
        """Determine business risk level"""
        popularity = lib_info['popularity'].lower()
        if 'very high' in popularity:
            return "Low"
        elif 'high' in popularity:
            return "Low-Medium"
        else:
            return "Medium"

    def _get_migration_risk(self, lib_info: Dict) -> str:
        """Determine migration risk"""
        name = lib_info['name']
        risk_map = {
            "React": "Medium - Large ecosystem but many alternatives available",
            "Vue.js": "Low-Medium - Good migration paths to other frameworks",
            "Django": "Medium - Well-established patterns for migration",
            "Flask": "Low - Lightweight nature makes migration easier",
            "Express.js": "Low - Standard patterns transferable to other frameworks"
        }
        return risk_map.get(name, "Medium - Evaluate based on project complexity")

    def _get_technical_considerations(self, lib_info: Dict) -> str:
        """Generate technical considerations"""
        name = lib_info['name']
        
        complexity_map = {
            "React": "Medium-High",
            "Vue.js": "Low-Medium", 
            "Django": "Medium",
            "Flask": "Low-Medium",
            "Express.js": "Low-Medium"
        }
        
        complexity = complexity_map.get(name, "Medium")
        
        return f"""
  • Complexity: {complexity} implementation difficulty
  • Flexibility: {'High' if name in ['Flask', 'Express.js'] else 'Medium'} customization options
  • Integration: Good compatibility with {lib_info['language']} ecosystem
  • Learning Curve: {self._get_learning_curve(name)}
  • Performance: {self._get_performance_rating(name)}
"""

    def _get_learning_curve(self, name: str) -> str:
        """Get learning curve assessment"""
        curve_map = {
            "React": "Steep for beginners, moderate for JS developers",
            "Vue.js": "Gentle, excellent for beginners",
            "Django": "Moderate, good for Python developers",
            "Flask": "Gentle, but requires architectural decisions",
            "Express.js": "Moderate, requires Node.js knowledge"
        }
        return curve_map.get(name, "Moderate")

    def _get_performance_rating(self, name: str) -> str:
        """Get performance rating"""
        perf_map = {
            "React": "Good with optimization",
            "Vue.js": "Excellent out of the box",
            "Django": "Good for complex applications",
            "Flask": "Excellent for lightweight apps",
            "Express.js": "Excellent for I/O operations"
        }
        return perf_map.get(name, "Good")

    def _get_modern_comparison_table(self, lib_info: Dict) -> str:
        """Generate modern comparison table with alternatives"""
        alternatives = lib_info.get('alternatives', [])
        if not alternatives:
            return f"{Colors.MUTED}No direct alternatives available in current database{Colors.RESET}"
        
        name = lib_info['name']
        
        # Create comparison data
        comparison_data = []
        comparison_data.append(["Feature", name] + alternatives[:3])
        
        # Add comparison rows
        rows = [
            ["Learning Curve", self._get_learning_curve_short(name)] + 
            [self._get_learning_curve_short(alt) for alt in alternatives[:3]],
            
            ["Performance", self._get_performance_short(name)] + 
            [self._get_performance_short(alt) for alt in alternatives[:3]],
            
            ["Community Size", lib_info['popularity']] + 
            ["Research needed"] * min(3, len(alternatives)),
            
            ["License", lib_info['license']] + 
            ["Check individually"] * min(3, len(alternatives))
        ]
        
        comparison_data.extend(rows)
        
        # Format as modern table
        table_lines = []
        for i, row in enumerate(comparison_data):
            if i == 0:  # Header
                header_line = " │ ".join(f"{Colors.BOLD}{cell[:15]:15}{Colors.RESET}" for cell in row)
                table_lines.append(header_line)
                table_lines.append("─" * (len(header_line) - len(Colors.BOLD) - len(Colors.RESET)))
            else:
                data_line = " │ ".join(f"{cell[:15]:15}" for cell in row)
                table_lines.append(data_line)
        
        table_text = "\n".join(table_lines)
        
        note = f"\n\n{Colors.MUTED}{Icons.INFO} For detailed comparison, analyze each alternative individually{Colors.RESET}"
        
        return table_text + note

    def _get_learning_curve_short(self, name: str) -> str:
        """Get short learning curve assessment"""
        curves = {
            "React": "Steep", "Vue.js": "Gentle", "Django": "Moderate",
            "Flask": "Easy", "Express.js": "Moderate", "Angular": "Steep",
            "Svelte": "Easy", "FastAPI": "Easy"
        }
        return curves.get(name, "Moderate")

    def _get_performance_short(self, name: str) -> str:
        """Get short performance rating"""
        ratings = {
            "React": "Good", "Vue.js": "Excellent", "Django": "Good", 
            "Flask": "Excellent", "Express.js": "Excellent", "Angular": "Good",
            "Svelte": "Excellent", "FastAPI": "Excellent"
        }
        return ratings.get(name, "Good")

    def _get_modern_recommendations(self, lib_info: Dict) -> str:
        """Generate modern recommendations"""
        name = lib_info['name']
        
        recommendations_map = {
            "React": {
                "best_for": "Large-scale applications, experienced teams, component-heavy UIs",
                "avoid_if": "Simple websites, tight deadlines, teams new to JavaScript",
                "migration": "Gradual adoption strategy, start with new components",
                "alternatives": "Vue.js for easier learning, Angular for enterprise"
            },
            "Vue.js": {
                "best_for": "Progressive enhancement, rapid prototyping, beginner-friendly projects",
                "avoid_if": "Very large enterprise applications requiring extensive ecosystem",
                "migration": "Excellent migration path from jQuery or vanilla JavaScript",
                "alternatives": "React for larger ecosystem, Svelte for smaller bundles"
            },
            "Django": {
                "best_for": "Content-heavy sites, rapid development, admin interface needs",
                "avoid_if": "Microservices architecture, real-time applications, API-only backends",
                "migration": "Plan database migration carefully, consider gradual API migration",
                "alternatives": "FastAPI for modern APIs, Flask for flexibility"
            },
            "Flask": {
                "best_for": "APIs, microservices, custom architectures, learning web development",
                "avoid_if": "Rapid prototyping needs, teams preferring opinionated structure",
                "migration": "Easiest migration path from other Python frameworks",
                "alternatives": "Django for batteries-included, FastAPI for modern async"
            },
            "Express.js": {
                "best_for": "APIs, real-time applications, Node.js environments, microservices",
                "avoid_if": "CPU-intensive tasks, teams without JavaScript experience",
                "migration": "Standard migration path from other Node.js frameworks",
                "alternatives": "Fastify for performance, NestJS for structure"
            }
        }
        
        rec = recommendations_map.get(name, {
            "best_for": f"Projects in {lib_info['category']} category",
            "avoid_if": "Incompatible requirements or team expertise mismatch",
            "migration": "Evaluate migration complexity based on current technology stack",
            "alternatives": "Research similar libraries in the same category"
        })
        
        recommendation_items = [
            f"{Icons.TARGET} {Colors.BOLD}Best suited for:{Colors.RESET}",
            f"  {rec['best_for']}",
            "",
            f"{Icons.WARNING} {Colors.BOLD}Consider alternatives if:{Colors.RESET}",
            f"  {rec['avoid_if']}",
            "",
            f"{Icons.ARROW_RIGHT} {Colors.BOLD}Migration strategy:{Colors.RESET}",
            f"  {rec['migration']}",
            "",
            f"{Icons.LIGHTBULB} {Colors.BOLD}Consider also:{Colors.RESET}",
            f"  {rec['alternatives']}"
        ]
        
        return "\n".join(recommendation_items)

    def compare_libraries(self, lib1: str, lib2: str) -> str:
        """Compare two libraries with modern side-by-side design"""
        
        # Modern header
        header = f"\n{Colors.HEADER}{Colors.BOLD}{Icons.COMPARE} Library Comparison{Colors.RESET}\n"
        
        # Create comparison header card
        comparison_header = ModernFormatter.create_card(
            f"Comparing: {lib1} vs {lib2}",
            f"Comprehensive side-by-side analysis of both libraries",
            Icons.CHART,
            Colors.PRIMARY
        )
        
        # Get analyses for both libraries
        analysis1 = self.analyze_library(lib1)
        analysis2 = self.analyze_library(lib2)
        
        # Create side-by-side comparison summary
        summary_content = f"""
{Colors.ACCENT}{Colors.BOLD}{lib1}{Colors.RESET}                    vs                    {Colors.ACCENT}{Colors.BOLD}{lib2}{Colors.RESET}
{'─' * 25}    {'─' * 25}

{Icons.TARGET} Use Cases:
• Focus on your specific requirements
• Consider team expertise and experience level
• Evaluate project timeline and complexity
• Assess long-term maintenance needs
• Review integration requirements
• Analyze performance criteria

{Icons.LIGHTBULB} Decision Framework:
• Technical requirements alignment
• Learning curve vs delivery timeline
• Community support and ecosystem
• License compatibility with project
• Migration and future-proofing strategy
        """.strip()
        
        summary_card = ModernFormatter.create_card(
            "Summary & Decision Guide",
            summary_content,
            Icons.TARGET,
            Colors.INFO
        )
        
        # Combine all parts
        basic_comparison = header + comparison_header + analysis1 + "\n" + analysis2 + "\n" + summary_card
        
        # Add AI enhancement if available
        if self.use_ai:
            ai_comparison = self._call_azure_openai(
                f"Create a detailed comparison between {lib1} and {lib2} libraries",
                f"Libraries to compare: {lib1} and {lib2}"
            )
            if ai_comparison:
                ai_card = ModernFormatter.create_card(
                    "AI-Powered Detailed Comparison",
                    ai_comparison,
                    Icons.LIGHTBULB,
                    Colors.ACCENT
                )
                basic_comparison += ai_card
        
        return basic_comparison

    def get_recommendations(self, category: str) -> str:
        """Get modern styled recommendations for a specific category"""
        category_libraries = []
        for lib_key, lib_info in self.known_libraries.items():
            if category.lower() in lib_info['category'].lower():
                category_libraries.append(lib_info)
        
        if not category_libraries:
            # No libraries found - show available categories
            available_categories = self._get_available_categories()
            
            not_found_content = f"""
{Colors.WARNING}No libraries found matching: {category}{Colors.RESET}

{Colors.INFO}{Icons.LIBRARY} Available Categories:{Colors.RESET}
{available_categories}

{Colors.PRIMARY}{Icons.LIGHTBULB} Try these examples:{Colors.RESET}
• "recommend web frameworks"
• "suggest frontend libraries" 
• "find database libraries"
• "recommend testing tools"
            """.strip()
            
            return ModernFormatter.create_card(
                "Category Not Found",
                not_found_content,
                Icons.WARNING,
                Colors.WARNING
            )
        
        # Header
        header = f"\n{Colors.HEADER}{Colors.BOLD}{Icons.TARGET} Recommendations for: {category.title()}{Colors.RESET}\n"
        
        # Found libraries card
        found_content = f"Found {Colors.ACCENT}{len(category_libraries)}{Colors.RESET} libraries in this category"
        found_card = ModernFormatter.create_card(
            "Search Results",
            found_content,
            Icons.SUCCESS,
            Colors.SUCCESS
        )
        
        # Library recommendations
        library_cards = []
        for lib in category_libraries[:5]:  # Limit to top 5
            lib_content = f"""
{Colors.DIM}Language:{Colors.RESET} {Colors.ACCENT}{lib['language']}{Colors.RESET}
{Colors.DIM}Description:{Colors.RESET} {lib['description']}

{Icons.STAR} Popularity: {ModernFormatter.create_badge(lib['popularity'], Colors.PRIMARY)}
{Icons.LICENSE} License: {ModernFormatter.create_badge(lib['license'], Colors.INFO)}

{Icons.ARROW_RIGHT} {Colors.DIM}For detailed analysis, type:{Colors.RESET} {Colors.ACCENT}analyze {lib['name']}{Colors.RESET}
            """.strip()
            
            library_cards.append(ModernFormatter.create_card(
                lib['name'],
                lib_content,
                Icons.LIBRARY,
                Colors.PRIMARY
            ))
        
        # Quick actions
        quick_actions = f"""
{Icons.ANALYSIS} {Colors.ACCENT}analyze <library>{Colors.RESET} - Get detailed analysis
{Icons.COMPARE} {Colors.ACCENT}compare <lib1> vs <lib2>{Colors.RESET} - Side-by-side comparison
{Icons.TARGET} {Colors.ACCENT}ai <question>{Colors.RESET} - AI-powered insights (if enabled)
        """.strip()
        
        actions_card = ModernFormatter.create_card(
            "Next Steps",
            quick_actions,
            Icons.LIGHTBULB,
            Colors.INFO
        )
        
        # Combine all parts
        result = header + found_card + "\n".join(library_cards) + actions_card
        return result

    def _get_available_categories(self) -> str:
        """Get list of available categories"""
        categories = set()
        for lib_info in self.known_libraries.values():
            categories.add(lib_info['category'])
        return "\n".join(f"  • {cat}" for cat in sorted(categories))

    def process_input(self, user_input: str) -> str:
        """Process user input and return appropriate response"""
        original_input = user_input.strip()
        user_input = user_input.strip().lower()
        
        # Handle exit commands
        if user_input in ['exit', 'quit', 'bye', 'goodbye']:
            return "exit"
        
        # Handle help command
        if user_input in ['help', '?', 'help me']:
            self.display_help()
            return ""
        
        # Handle list command
        if user_input in ['list', 'show libraries', 'libraries']:
            self.list_known_libraries()
            return ""
        
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
        
        # Handle AI command
        if user_input.startswith('ai ') and self.use_ai:
            query = original_input[3:].strip()
            response = self._call_azure_openai(query)
            if response:
                return f"{Colors.HEADER}🤖 AI Response:{Colors.ENDC}\n{response}"
            else:
                return f"{Colors.FAIL}Sorry, I couldn't process your AI request at the moment.{Colors.ENDC}"
        
        # Handle comparison commands
        if ' vs ' in user_input or ' versus ' in user_input:
            separator = ' vs ' if ' vs ' in user_input else ' versus '
            parts = user_input.split(separator)
            if len(parts) == 2:
                lib1 = parts[0].strip()
                lib2 = parts[1].strip()
                # Remove common prefixes
                for prefix in ['compare ', 'analyze ']:
                    if lib1.startswith(prefix):
                        lib1 = lib1[len(prefix):]
                return self.compare_libraries(lib1, lib2)
        
        # Handle analyze commands
        if user_input.startswith('analyze '):
            library = user_input[8:].strip()
            return self.analyze_library(library)
        
        # Handle recommend commands
        if user_input.startswith('recommend '):
            category = user_input[10:].strip()
            return self.get_recommendations(category)
        
        # Handle general queries
        if any(keyword in user_input for keyword in ['what is', 'tell me about', 'about']):
            # Extract library name
            for keyword in ['what is ', 'tell me about ', 'about ']:
                if keyword in user_input:
                    library = user_input.split(keyword)[1].strip()
                    return self.analyze_library(library)
        
        # Handle recommendation requests
        if any(keyword in user_input for keyword in ['suggest', 'recommend', 'best', 'good']):
            return self._handle_recommendation_request(user_input)
        
        # If AI is available, try to handle any unmatched query with AI
        if self.use_ai and len(original_input.strip()) > 3:
            ai_response = self._call_azure_openai(original_input)
            if ai_response:
                return f"{Colors.HEADER}🤖 AI Response:{Colors.ENDC}\n{ai_response}"
        
        # Default response for unrecognized input
        ai_tip = f"• ai <your question> (for AI-powered analysis)\n" if self.use_ai else ""
        
        return f"""
{Colors.WARNING}I'm not sure how to help with that specific request.{Colors.ENDC}

{Colors.OKCYAN}Try these commands:{Colors.ENDC}
• analyze <library_name>
• compare <lib1> vs <lib2>
• recommend <category>
• list (to see available libraries)
• help (for detailed instructions)
• save (to save conversation to markdown)
{ai_tip}
{Colors.OKGREEN}Or ask me about specific libraries like:{Colors.ENDC}
• "What is React?"
• "Tell me about Django"
• "Recommend JavaScript frameworks"
"""

    def _handle_recommendation_request(self, user_input: str) -> str:
        """Handle various recommendation request formats"""
        # Extract category/technology from the request
        categories = {
            'javascript': 'Frontend Framework',
            'js': 'Frontend Framework',
            'frontend': 'Frontend Framework',
            'web framework': 'Web Framework',
            'python': 'Web Framework',
            'backend': 'Web Framework',
            'api': 'Web Framework'
        }
        
        for keyword, category in categories.items():
            if keyword in user_input:
                return self.get_recommendations(category)
        
        # If no specific category found, show general guidance
        return f"""
{Colors.OKCYAN}To provide better recommendations, please specify:{Colors.ENDC}

{Colors.OKGREEN}Technology/Language:{Colors.ENDC}
• JavaScript/Frontend frameworks
• Python web frameworks  
• Node.js frameworks
• Database libraries
• Testing frameworks

{Colors.OKGREEN}Use Case:{Colors.ENDC}
• "recommend Python web frameworks"
• "suggest JavaScript testing libraries"
• "best database ORMs for Python"

{Colors.WARNING}Or browse available categories with: list{Colors.ENDC}
"""

    def run(self):
        """Main chat loop"""
        self.display_welcome()
        
        try:
            while True:
                print(f"\n{Colors.OKBLUE}🤖 Library Advisor:{Colors.ENDC} ", end="")
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
                    
                    print(f"\n{Colors.OKGREEN}Thank you for using Library Advisory System! 👋{Colors.ENDC}")
                    print(f"{Colors.OKCYAN}Happy coding!{Colors.ENDC}\n")
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
            print(f"{Colors.OKGREEN}Thank you for using Library Advisory System! 👋{Colors.ENDC}\n")
        
        except Exception as e:
            print(f"\n{Colors.FAIL}An error occurred: {e}{Colors.ENDC}")
            print(f"{Colors.WARNING}Please restart the application.{Colors.ENDC}\n")
        
        finally:
            # Save library database before exit
            self._save_library_database()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Library Advisory System - Terminal Chatbot')
    parser.add_argument('--version', action='version', version='Library Advisory System 1.0.0')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    if args.debug:
        print("Debug mode enabled")
    
    # Initialize and run the chatbot
    bot = LibraryAdvisoryBot()
    bot.run()

if __name__ == "__main__":
    main()
