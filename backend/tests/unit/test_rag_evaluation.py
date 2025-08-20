import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.rag_evaluation import RAGEvaluator

print("RAG evaluation imports successful")

# Run evaluation
try:
    evaluator = RAGEvaluator()
    results = evaluator.run_comprehensive_evaluation()
    
    print("\nRAG Evaluation Results:")
    print(f"Success rate: {results['retrieval_performance']['successful_retrievals']}/{results['retrieval_performance']['total_queries']}")
    print(f"Average relevance: {results['retrieval_performance']['average_relevance_score']:.2f}")
    print(f"Total documents in vector DB: {results['system_health']['total_documents']}")
    
    print("\nRecommendations:")
    for rec in results['recommendations']:
        print(f"- {rec}")
    
    print("\nDetailed Query Results:")
    for result in results['retrieval_performance']['query_results']:
        print(f"  Query: {result['query']}")
        print(f"  Relevance: {result['relevance_score']:.2f}")
        print(f"  Retrieved: {result['retrieved_docs']} docs")
        print()
        
except Exception as e:
    print(f"Error: {e}")