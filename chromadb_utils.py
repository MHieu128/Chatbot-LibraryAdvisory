#!/usr/bin/env python3
"""
ChromaDB Utilities for Library Advisory System
Provides semantic search and vector database functionality
"""

import os
import json
import logging
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass

# ChromaDB and ML imports
try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    import numpy as np
    CHROMADB_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ChromaDB dependencies not installed. Run: pip install -r requirements.txt")
    print(f"Error: {e}")
    CHROMADB_AVAILABLE = False

@dataclass
class SearchResult:
    """Data structure for search results"""
    id: str
    document: str
    metadata: Dict[str, Any]
    distance: float
    score: float  # Similarity score (1 - distance)

@dataclass
class LibraryData:
    """Enhanced library data structure"""
    name: str
    category: str
    language: str
    description: str
    license: str
    popularity: str
    alternatives: List[str]
    use_cases: List[str]
    pros: List[str]
    cons: List[str]
    ideal_for: str
    avoid_if: str
    learning_curve: str
    performance_rating: int
    community_size: str
    documentation_quality: str
    github_stars: int = 0
    weekly_downloads: int = 0

class ChromaDBManager:
    """Main ChromaDB manager for the Library Advisory System"""
    
    def __init__(self, 
                 persist_directory: str = "./chromadb_data",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize ChromaDB manager
        
        Args:
            persist_directory: Directory to store ChromaDB data
            embedding_model: Sentence transformer model for embeddings
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB dependencies not available. Install requirements.txt")
        
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.client = None
        self.collections = {}
        
        # Collection names
        self.LIBRARIES_COLLECTION = "libraries"
        self.FAQS_COLLECTION = "faqs" 
        self.USER_QUERIES_COLLECTION = "user_queries"
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        
        # Ensure data directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize client and collections
        self._initialize_client()
        self._initialize_collections()
    
    def _initialize_client(self):
        """Initialize ChromaDB client with persistence"""
        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    allow_reset=False,
                    anonymized_telemetry=False
                )
            )
            self.logger.info(f"ChromaDB client initialized with persistence at {self.persist_directory}")
        except Exception as e:
            self.logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise
    
    def _initialize_collections(self):
        """Initialize all required collections with embedding functions"""
        try:
            # Create embedding function
            embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model
            )
            
            # Initialize libraries collection
            self.collections[self.LIBRARIES_COLLECTION] = self.client.get_or_create_collection(
                name=self.LIBRARIES_COLLECTION,
                embedding_function=embedding_function,
                metadata={"description": "Library information with semantic search capabilities"}
            )
            
            # Initialize FAQs collection
            self.collections[self.FAQS_COLLECTION] = self.client.get_or_create_collection(
                name=self.FAQS_COLLECTION,
                embedding_function=embedding_function,
                metadata={"description": "Frequently asked questions with semantic matching"}
            )
            
            # Initialize user queries collection
            self.collections[self.USER_QUERIES_COLLECTION] = self.client.get_or_create_collection(
                name=self.USER_QUERIES_COLLECTION,
                embedding_function=embedding_function,
                metadata={"description": "User interaction history for personalization"}
            )
            
            self.logger.info("All ChromaDB collections initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize collections: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics about all collections"""
        stats = {}
        for name, collection in self.collections.items():
            try:
                stats[name] = collection.count()
            except Exception as e:
                self.logger.warning(f"Failed to get count for collection {name}: {e}")
                stats[name] = 0
        return stats
    
    # === LIBRARY MANAGEMENT ===
    
    def add_library(self, library_data: LibraryData) -> bool:
        """Add a library to the database with enhanced metadata"""
        try:
            # Create rich document text for better embeddings
            document = self._create_library_document(library_data)
            
            # Prepare metadata
            metadata = {
                "name": library_data.name,
                "category": library_data.category,
                "language": library_data.language,
                "license": library_data.license,
                "popularity": library_data.popularity,
                "learning_curve": library_data.learning_curve,
                "performance_rating": library_data.performance_rating,
                "community_size": library_data.community_size,
                "documentation_quality": library_data.documentation_quality,
                "github_stars": library_data.github_stars,
                "weekly_downloads": library_data.weekly_downloads,
                "alternatives": ",".join(library_data.alternatives),
                "use_cases": ",".join(library_data.use_cases),
                "added_date": datetime.now().isoformat()
            }
            
            # Generate unique ID
            library_id = f"library_{library_data.name.lower().replace(' ', '_').replace('.', '_')}"
            
            # Add to collection
            self.collections[self.LIBRARIES_COLLECTION].add(
                ids=[library_id],
                documents=[document],
                metadatas=[metadata]
            )
            
            self.logger.info(f"Added library: {library_data.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add library {library_data.name}: {e}")
            return False
    
    def _create_library_document(self, library_data: LibraryData) -> str:
        """Create a rich document text for better embeddings"""
        document_parts = [
            f"{library_data.name} is a {library_data.language} {library_data.category}.",
            f"Description: {library_data.description}",
            f"License: {library_data.license}",
            f"Popularity: {library_data.popularity}",
            f"Learning curve: {library_data.learning_curve}",
            f"Use cases: {', '.join(library_data.use_cases)}",
            f"Advantages: {', '.join(library_data.pros)}",
            f"Disadvantages: {', '.join(library_data.cons)}",
            f"Ideal for: {library_data.ideal_for}",
            f"Avoid if: {library_data.avoid_if}",
            f"Alternatives: {', '.join(library_data.alternatives)}"
        ]
        
        return " ".join(document_parts)
    
    def search_libraries(self, 
                        query: str, 
                        n_results: int = 5,
                        filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search libraries using semantic similarity"""
        try:
            # Build where clause for filtering
            where_clause = self._build_where_clause(filters) if filters else None
            
            # Perform search
            results = self.collections[self.LIBRARIES_COLLECTION].query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Convert to SearchResult objects
            search_results = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    search_result = SearchResult(
                        id=results['ids'][0][i],
                        document=results['documents'][0][i],
                        metadata=results['metadatas'][0][i],
                        distance=results['distances'][0][i],
                        score=1 - results['distances'][0][i]  # Convert distance to similarity score
                    )
                    search_results.append(search_result)
            
            self.logger.info(f"Library search for '{query}' returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            self.logger.error(f"Library search failed for query '{query}': {e}")
            return []
    
    def get_library_by_name(self, name: str) -> Optional[SearchResult]:
        """Get a specific library by name"""
        try:
            library_id = f"library_{name.lower().replace(' ', '_').replace('.', '_')}"
            
            results = self.collections[self.LIBRARIES_COLLECTION].get(
                ids=[library_id],
                include=['documents', 'metadatas']
            )
            
            if results['ids']:
                return SearchResult(
                    id=results['ids'][0],
                    document=results['documents'][0],
                    metadata=results['metadatas'][0],
                    distance=0.0,
                    score=1.0
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get library '{name}': {e}")
            return None
    
    def find_similar_libraries(self, library_name: str, n_results: int = 3) -> List[SearchResult]:
        """Find libraries similar to a given library"""
        try:
            # Get the library document first
            library = self.get_library_by_name(library_name)
            
            if not library:
                # Fallback: search by name
                return self.search_libraries(library_name, n_results)
            
            # Search for similar libraries using the library's document
            results = self.collections[self.LIBRARIES_COLLECTION].query(
                query_texts=[library.document],
                n_results=n_results + 1,  # +1 to exclude the original library
                include=['documents', 'metadatas', 'distances']
            )
            
            # Filter out the original library and convert to SearchResult objects
            similar_libraries = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    result_id = results['ids'][0][i]
                    
                    # Skip the original library
                    if result_id == library.id:
                        continue
                    
                    search_result = SearchResult(
                        id=result_id,
                        document=results['documents'][0][i],
                        metadata=results['metadatas'][0][i],
                        distance=results['distances'][0][i],
                        score=1 - results['distances'][0][i]
                    )
                    similar_libraries.append(search_result)
                    
                    # Stop when we have enough results
                    if len(similar_libraries) >= n_results:
                        break
            
            self.logger.info(f"Found {len(similar_libraries)} similar libraries to {library_name}")
            return similar_libraries
            
        except Exception as e:
            self.logger.error(f"Failed to find similar libraries to '{library_name}': {e}")
            return []
    
    # === FAQ MANAGEMENT ===
    
    def add_faq(self, question: str, answer: str, category: str, 
               topic: str = "", difficulty: str = "intermediate",
               related_libraries: List[str] = None) -> bool:
        """Add a FAQ to the database"""
        try:
            # Create document combining question and answer
            document = f"Question: {question} Answer: {answer}"
            
            # Prepare metadata
            metadata = {
                "question": question,
                "category": category,
                "topic": topic,
                "difficulty": difficulty,
                "related_libraries": ",".join(related_libraries or []),
                "added_date": datetime.now().isoformat()
            }
            
            # Generate unique ID
            faq_id = f"faq_{hashlib.md5(question.encode()).hexdigest()[:8]}"
            
            # Add to collection
            self.collections[self.FAQS_COLLECTION].add(
                ids=[faq_id],
                documents=[document],
                metadatas=[metadata]
            )
            
            self.logger.info(f"Added FAQ: {question[:50]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add FAQ: {e}")
            return False
    
    def search_faqs(self, query: str, n_results: int = 3, 
                   category_filter: Optional[str] = None) -> List[SearchResult]:
        """Search FAQs using semantic similarity"""
        try:
            # Build filters
            where_clause = None
            if category_filter:
                where_clause = {"category": category_filter}
            
            # Perform search
            results = self.collections[self.FAQS_COLLECTION].query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Convert to SearchResult objects
            search_results = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    # Only include results with good similarity (distance < 0.7)
                    if results['distances'][0][i] < 0.7:
                        search_result = SearchResult(
                            id=results['ids'][0][i],
                            document=results['documents'][0][i],
                            metadata=results['metadatas'][0][i],
                            distance=results['distances'][0][i],
                            score=1 - results['distances'][0][i]
                        )
                        search_results.append(search_result)
            
            self.logger.info(f"FAQ search for '{query}' returned {len(search_results)} relevant results")
            return search_results
            
        except Exception as e:
            self.logger.error(f"FAQ search failed for query '{query}': {e}")
            return []
    
    # === USER QUERY MANAGEMENT ===
    
    def store_user_query(self, query: str, response: str, 
                        session_id: str, user_intent: str = "unknown",
                        resolved: bool = True, satisfaction_score: float = 3.0) -> bool:
        """Store user interaction for learning and personalization"""
        try:
            # Create document combining query and response
            document = f"User Query: {query} System Response: {response}"
            
            # Prepare metadata
            metadata = {
                "session_id": session_id,
                "user_intent": user_intent,
                "resolved": resolved,
                "satisfaction_score": satisfaction_score,
                "query_length": len(query),
                "response_length": len(response),
                "timestamp": datetime.now().isoformat()
            }
            
            # Generate unique ID
            query_id = f"query_{session_id}_{int(time.time())}_{hashlib.md5(query.encode()).hexdigest()[:6]}"
            
            # Add to collection
            self.collections[self.USER_QUERIES_COLLECTION].add(
                ids=[query_id],
                documents=[document],
                metadatas=[metadata]
            )
            
            self.logger.info(f"Stored user query for session {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store user query: {e}")
            return False
    
    def get_user_context(self, session_id: str, n_results: int = 5) -> List[SearchResult]:
        """Get recent user interactions for context"""
        try:
            # Search for queries from this session
            results = self.collections[self.USER_QUERIES_COLLECTION].get(
                where={"session_id": session_id},
                include=['documents', 'metadatas']
            )
            
            # Convert to SearchResult objects and sort by timestamp
            search_results = []
            if results['ids']:
                for i in range(len(results['ids'])):
                    search_result = SearchResult(
                        id=results['ids'][i],
                        document=results['documents'][i],
                        metadata=results['metadatas'][i],
                        distance=0.0,
                        score=1.0
                    )
                    search_results.append(search_result)
                
                # Sort by timestamp (most recent first)
                search_results.sort(
                    key=lambda x: x.metadata.get('timestamp', ''),
                    reverse=True
                )
                
                # Return only the most recent n_results
                search_results = search_results[:n_results]
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Failed to get user context for session {session_id}: {e}")
            return []
    
    # === UTILITY METHODS ===
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build ChromaDB where clause from filters"""
        where_clause = {}
        
        # Handle simple equality filters
        for key, value in filters.items():
            if isinstance(value, (str, int, float, bool)):
                where_clause[key] = value
            elif isinstance(value, list):
                # Handle list filters (e.g., category in ['web', 'frontend'])
                where_clause[key] = {"$in": value}
        
        return where_clause
    
    def migrate_from_json(self, json_file_path: str) -> Tuple[int, int]:
        """Migrate existing JSON library data to ChromaDB"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            success_count = 0
            total_count = len(json_data)
            
            for lib_key, lib_info in json_data.items():
                # Convert JSON data to LibraryData object
                library_data = self._json_to_library_data(lib_info)
                
                if self.add_library(library_data):
                    success_count += 1
            
            self.logger.info(f"Migration completed: {success_count}/{total_count} libraries migrated")
            return success_count, total_count
            
        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            return 0, 0
    
    def _json_to_library_data(self, lib_info: Dict[str, Any]) -> LibraryData:
        """Convert JSON library info to LibraryData object with enhanced data"""
        
        # Enhanced data based on library name
        enhanced_data = self._get_enhanced_library_data(lib_info['name'])
        
        return LibraryData(
            name=lib_info['name'],
            category=lib_info['category'],
            language=lib_info['language'],
            description=lib_info['description'],
            license=lib_info['license'],
            popularity=lib_info['popularity'],
            alternatives=lib_info.get('alternatives', []),
            use_cases=enhanced_data.get('use_cases', [f"{lib_info['category']} development"]),
            pros=enhanced_data.get('pros', [f"Popular {lib_info['language']} library"]),
            cons=enhanced_data.get('cons', ["Learning curve required"]),
            ideal_for=enhanced_data.get('ideal_for', f"Projects requiring {lib_info['category'].lower()}"),
            avoid_if=enhanced_data.get('avoid_if', "Incompatible with project requirements"),
            learning_curve=enhanced_data.get('learning_curve', 'medium'),
            performance_rating=enhanced_data.get('performance_rating', 4),
            community_size=lib_info['popularity'].lower(),
            documentation_quality=enhanced_data.get('documentation_quality', 'good'),
            github_stars=enhanced_data.get('github_stars', 0),
            weekly_downloads=enhanced_data.get('weekly_downloads', 0)
        )
    
    def _get_enhanced_library_data(self, library_name: str) -> Dict[str, Any]:
        """Get enhanced data for specific libraries"""
        
        enhanced_data_map = {
            "React": {
                "use_cases": ["Single Page Applications", "Enterprise web apps", "Component libraries", "Mobile apps with React Native"],
                "pros": ["Large ecosystem", "Component reusability", "Strong community", "Excellent tooling", "TypeScript support"],
                "cons": ["Steep learning curve", "Frequent updates", "Tooling complexity", "Large bundle size"],
                "ideal_for": "Large teams building complex interactive UIs with component reusability",
                "avoid_if": "Simple static websites, tight deadlines, or teams new to JavaScript",
                "learning_curve": "medium-high",
                "performance_rating": 4,
                "documentation_quality": "excellent",
                "github_stars": 220000,
                "weekly_downloads": 18000000
            },
            "Vue.js": {
                "use_cases": ["Progressive enhancement", "Rapid prototyping", "Small to medium web apps", "Beginner-friendly projects"],
                "pros": ["Gentle learning curve", "Progressive framework", "Excellent documentation", "Small bundle size"],
                "cons": ["Smaller ecosystem than React", "Less enterprise adoption", "Fewer job opportunities"],
                "ideal_for": "Teams wanting rapid development with good developer experience",
                "avoid_if": "Very large enterprise applications requiring extensive ecosystem",
                "learning_curve": "low-medium",
                "performance_rating": 5,
                "documentation_quality": "excellent",
                "github_stars": 207000,
                "weekly_downloads": 4200000
            },
            "Django": {
                "use_cases": ["Content management", "E-commerce platforms", "Social networks", "Admin interfaces"],
                "pros": ["Batteries included", "Built-in security", "Admin panel", "ORM included", "Rapid development"],
                "cons": ["Monolithic architecture", "Overkill for simple apps", "ORM limitations", "Template system"],
                "ideal_for": "Content-heavy websites and applications requiring rapid development",
                "avoid_if": "Microservices architecture, real-time applications, or API-only backends",
                "learning_curve": "medium",
                "performance_rating": 4,
                "documentation_quality": "excellent",
                "github_stars": 78000,
                "weekly_downloads": 1800000
            },
            "Flask": {
                "use_cases": ["APIs", "Microservices", "Custom architectures", "Learning web development"],
                "pros": ["Minimalist design", "Flexibility", "Easy to learn", "Modular extensions"],
                "cons": ["Manual configuration", "No built-in features", "Architectural decisions required"],
                "ideal_for": "APIs, microservices, and custom architectures where flexibility is key",
                "avoid_if": "Rapid prototyping needs or teams preferring opinionated structure",
                "learning_curve": "low-medium",
                "performance_rating": 5,
                "documentation_quality": "good",
                "github_stars": 67000,
                "weekly_downloads": 8500000
            },
            "Express.js": {
                "use_cases": ["REST APIs", "Real-time applications", "Microservices", "Web backends"],
                "pros": ["Fast performance", "Extensive middleware", "Large ecosystem", "Industry standard"],
                "cons": ["Minimal structure", "No built-in security", "Callback complexity", "Manual error handling"],
                "ideal_for": "Node.js APIs and real-time applications requiring high performance",
                "avoid_if": "CPU-intensive tasks or teams without JavaScript experience",
                "learning_curve": "low-medium",
                "performance_rating": 5,
                "documentation_quality": "good",
                "github_stars": 65000,
                "weekly_downloads": 22000000
            }
        }
        
        return enhanced_data_map.get(library_name, {})
    
    def initialize_mock_data(self) -> bool:
        """Initialize the database with comprehensive mock data"""
        try:
            # First migrate existing JSON data
            if os.path.exists("library_database.json"):
                success_count, total_count = self.migrate_from_json("library_database.json")
                self.logger.info(f"Migrated {success_count}/{total_count} libraries from JSON")
            
            # Add comprehensive FAQ data
            self._add_mock_faqs()
            
            self.logger.info("Mock data initialization completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize mock data: {e}")
            return False
    
    def _add_mock_faqs(self):
        """Add comprehensive FAQ data"""
        faqs = [
            {
                "question": "What's the difference between React and Vue.js?",
                "answer": "React has a steeper learning curve but larger ecosystem and job market. Vue.js is more beginner-friendly with gentler learning curve and excellent documentation. React is better for large teams and enterprise applications, while Vue.js excels in rapid prototyping and progressive enhancement.",
                "category": "comparison",
                "topic": "frontend_frameworks",
                "related_libraries": ["react", "vue"]
            },
            {
                "question": "Should I choose Django or Flask for my Python web project?",
                "answer": "Choose Django for content-heavy websites, admin interfaces, and rapid development with built-in features. Choose Flask for APIs, microservices, and when you need maximum flexibility and control over your architecture.",
                "category": "comparison",
                "topic": "python_frameworks",
                "related_libraries": ["django", "flask"]
            },
            {
                "question": "What are the main advantages of using a frontend framework?",
                "answer": "Frontend frameworks provide component reusability, better state management, improved developer experience with tooling, easier testing, better code organization, and often better performance through optimizations like virtual DOM.",
                "category": "general",
                "topic": "frontend_frameworks"
            },
            {
                "question": "How do I choose between different JavaScript frameworks?",
                "answer": "Consider your team's experience, project complexity, performance requirements, ecosystem needs, learning curve, and long-term maintenance. React for large teams, Vue.js for balanced approach, Angular for enterprise, Svelte for performance.",
                "category": "decision_making",
                "topic": "javascript_frameworks"
            },
            {
                "question": "What makes a library or framework enterprise-ready?",
                "answer": "Enterprise readiness includes: stable long-term support, strong security track record, comprehensive documentation, large community, professional support options, proven scalability, regular updates, and compatibility with enterprise tools.",
                "category": "enterprise",
                "topic": "evaluation_criteria"
            }
        ]
        
        for faq in faqs:
            self.add_faq(
                question=faq["question"],
                answer=faq["answer"],
                category=faq["category"],
                topic=faq.get("topic", ""),
                related_libraries=faq.get("related_libraries", [])
            )

# Global instance
_chromadb_manager = None

def get_chromadb_manager() -> ChromaDBManager:
    """Get or create global ChromaDB manager instance"""
    global _chromadb_manager
    if _chromadb_manager is None:
        _chromadb_manager = ChromaDBManager()
    return _chromadb_manager

def initialize_chromadb() -> bool:
    """Initialize ChromaDB with mock data"""
    try:
        manager = get_chromadb_manager()
        return manager.initialize_mock_data()
    except Exception as e:
        print(f"Failed to initialize ChromaDB: {e}")
        return False

if __name__ == "__main__":
    # Test the ChromaDB implementation
    logging.basicConfig(level=logging.INFO)
    
    print("Testing ChromaDB implementation...")
    
    # Initialize manager
    manager = ChromaDBManager()
    
    # Initialize with mock data
    if manager.initialize_mock_data():
        print("✓ Mock data initialized successfully")
        
        # Test library search
        results = manager.search_libraries("fast web framework")
        print(f"✓ Found {len(results)} libraries for 'fast web framework'")
        for result in results:
            print(f"  - {result.metadata['name']} (score: {result.score:.3f})")
        
        # Test FAQ search
        faq_results = manager.search_faqs("React vs Vue")
        print(f"✓ Found {len(faq_results)} FAQs for 'React vs Vue'")
        
        # Test stats
        stats = manager.get_collection_stats()
        print(f"✓ Collection stats: {stats}")
        
    else:
        print("✗ Failed to initialize mock data")