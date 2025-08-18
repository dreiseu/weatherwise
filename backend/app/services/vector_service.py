"""
Vector Database Service for WeatherWise
Handles document embeddings and similarity search for DRRM knowledge
"""

import chromadb
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class VectorService:
    """Vector database service using ChromaDB."""

    def __init__(self, persist_directory: str = "vector_db"):
        """Initialize vector service."""
        self.persist_directory = persist_directory

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Create or get collection for DRRM knowledge
        self.collection = self.client.get_or_create_collection(
            name="drrm_knowledge",
            metadata={"description": "DRRM protocols and disaster management knowledge"}
        )

        logger.info(f"Vector service initialized with {self.collection.count()} documents")
    
    def add_document(self, text: str, doc_id: str, metadata: Optional[Dict] = None):
        """Add a document to the vector database."""
        try:
            self.collection.add(
                documents=[text],
                ids=[doc_id],
                metadatas=[metadata or {}]
            )
            logger.info(f"Added document: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add document {doc_id}: {e}")
            return False
        
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for similar documents."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            logger.info(f"Search found {len(results['documents'][0])} results")
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

if __name__ == "__main__":
    # Test the service
    vector_service = VectorService()
    print("✅ Vector service working!")