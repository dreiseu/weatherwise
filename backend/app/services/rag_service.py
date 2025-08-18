"""
RAG Service for WeatherWise
Combines vector search with LLM generation for intelligent DRRM responses
"""

import logging
from typing import Dict, List, Optional
from .vector_service import VectorService
from .llm_service import LLMService

# Configure logging
logger = logging.getLogger(__name__)

class RAGService:
    """RAG service combining vector search and LLM generation."""
    
    def __init__(self):
        """Initialize RAG service."""
        self.vector_service = VectorService()
        self.llm_service = LLMService()
        logger.info("RAG service initialized")
    
    def generate_weather_analysis(self, weather_data: Dict, query: str) -> Dict:
        """Generate weather analysis using RAG approach."""
        
        # Step 1: Search for relevant DRRM knowledge
        search_results = self.vector_service.search(query, n_results=3)
        
        # Step 2: Extract relevant documents
        relevant_docs = []
        if search_results and search_results['documents'][0]:
            relevant_docs = search_results['documents'][0]
        
        # Step 3: Generate analysis using LLM with context
        analysis = self.llm_service.generate_drrm_analysis(weather_data, relevant_docs)
        
        return {
            "query": query,
            "weather_data": weather_data,
            "relevant_knowledge": relevant_docs,
            "analysis": analysis,
            "knowledge_sources": len(relevant_docs)
        }

if __name__ == "__main__":
    # Test the RAG service
    rag_service = RAGService()
    print("✅ RAG service working!")