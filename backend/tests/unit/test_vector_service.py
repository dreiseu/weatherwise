import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.vector_service import VectorService

print("✅ Vector service imports successful")

# Test adding and searching documents
try:
    vector_service = VectorService()
    
    # Add a test DRRM document
    test_doc = "During typhoon preparation, evacuate coastal areas and secure infrastructure."
    success = vector_service.add_document(
        text=test_doc,
        doc_id="test_typhoon_prep_001",
        metadata={"type": "typhoon", "category": "preparation"}
    )
    
    if success:
        print("✅ Document added successfully")
        
        # Test search
        results = vector_service.search("typhoon evacuation procedures")
        
        if results and len(results['documents'][0]) > 0:
            print(f"✅ Search found {len(results['documents'][0])} results")
            print(f"   Top result: {results['documents'][0][0][:50]}...")
        else:
            print("⚠️  No search results found")
    else:
        print("❌ Failed to add document")
        
    # Add more DRRM documents
    drrm_docs = [
        {
            "text": "PAGASA issues typhoon signals when sustained winds reach 39 km/h. Signal No. 1 means winds of 39-61 km/h expected in 36 hours.",
            "id": "pagasa_signals_001",
            "metadata": {"type": "typhoon", "source": "PAGASA", "category": "warning_system"}
        },
        {
            "text": "Flood-prone areas in Metro Manila include Marikina, Pasig River areas, and low-lying districts. Residents should evacuate when water reaches knee-deep levels.",
            "id": "metro_manila_flood_001", 
            "metadata": {"type": "flooding", "location": "Metro Manila", "category": "evacuation"}
        }
    ]

    print("\n📚 Adding more DRRM knowledge...")
    for doc in drrm_docs:
        success = vector_service.add_document(doc["text"], doc["id"], doc["metadata"])
        if success:
            print(f"✅ Added: {doc['id']}")

    # Test search with different queries
    test_queries = ["PAGASA warning signals", "Metro Manila flooding"]

    for query in test_queries:
        print(f"\n🔍 Searching: '{query}'")
        results = vector_service.search(query, n_results=2)
        if results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                print(f"   {i+1}. {doc[:60]}...")
    
except Exception as e:
    print(f"❌ Error: {e}")