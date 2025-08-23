from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
from openai import AzureOpenAI
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from core.embedding_manager import EmbeddingManager, SearchResult
from core.function_handler import FunctionHandler
from core.project_scanner import ProjectProfile

# Set up logger
logger = logging.getLogger(__name__)

@dataclass
class RAGResponse:
    """Response from RAG engine"""
    answer: str
    sources: List[SearchResult]
    function_calls: List[Dict]
    confidence: float
    project_context: Optional[str] = None

class LibraryManagementTool:
    """Custom tool for library management functions"""
    
    def __init__(self, function_handler: FunctionHandler, project: ProjectProfile):
        self.function_handler = function_handler
        self.project = project
        self.name = "library_management"
        self.description = "Handle library management operations like finding references, checking compatibility, and suggesting upgrades"
    
    def run(self, query: str) -> str:
        """Execute library management function"""
        try:
            # Parse query to determine function type
            if "find references" in query.lower() or "find usage" in query.lower():
                library_name = self._extract_library_name(query)
                if library_name:
                    references = self.function_handler.find_library_references(self.project, library_name)
                    return self._format_references_result(references)
            
            elif "check compatibility" in query.lower() or "compatible" in query.lower():
                library_name = self._extract_library_name(query)
                if library_name:
                    result = self.function_handler.check_compatibility(self.project.dependencies, library_name)
                    return self._format_compatibility_result(result)
            
            elif "incompatible" in query.lower() or "conflicts" in query.lower():
                framework_version = self._extract_framework_version(query)
                if framework_version:
                    incompatible = self.function_handler.list_incompatible_libraries(self.project, framework_version)
                    return self._format_incompatible_result(incompatible)
            
            elif "upgrade" in query.lower() or "migration" in query.lower() or "update" in query.lower():
                # Check if specific framework version is mentioned
                framework_version = self._extract_framework_version(query)
                if framework_version:
                    recommendations = self.function_handler.suggest_library_upgrades(self.project, framework_version)
                else:
                    # Provide general upgrade recommendations
                    recommendations = self.function_handler.get_general_upgrade_recommendations(self.project)
                
                return self._format_upgrade_recommendations(recommendations)
            
            return "Unable to determine library management function from query."
            
        except Exception as e:
            return f"Error executing library management function: {str(e)}"
    
    def _extract_library_name(self, query: str) -> Optional[str]:
        """Extract library name from query"""
        # Simple extraction - in production, this would be more sophisticated
        words = query.split()
        for word in words:
            if word.startswith('"') and word.endswith('"'):
                return word.strip('"')
            elif word.startswith("'") and word.endswith("'"):
                return word.strip("'")
        
        # Look for common library patterns
        import re
        patterns = [
            r'library\s+([^\s]+)',
            r'package\s+([^\s]+)',
            r'dependency\s+([^\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_framework_version(self, query: str) -> Optional[str]:
        """Extract framework version from query"""
        import re
        patterns = [
            r'(react|vue|\.net|angular)[\s@]+(\d+)',
            r'to\s+(react|vue|\.net|angular)[\s@]*(\d+)',
            r'upgrade\s+to\s+([^\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if len(match.groups()) >= 2:
                    return f"{match.group(1)}@{match.group(2)}"
                else:
                    return match.group(1)
        
        return None
    
    def _format_references_result(self, references) -> str:
        """Format library references result"""
        if not references:
            return "No references found for the specified library."
        
        result = f"Found {len(references)} references:\n\n"
        for ref in references:
            result += f"• {ref.file_path} (line {ref.line_number}): {ref.context}\n"
        
        return result
    
    def _format_compatibility_result(self, result) -> str:
        """Format compatibility check result"""
        output = f"Compatibility check for {result.library}:\n\n"
        output += f"Compatible: {'Yes' if result.is_compatible else 'No'}\n\n"
        
        if result.conflicts:
            output += "Conflicts:\n"
            for conflict in result.conflicts:
                output += f"• {conflict}\n"
            output += "\n"
        
        if result.warnings:
            output += "Warnings:\n"
            for warning in result.warnings:
                output += f"• {warning}\n"
            output += "\n"
        
        if result.recommendations:
            output += "Recommendations:\n"
            for rec in result.recommendations:
                output += f"• {rec}\n"
        
        return output
    
    def _format_incompatible_result(self, incompatible) -> str:
        """Format incompatible libraries result"""
        if not incompatible:
            return "No incompatible libraries found."
        
        result = f"Found {len(incompatible)} incompatible libraries:\n\n"
        for lib in incompatible:
            result += f"• {lib}\n"
        
        return result
    
    def _format_upgrade_recommendations(self, recommendations) -> str:
        """Format upgrade recommendations"""
        if not recommendations:
            return "No upgrade recommendations found for this project."
        
        result = f"Found {len(recommendations)} upgrade recommendations for your Vue.js project:\n\n"
        
        for i, rec in enumerate(recommendations, 1):
            result += f"{i}. **{rec.library}**: {rec.current_version} → {rec.recommended_version}\n"
            result += f"   📝 Reason: {rec.reason}\n"
            
            if rec.breaking_changes:
                result += "   ⚠️ Breaking changes:\n"
                for change in rec.breaking_changes:
                    result += f"      - {change}\n"
                    
            if rec.migration_steps:
                result += "   🔧 Migration steps:\n"
                for step in rec.migration_steps:
                    result += f"      - {step}\n"
                    
            result += "\n"
        
        result += "💡 **Tip**: Always backup your project and test thoroughly after upgrades!"
        return result

class RAGEngine:
    """Main RAG processing engine"""
    
    def __init__(self, 
                 gpt_api_key: str,
                 gpt_endpoint: str,
                 gpt_deployment: str,
                 embedding_manager: EmbeddingManager):
        """
        Initialize RAG engine
        
        Args:
            gpt_api_key: Azure OpenAI API key for GPT
            gpt_endpoint: Azure OpenAI endpoint
            gpt_deployment: GPT model deployment name
            embedding_manager: Embedding manager instance
        """
        self.embedding_manager = embedding_manager
        
        # Initialize Azure OpenAI client for direct API calls
        self.client = AzureOpenAI(
            api_key=gpt_api_key,
            api_version="2024-02-01",
            azure_endpoint=gpt_endpoint
        )
        self.gpt_deployment = gpt_deployment
        
        # Initialize LangChain components
        self.llm = AzureChatOpenAI(
            azure_endpoint=gpt_endpoint,
            api_key=gpt_api_key,
            api_version="2024-02-01",
            deployment_name=gpt_deployment,
            temperature=0.1
        )
        
        self.function_handler = FunctionHandler()
        self.current_project = None
        
        # System prompt for the assistant
        self.system_prompt = """You are Library Advisor, an expert AI assistant for managing libraries and dependencies in React, Vue.js, and .NET projects.

Your capabilities include:
1. Analyzing project structure and dependencies
2. Finding library references and usage patterns
3. Checking library compatibility and conflicts
4. Suggesting library upgrades and migrations
5. Providing best practices and recommendations

When answering questions:
- ALWAYS respect the project's framework (React, Vue.js, or .NET) and provide recommendations specific to that framework
- If the project is Vue.js, provide Vue.js solutions - do NOT suggest switching to React
- If the project is React, provide React solutions - do NOT suggest switching to Vue.js
- Use information from the project's embedded content (retrieved via semantic search)
- Use function calls for dynamic analysis when needed
- Provide clear, actionable advice
- Cite specific files and line numbers when relevant
- Include both benefits and risks in your recommendations
- Format responses in a structured, easy-to-read manner

CRITICAL: Never suggest changing frameworks unless explicitly asked. Stay within the project's current framework ecosystem.

Always distinguish between information from semantic search and function call results in your responses."""
    
    def process_query(self, 
                     query: str, 
                     project: Optional[ProjectProfile] = None,
                     max_search_results: int = 5) -> RAGResponse:
        """
        Process a user query using RAG pipeline
        
        Args:
            query: User question
            project: Optional project context
            max_search_results: Maximum number of search results to use
            
        Returns:
            RAGResponse with answer and sources
        """
        logger.info(f"Processing query: {query}")
        if project:
            logger.info(f"Project context: {project.framework} project with {len(project.dependencies)} dependencies")
        else:
            logger.info("No project context provided")
            
        self.current_project = project
        
        # Step 1: Semantic search for relevant context
        search_results = []
        if project:
            search_query = f"project:{project.project_id} {query}"
            search_results = self.embedding_manager.search_similar_content(
                search_query, 
                k=max_search_results
            )
        
        # Step 2: Determine if function calling is needed
        function_calls = []
        function_results = ""
        
        if project and self._requires_function_calling(query):
            tool = LibraryManagementTool(self.function_handler, project)
            function_result = tool.run(query)
            function_results = function_result
            function_calls.append({
                'function': 'library_management',
                'query': query,
                'result': function_result
            })
        
        # Step 3: Combine context and generate response
        context = self._build_context(search_results, function_results, project)
        answer = self._generate_response(query, context)
        
        # Step 4: Calculate confidence based on available information
        confidence = self._calculate_confidence(search_results, function_calls, project)
        
        return RAGResponse(
            answer=answer,
            sources=search_results,
            function_calls=function_calls,
            confidence=confidence,
            project_context=project.name if project else None
        )
    
    def _requires_function_calling(self, query: str) -> bool:
        """Determine if query requires function calling"""
        function_keywords = [
            'find references', 'find usage', 'check compatibility',
            'incompatible', 'conflicts', 'upgrade', 'migration',
            'remove library', 'add library', 'dependencies'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in function_keywords)
    
    def _build_context(self, 
                      search_results: List[SearchResult],
                      function_results: str,
                      project: Optional[ProjectProfile]) -> str:
        """Build context string for GPT"""
        context_parts = []
        
        # Add project information
        if project:
            context_parts.append(f"PROJECT CONTEXT:")
            context_parts.append(f"Name: {project.name}")
            context_parts.append(f"Framework: {project.framework}")
            context_parts.append(f"Languages: {', '.join(project.languages)}")
            context_parts.append(f"Total Files: {project.total_files}")
            
            if project.dependencies:
                context_parts.append(f"Dependencies:")
                for dep, version in list(project.dependencies.items())[:10]:  # Limit to first 10
                    context_parts.append(f"  - {dep}: {version}")
            context_parts.append("")
        
        # Add semantic search results
        if search_results:
            context_parts.append("RELEVANT CODE SNIPPETS (from semantic search):")
            for i, result in enumerate(search_results, 1):
                context_parts.append(f"{i}. File: {result.document.metadata.get('file_path', 'unknown')}")
                context_parts.append(f"   Relevance Score: {result.score:.3f}")
                context_parts.append(f"   Content: {result.document.content[:500]}...")
                context_parts.append("")
        
        # Add function call results
        if function_results:
            context_parts.append("FUNCTION ANALYSIS RESULTS:")
            context_parts.append(function_results)
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _generate_response(self, query: str, context: str) -> str:
        """Generate response using GPT"""
        try:
            # Extract framework from context for emphasis
            framework_emphasis = ""
            if "Framework:" in context:
                for line in context.split('\n'):
                    if line.startswith("Framework:"):
                        framework = line.split("Framework:")[1].strip()
                        framework_emphasis = f"\n\nIMPORTANT: This is a {framework} project. Provide solutions specific to {framework} only."
                        break
            
            user_prompt = f"Context:\n{context}\n\nQuestion: {query}{framework_emphasis}\n\nProvide a comprehensive answer based on the context above, staying within the project's framework ecosystem."
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.gpt_deployment,
                messages=messages,
                temperature=0.1,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def _calculate_confidence(self, 
                            search_results: List[SearchResult],
                            function_calls: List[Dict],
                            project: Optional[ProjectProfile]) -> float:
        """Calculate confidence score for the response"""
        confidence = 0.0
        
        # Base confidence from having project context
        if project:
            confidence += 0.3
        
        # Confidence from search results
        if search_results:
            avg_score = sum(r.score for r in search_results) / len(search_results)
            confidence += min(0.4, avg_score)
        
        # Confidence from function calls
        if function_calls:
            confidence += 0.3
        
        return min(1.0, confidence)
    
    def get_project_summary(self, project: ProjectProfile) -> str:
        """Generate a summary of the project"""
        query = f"Summarize this {project.framework} project including its structure, dependencies, and potential improvements"
        
        response = self.process_query(query, project)
        return response.answer
