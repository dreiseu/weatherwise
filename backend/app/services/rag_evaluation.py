"""
RAG Evaluation Service
Measures and improves RAG system performance
"""

import logging
from typing import Dict, List, Tuple
from .vector_service import VectorService
from .llm_service import LLMService

logger = logging.getLogger(__name__)

class RAGEvaluator:
    """Evaluate and optimize RAG system performance."""
    
    def __init__(self):
        """Initialize RAG evaluator."""
        self.vector_service = VectorService()
        self.llm_service = LLMService()
        logger.info("RAG evaluator initialized")
    
    def evaluate_retrieval_quality(self, test_queries: List[Dict]) -> Dict:
        """Evaluate retrieval quality with test queries."""
        
        results = {
            "total_queries": len(test_queries),
            "successful_retrievals": 0,
            "average_relevance_score": 0.0,
            "query_results": []
        }
        
        total_relevance = 0.0
        
        for query_data in test_queries:
            query = query_data["query"]
            expected_topics = query_data.get("expected_topics", [])
            
            # Perform search
            search_results = self.vector_service.search(query, n_results=3)
            
            if search_results and search_results['documents'][0]:
                results["successful_retrievals"] += 1
                
                # Calculate relevance score (simplified)
                relevance_score = self._calculate_relevance(
                    search_results['documents'][0], 
                    expected_topics
                )
                total_relevance += relevance_score
                
                results["query_results"].append({
                    "query": query,
                    "retrieved_docs": len(search_results['documents'][0]),
                    "relevance_score": relevance_score,
                    "top_result_preview": search_results['documents'][0][0][:100] + "..."
                })
            else:
                results["query_results"].append({
                    "query": query,
                    "retrieved_docs": 0,
                    "relevance_score": 0.0,
                    "error": "No results found"
                })
        
        if results["successful_retrievals"] > 0:
            results["average_relevance_score"] = total_relevance / results["successful_retrievals"]
        
        return results
    
    def _calculate_relevance(self, retrieved_docs: List[str], expected_topics: List[str]) -> float:
        """Calculate relevance score for retrieved documents."""
        
        if not expected_topics:
            return 1.0  # Default score if no expected topics specified
        
        relevance_scores = []
        
        for doc in retrieved_docs:
            doc_lower = doc.lower()
            topic_matches = sum(1 for topic in expected_topics if topic.lower() in doc_lower)
            doc_score = topic_matches / len(expected_topics)
            relevance_scores.append(doc_score)
        
        return sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
    
    def run_comprehensive_evaluation(self) -> Dict:
        """Run comprehensive RAG system evaluation."""
        
        # Test queries with expected topics
        test_queries = [
            {
                "query": "typhoon evacuation procedures",
                "expected_topics": ["evacuation", "typhoon", "signal"]
            },
            {
                "query": "earthquake building safety",
                "expected_topics": ["earthquake", "building", "safety", "1992"]
            },
            {
                "query": "flood management Metro Manila",
                "expected_topics": ["flood", "manila", "marikina", "evacuation"]
            },
            {
                "query": "volcanic alert levels",
                "expected_topics": ["volcanic", "alert", "phivolcs", "eruption"]
            },
            {
                "query": "NDRRMC organization structure",
                "expected_topics": ["ndrrmc", "organization", "coordination"]
            }
        ]
        
        print("Running comprehensive RAG evaluation...")
        
        retrieval_results = self.evaluate_retrieval_quality(test_queries)
        
        evaluation_summary = {
            "retrieval_performance": retrieval_results,
            "system_health": {
                "vector_db_status": "operational",
                "llm_service_status": "operational" if self.llm_service.api_key else "limited",
                "total_documents": self.vector_service.collection.count()
            },
            "recommendations": self._generate_recommendations(retrieval_results)
        }
        
        return evaluation_summary
    
    def _generate_recommendations(self, retrieval_results: Dict) -> List[str]:
        """Generate recommendations for RAG improvement."""
        
        recommendations = []
        
        success_rate = retrieval_results["successful_retrievals"] / retrieval_results["total_queries"]
        avg_relevance = retrieval_results["average_relevance_score"]
        
        if success_rate < 0.9:
            recommendations.append("Consider expanding knowledge base coverage")
        
        if avg_relevance < 0.7:
            recommendations.append("Improve document chunking strategy for better relevance")
        
        if avg_relevance > 0.8:
            recommendations.append("RAG retrieval quality is good")
        
        recommendations.append(f"Current retrieval success rate: {success_rate:.1%}")
        recommendations.append(f"Average relevance score: {avg_relevance:.2f}")
        
        return recommendations

if __name__ == "__main__":
    evaluator = RAGEvaluator()
    results = evaluator.run_comprehensive_evaluation()
    
    print("\nRAG Evaluation Results:")
    print(f"Success rate: {results['retrieval_performance']['successful_retrievals']}/{results['retrieval_performance']['total_queries']}")
    print(f"Average relevance: {results['retrieval_performance']['average_relevance_score']:.2f}")
    print("\nRecommendations:")
    for rec in results['recommendations']:
        print(f"- {rec}")