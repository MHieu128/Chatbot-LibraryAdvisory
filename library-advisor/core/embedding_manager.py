import os
import json
import numpy as np
import faiss
import pickle
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from openai import AzureOpenAI
import tiktoken
from pathlib import Path

@dataclass
class EmbeddingDocument:
    """Represents a document with its embedding"""
    id: str
    content: str
    metadata: Dict
    embedding: Optional[np.ndarray] = None

@dataclass
class SearchResult:
    """Represents a search result"""
    document: EmbeddingDocument
    score: float
    rank: int

class EmbeddingManager:
    """Manages embeddings and FAISS vector database"""
    
    def __init__(self, 
                 api_key: str, 
                 endpoint: str, 
                 deployment: str,
                 faiss_db_path: str,
                 embedding_dimension: int = 1536):
        """
        Initialize embedding manager
        
        Args:
            api_key: Azure OpenAI API key for embeddings
            endpoint: Azure OpenAI endpoint
            deployment: Embedding model deployment name
            faiss_db_path: Path to store FAISS database
            embedding_dimension: Dimension of embeddings
        """
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version="2024-02-01",
            azure_endpoint=endpoint
        )
        self.deployment = deployment
        self.faiss_db_path = Path(faiss_db_path)
        self.embedding_dimension = embedding_dimension
        
        # Initialize tokenizer for token counting
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # FAISS index and metadata storage
        self.index = None
        self.documents: Dict[str, EmbeddingDocument] = {}
        
        # Create storage directory
        self.faiss_db_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing index if available
        self._load_index()
    
    def create_embeddings(self, texts: List[str], metadata_list: List[Dict] = None) -> List[EmbeddingDocument]:
        """
        Create embeddings for a list of texts
        
        Args:
            texts: List of texts to embed
            metadata_list: Optional metadata for each text
            
        Returns:
            List of EmbeddingDocument objects
        """
        if metadata_list is None:
            metadata_list = [{}] * len(texts)
        
        # Process texts in batches to handle API limits
        batch_size = 10
        documents = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_metadata = metadata_list[i:i + batch_size]
            
            try:
                # Create embeddings using Azure OpenAI
                response = self.client.embeddings.create(
                    input=batch_texts,
                    model=self.deployment
                )
                
                # Process results
                for j, embedding_data in enumerate(response.data):
                    doc_id = f"doc_{len(documents) + j}_{hash(batch_texts[j]) % 10000}"
                    
                    document = EmbeddingDocument(
                        id=doc_id,
                        content=batch_texts[j],
                        metadata=batch_metadata[j],
                        embedding=np.array(embedding_data.embedding, dtype=np.float32)
                    )
                    
                    documents.append(document)
                    
            except Exception as e:
                error_msg = str(e).lower()
                if "connection error" in error_msg or "connection" in error_msg:
                    print(f"❌ Connection Error (Batch {i//batch_size + 1}): Cannot connect to Azure OpenAI endpoint")
                    print("   Please check your AZURE_OPENAI_ENDPOINT in .env file")
                    print(f"   Current endpoint: {self.client._azure_endpoint}")
                elif "unauthorized" in error_msg or "401" in error_msg:
                    print(f"❌ Authentication Error (Batch {i//batch_size + 1}): Invalid API key")
                    print("   Please check your AZURE_OPENAI_API_KEY_EMBEDDING in .env file")
                elif "not found" in error_msg or "404" in error_msg:
                    print(f"❌ Deployment Error (Batch {i//batch_size + 1}): Model deployment not found")
                    print(f"   Please check your AZURE_OPENAI_EMBEDDING_DEPLOYMENT: {self.deployment}")
                else:
                    print(f"❌ Error creating embeddings for batch {i//batch_size + 1}: {e}")
                continue
        
        return documents
    
    def store_in_faiss(self, documents: List[EmbeddingDocument]) -> bool:
        """
        Store documents in FAISS index
        
        Args:
            documents: List of documents to store
            
        Returns:
            Success status
        """
        try:
            if not documents:
                return False
            
            # Initialize index if needed
            if self.index is None:
                self.index = faiss.IndexFlatIP(self.embedding_dimension)  # Inner product for cosine similarity
            
            # Prepare embeddings
            embeddings = np.array([doc.embedding for doc in documents])
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Add to index
            self.index.add(embeddings)
            
            # Store documents metadata
            for doc in documents:
                self.documents[doc.id] = doc
            
            # Save to disk
            self._save_index()
            
            print(f"Successfully stored {len(documents)} documents in FAISS index")
            return True
            
        except Exception as e:
            print(f"Error storing documents in FAISS: {e}")
            return False
    
    def search_similar_content(self, 
                             query: str, 
                             k: int = 5,
                             score_threshold: float = 0.5) -> List[SearchResult]:
        """
        Search for similar content using FAISS
        
        Args:
            query: Query text
            k: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results
        """
        if self.index is None or self.index.ntotal == 0:
            return []
        
        try:
            # Create query embedding
            query_docs = self.create_embeddings([query])
            if not query_docs:
                return []
            
            query_embedding = query_docs[0].embedding.reshape(1, -1)
            faiss.normalize_L2(query_embedding)
            
            # Search FAISS index
            scores, indices = self.index.search(query_embedding, k)
            
            # Prepare results
            results = []
            doc_list = list(self.documents.values())
            
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(doc_list) and score >= score_threshold:
                    result = SearchResult(
                        document=doc_list[idx],
                        score=float(score),
                        rank=i + 1
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error searching FAISS index: {e}")
            return []
    
    def update_vector_db(self, project_id: str, documents: List[EmbeddingDocument]) -> bool:
        """
        Update vector database for a specific project
        
        Args:
            project_id: Unique project identifier
            documents: New documents to add/update
            
        Returns:
            Success status
        """
        try:
            # Remove existing documents for this project
            self._remove_project_documents(project_id)
            
            # Add project_id to metadata
            for doc in documents:
                doc.metadata['project_id'] = project_id
            
            # Store new documents
            return self.store_in_faiss(documents)
            
        except Exception as e:
            print(f"Error updating vector database: {e}")
            return False
    
    def get_project_statistics(self, project_id: str) -> Dict:
        """
        Get statistics for a specific project
        
        Args:
            project_id: Project identifier
            
        Returns:
            Statistics dictionary
        """
        project_docs = [doc for doc in self.documents.values() 
                       if doc.metadata.get('project_id') == project_id]
        
        if not project_docs:
            return {}
        
        return {
            'total_documents': len(project_docs),
            'total_tokens': sum(len(self.tokenizer.encode(doc.content)) for doc in project_docs),
            'avg_document_length': np.mean([len(doc.content) for doc in project_docs]),
            'file_types': list(set(doc.metadata.get('file_type', 'unknown') for doc in project_docs))
        }
    
    def _remove_project_documents(self, project_id: str):
        """Remove all documents for a specific project"""
        # Note: FAISS doesn't support efficient deletion, so we rebuild the index
        remaining_docs = [doc for doc in self.documents.values() 
                         if doc.metadata.get('project_id') != project_id]
        
        if remaining_docs:
            # Rebuild index with remaining documents
            self.index = faiss.IndexFlatIP(self.embedding_dimension)
            embeddings = np.array([doc.embedding for doc in remaining_docs])
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings)
            
            # Update documents dictionary
            self.documents = {doc.id: doc for doc in remaining_docs}
        else:
            # Clear everything
            self.index = None
            self.documents = {}
    
    def _save_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            if self.index is not None:
                # Save FAISS index
                index_path = self.faiss_db_path / "faiss.index"
                faiss.write_index(self.index, str(index_path))
                
                # Save documents metadata
                metadata_path = self.faiss_db_path / "documents.pkl"
                with open(metadata_path, 'wb') as f:
                    pickle.dump(self.documents, f)
                
                print(f"FAISS index saved to {self.faiss_db_path}")
                
        except Exception as e:
            print(f"Error saving FAISS index: {e}")
    
    def _load_index(self):
        """Load FAISS index and metadata from disk"""
        try:
            index_path = self.faiss_db_path / "faiss.index"
            metadata_path = self.faiss_db_path / "documents.pkl"
            
            if index_path.exists() and metadata_path.exists():
                # Load FAISS index
                self.index = faiss.read_index(str(index_path))
                
                # Load documents metadata
                with open(metadata_path, 'rb') as f:
                    self.documents = pickle.load(f)
                
                print(f"Loaded FAISS index with {self.index.ntotal} documents")
            else:
                print("No existing FAISS index found, starting fresh")
                
        except Exception as e:
            print(f"Error loading FAISS index: {e}")
            self.index = None
            self.documents = {}
    
    def get_index_info(self) -> Dict:
        """Get information about the current index"""
        if self.index is None:
            return {
                'total_documents': 0,
                'index_size': 0,
                'embedding_dimension': self.embedding_dimension
            }
        
        return {
            'total_documents': self.index.ntotal,
            'index_size': len(self.documents),
            'embedding_dimension': self.embedding_dimension,
            'projects': list(set(doc.metadata.get('project_id', 'unknown') 
                               for doc in self.documents.values()))
        }
