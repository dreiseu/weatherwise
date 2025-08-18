"""
Load DRRM Knowledge into Vector Database
"""

import sys
from pathlib import Path

# Add paths
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.append(str(Path('..').resolve()))

from app.services.vector_service import VectorService
from data.drrm_knowledge import DRRM_DOCUMENTS

def load_all_drrm_knowledge():
    """Load all DRRM documents into vector database."""
    
    print("📚 Loading DRRM Knowledge into Vector Database...")
    
    vector_service = VectorService()
    
    success_count = 0
    for doc in DRRM_DOCUMENTS:
        success = vector_service.add_document(
            text=doc["text"],
            doc_id=doc["id"], 
            metadata=doc["metadata"]
        )
        
        if success:
            success_count += 1
            print(f"✅ Added: {doc['id']}")
        else:
            print(f"❌ Failed: {doc['id']}")
    
    print(f"\n📊 Summary: {success_count}/{len(DRRM_DOCUMENTS)} documents loaded successfully")
    return success_count == len(DRRM_DOCUMENTS)

if __name__ == "__main__":
    success = load_all_drrm_knowledge()
    if success:
        print("🎉 All DRRM knowledge loaded successfully!")
    else:
        print("⚠️  Some documents failed to load")