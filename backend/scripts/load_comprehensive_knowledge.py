"""
Load Comprehensive DRRM Knowledge
Processes and loads detailed DRRM documents into vector database
"""

import sys
from pathlib import Path

# Add paths
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.append(str(backend_dir.parent))

from app.services.vector_service import VectorService
from scripts.process_documents import DocumentProcessor
from data.comprehensive_drrm import COMPREHENSIVE_DRRM_DOCS

def load_comprehensive_knowledge():
    """Load and process comprehensive DRRM documents."""
    
    print("Processing comprehensive DRRM knowledge...")
    
    vector_service = VectorService()
    processor = DocumentProcessor(chunk_size=400, overlap=50)
    
    total_chunks = 0
    success_count = 0
    
    for doc in COMPREHENSIVE_DRRM_DOCS:
        print(f"\nProcessing: {doc['id']}")
        
        # Process document into chunks
        chunks = processor.chunk_text(doc["text"], doc["id"], doc["metadata"])
        
        # Add each chunk to vector database
        for chunk in chunks:
            success = vector_service.add_document(
                text=chunk["text"],
                doc_id=chunk["id"],
                metadata=chunk["metadata"]
            )
            
            if success:
                success_count += 1
                print(f"  Added: {chunk['id']}")
            else:
                print(f"  Failed: {chunk['id']}")
            
            total_chunks += 1
    
    print(f"\nSummary: {success_count}/{total_chunks} chunks loaded successfully")
    return success_count == total_chunks

if __name__ == "__main__":
    success = load_comprehensive_knowledge()
    if success:
        print("Comprehensive DRRM knowledge loaded successfully!")
    else:
        print("Some chunks failed to load")