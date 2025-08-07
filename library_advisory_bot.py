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

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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
        """Display welcome message and instructions"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}🔍 Library Advisory System{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*50}{Colors.ENDC}")
        print(f"{Colors.OKBLUE}Welcome to the comprehensive library evaluation and recommendation system!{Colors.ENDC}")
        
        # Show AI status
        if self.use_ai:
            print(f"{Colors.OKGREEN}🤖 AI-Enhanced Analysis: ENABLED (Azure OpenAI){Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}🤖 AI-Enhanced Analysis: DISABLED (Basic mode){Colors.ENDC}")
        print()
        
        print(f"{Colors.OKCYAN}I can help you with:{Colors.ENDC}")
        print(f"  • {Colors.OKGREEN}Library analysis and comparison{Colors.ENDC}")
        print(f"  • {Colors.OKGREEN}Technical evaluation and recommendations{Colors.ENDC}")
        print(f"  • {Colors.OKGREEN}Cost and licensing analysis{Colors.ENDC}")
        print(f"  • {Colors.OKGREEN}Risk assessment and security evaluation{Colors.ENDC}")
        print(f"  • {Colors.OKGREEN}Finding alternatives and migration paths{Colors.ENDC}")
        if self.use_ai:
            print(f"  • {Colors.OKGREEN}AI-powered intelligent insights and recommendations{Colors.ENDC}")
        print()
        
        print(f"{Colors.WARNING}Commands:{Colors.ENDC}")
        print(f"  • Type {Colors.BOLD}'help'{Colors.ENDC} for detailed instructions")
        print(f"  • Type {Colors.BOLD}'list'{Colors.ENDC} to see available libraries")
        print(f"  • Type {Colors.BOLD}'compare <lib1> vs <lib2>'{Colors.ENDC} to compare libraries")
        print(f"  • Type {Colors.BOLD}'analyze <library>'{Colors.ENDC} for detailed analysis")
        print(f"  • Type {Colors.BOLD}'recommend <category>'{Colors.ENDC} for recommendations")
        if self.use_ai:
            print(f"  • Type {Colors.BOLD}'ai <your question>'{Colors.ENDC} for AI-powered analysis")
        print(f"  • Type {Colors.BOLD}'save'{Colors.ENDC} to save conversation to markdown file")
        print(f"  • Type {Colors.BOLD}'exit' or 'quit'{Colors.ENDC} to leave\n")

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
        """Display list of known libraries"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}📚 Known Libraries Database{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*40}{Colors.ENDC}\n")
        
        categories = {}
        for lib_key, lib_info in self.known_libraries.items():
            category = lib_info.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(lib_info)
        
        for category, libs in categories.items():
            print(f"{Colors.OKCYAN}{Colors.BOLD}{category}:{Colors.ENDC}")
            for lib in libs:
                print(f"  • {Colors.OKGREEN}{lib['name']}{Colors.ENDC} ({lib['language']}) - {lib['description']}")
            print()

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
        """Generate detailed analysis for a known library"""
        name = lib_info['name']
        analysis = f"""
{Colors.HEADER}{Colors.BOLD}# Library Analysis: {name}{Colors.ENDC}

{Colors.OKCYAN}## Overview{Colors.ENDC}
{lib_info['description']} ({lib_info['language']})
Category: {lib_info['category']}
License: {lib_info['license']}
Popularity: {lib_info['popularity']}

{Colors.OKGREEN}## Advantages ✅{Colors.ENDC}
{self._get_advantages(lib_info)}

{Colors.FAIL}## Disadvantages ❌{Colors.ENDC}
{self._get_disadvantages(lib_info)}

{Colors.WARNING}## Cost & Licensing 💰{Colors.ENDC}
{self._get_cost_analysis(lib_info)}

{Colors.FAIL}## Risk Assessment ⚠️{Colors.ENDC}
{self._get_risk_assessment(lib_info)}

{Colors.OKBLUE}## Technical Considerations 🔧{Colors.ENDC}
{self._get_technical_considerations(lib_info)}

{Colors.OKCYAN}## Similar Libraries Comparison 📊{Colors.ENDC}
{self._get_comparison_table(lib_info)}

{Colors.OKGREEN}## Recommendations 🎯{Colors.ENDC}
{self._get_recommendations(lib_info)}
"""
        return analysis

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

    def _get_advantages(self, lib_info: Dict) -> str:
        """Generate advantages based on library info"""
        name = lib_info['name']
        category = lib_info['category']
        
        advantages_map = {
            "React": [
                "Massive community support and ecosystem",
                "Virtual DOM for efficient rendering",
                "Component-based architecture promotes reusability",
                "Excellent developer tools and debugging support",
                "Strong TypeScript integration",
                "Backed by Meta (Facebook) ensuring long-term support"
            ],
            "Vue.js": [
                "Gentle learning curve and excellent documentation",
                "Progressive adoption - can be integrated incrementally",
                "Excellent performance with efficient reactivity system",
                "Strong template syntax and single-file components",
                "Great developer experience with Vue CLI and dev tools",
                "Smaller bundle size compared to React/Angular"
            ],
            "Django": [
                "Batteries-included framework with ORM, admin panel, auth",
                "Excellent security features built-in",
                "Rapid development with DRY principle",
                "Scalable architecture suitable for large applications",
                "Strong community and extensive third-party packages",
                "Excellent documentation and learning resources"
            ],
            "Flask": [
                "Lightweight and minimalist design",
                "High flexibility and customization options",
                "Easy to learn and quick to prototype",
                "Excellent for microservices architecture",
                "Strong ecosystem of extensions",
                "Full control over application structure"
            ],
            "Express.js": [
                "Minimalist and unopinionated framework",
                "Excellent performance and scalability",
                "Huge middleware ecosystem",
                "Easy integration with databases and services",
                "Strong community support",
                "Perfect for RESTful APIs and microservices"
            ]
        }
        
        advantages = advantages_map.get(name, [
            f"Popular choice in {category} category",
            f"Good community support for {lib_info['language']} ecosystem",
            f"Open source with {lib_info['license']} license"
        ])
        
        return "\n".join(f"  • {adv}" for adv in advantages)

    def _get_disadvantages(self, lib_info: Dict) -> str:
        """Generate disadvantages based on library info"""
        name = lib_info['name']
        
        disadvantages_map = {
            "React": [
                "Steep learning curve for beginners",
                "Rapid ecosystem changes can cause fragmentation",
                "JSX syntax might be confusing initially",
                "Requires additional libraries for full functionality",
                "Large bundle size for simple applications",
                "Complex build setup and tooling requirements"
            ],
            "Vue.js": [
                "Smaller ecosystem compared to React",
                "Less job market demand than React/Angular",
                "Potential concerns about long-term backing",
                "Limited resources for complex enterprise scenarios",
                "TypeScript support, while good, not as mature as React"
            ],
            "Django": [
                "Can be overkill for simple applications",
                "Monolithic structure may limit flexibility",
                "ORM can become complex for advanced queries",
                "Deployment can be complex for beginners",
                "Less suitable for real-time applications",
                "Template system limitations compared to modern alternatives"
            ],
            "Flask": [
                "Requires more setup and configuration decisions",
                "No built-in ORM or admin interface",
                "Can lead to inconsistent project structures",
                "Security features need manual implementation",
                "May require more third-party dependencies",
                "Learning curve for proper application architecture"
            ],
            "Express.js": [
                "Minimalist approach requires more manual setup",
                "No built-in security features",
                "Callback hell potential (though mitigated by async/await)",
                "Requires careful error handling implementation",
                "No opinionated structure can lead to inconsistency",
                "Security vulnerabilities if not properly configured"
            ]
        }
        
        disadvantages = disadvantages_map.get(name, [
            "Learning curve may vary depending on background",
            "Dependency on community for updates and support",
            "Potential compatibility issues with other libraries"
        ])
        
        return "\n".join(f"  • {dis}" for dis in disadvantages)

    def _get_cost_analysis(self, lib_info: Dict) -> str:
        """Generate cost analysis"""
        license_type = lib_info['license']
        
        if license_type in ['MIT', 'BSD', 'Apache']:
            return f"""
  • License: {license_type} - Free for commercial use
  • Pricing: Open source, no licensing fees
  • Total Cost of Ownership: 
    - Development time and learning curve
    - Training and onboarding costs
    - Potential support and consulting fees
    - Infrastructure and hosting costs
  • Hidden Costs: Third-party integrations, premium tools, enterprise support
"""
        else:
            return f"""
  • License: {license_type} - Review terms carefully
  • Pricing: Check current pricing model
  • Total Cost of Ownership: Calculate based on team size and usage
"""

    def _get_risk_assessment(self, lib_info: Dict) -> str:
        """Generate risk assessment"""
        return f"""
  • Security: Regular security updates, {lib_info['popularity']} adoption reduces risk
  • Maintenance: Active community, regular updates expected
  • Business Risk: {self._get_business_risk_level(lib_info)} risk based on popularity and backing
  • Technical Debt: Manageable with proper version management
  • Migration Risk: {self._get_migration_risk(lib_info)}
"""

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

    def _get_comparison_table(self, lib_info: Dict) -> str:
        """Generate comparison table with alternatives"""
        alternatives = lib_info.get('alternatives', [])
        if not alternatives:
            return "No direct alternatives in database"
        
        name = lib_info['name']
        table = f"""
| Feature | {name} | {alternatives[0] if len(alternatives) > 0 else 'N/A'} | {alternatives[1] if len(alternatives) > 1 else 'N/A'} | {alternatives[2] if len(alternatives) > 2 else 'N/A'} |
|---------|--------|------------|------------|------------|
| Learning Curve | {self._get_learning_curve(name)} | Compare individually | Compare individually | Compare individually |
| Performance | {self._get_performance_rating(name)} | Varies | Varies | Varies |
| Community | {lib_info['popularity']} | Research needed | Research needed | Research needed |
| License | {lib_info['license']} | Check individually | Check individually | Check individually |

{Colors.WARNING}Note: For detailed comparison, analyze each alternative individually.{Colors.ENDC}
"""
        return table

    def _get_recommendations(self, lib_info: Dict) -> str:
        """Generate recommendations"""
        name = lib_info['name']
        
        recommendations_map = {
            "React": {
                "best_for": "Large-scale applications, teams with JS experience, component-heavy UIs",
                "avoid_if": "Simple websites, tight deadlines, small teams without JS experience",
                "migration": "Consider gradual adoption, start with new components"
            },
            "Vue.js": {
                "best_for": "Progressive enhancement, teams new to frameworks, rapid prototyping",
                "avoid_if": "Very large enterprise apps, teams requiring extensive ecosystem",
                "migration": "Excellent migration path from jQuery or vanilla JS"
            },
            "Django": {
                "best_for": "Content-heavy sites, rapid development, teams needing admin interface",
                "avoid_if": "Microservices, real-time apps, API-only backends",
                "migration": "Plan database migration carefully, consider gradual API migration"
            },
            "Flask": {
                "best_for": "APIs, microservices, custom architectures, learning web development",
                "avoid_if": "Rapid prototyping with admin needs, teams preferring opinionated structure",
                "migration": "Easy to migrate to from other Python frameworks"
            },
            "Express.js": {
                "best_for": "APIs, real-time applications, Node.js environments, microservices",
                "avoid_if": "CPU-intensive tasks, teams without JS experience",
                "migration": "Good migration path from other Node.js frameworks"
            }
        }
        
        rec = recommendations_map.get(name, {
            "best_for": f"Projects in {lib_info['category']} category",
            "avoid_if": "Incompatible requirements or team expertise",
            "migration": "Evaluate migration complexity based on current stack"
        })
        
        return f"""
  • Best for: {rec['best_for']}
  • Avoid if: {rec['avoid_if']}
  • Migration path: {rec['migration']}
"""

    def compare_libraries(self, lib1: str, lib2: str) -> str:
        """Compare two libraries side by side"""
        basic_comparison = f"""
{Colors.HEADER}{Colors.BOLD}📊 Library Comparison: {lib1} vs {lib2}{Colors.ENDC}

{Colors.OKCYAN}Analyzing both libraries...{Colors.ENDC}

{Colors.OKGREEN}--- {lib1} Analysis ---{Colors.ENDC}
{self.analyze_library(lib1)}

{Colors.OKGREEN}--- {lib2} Analysis ---{Colors.ENDC}
{self.analyze_library(lib2)}

{Colors.WARNING}Summary Recommendation:{Colors.ENDC}
Consider your specific requirements:
• Team expertise and learning curve
• Project timeline and complexity
• Long-term maintenance needs
• Integration requirements
• Performance criteria
"""
        
        # Enhance with AI comparison if available
        if self.use_ai:
            ai_comparison = self._call_azure_openai(
                f"Compare {lib1} vs {lib2} libraries in detail",
                f"Libraries to compare: {lib1} and {lib2}"
            )
            if ai_comparison:
                basic_comparison += f"\n\n{Colors.HEADER}🤖 AI-Powered Detailed Comparison:{Colors.ENDC}\n{ai_comparison}"
        
        return basic_comparison

    def get_recommendations(self, category: str) -> str:
        """Get recommendations for a specific category"""
        category_libraries = []
        for lib_key, lib_info in self.known_libraries.items():
            if category.lower() in lib_info['category'].lower():
                category_libraries.append(lib_info)
        
        if not category_libraries:
            return f"""
{Colors.WARNING}No libraries found for category: {category}{Colors.ENDC}

{Colors.OKCYAN}Available categories:{Colors.ENDC}
{self._get_available_categories()}

{Colors.OKGREEN}Try asking for specific recommendations like:{Colors.ENDC}
• "recommend web frameworks"
• "suggest frontend libraries"
• "find database libraries"
"""
        
        result = f"""
{Colors.HEADER}{Colors.BOLD}🎯 Recommendations for: {category}{Colors.ENDC}

{Colors.OKCYAN}Found {len(category_libraries)} libraries in this category:{Colors.ENDC}

"""
        
        for lib in category_libraries[:5]:  # Limit to top 5
            result += f"""
{Colors.OKGREEN}• {lib['name']}{Colors.ENDC}
  Language: {lib['language']}
  Description: {lib['description']}
  Popularity: {lib['popularity']}
  License: {lib['license']}
  
"""
        
        result += f"{Colors.WARNING}For detailed analysis of any library, type: analyze <library_name>{Colors.ENDC}"
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
