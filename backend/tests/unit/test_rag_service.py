import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.rag_service import RAGService

print("✅ RAG service imports successful")

# Test the RAG service
try:
    rag_service = RAGService()
    
    # Test weather data
    weather_data = {
        "location": "Manila,PH",
        "temperature": 32.5,
        "humidity": 85,
        "wind_speed": 25,
        "pressure": 1010,
        "weather_condition": "Cloudy"
    }
    
    # Test analysis
    result = rag_service.generate_weather_analysis(
        weather_data, 
        "typhoon preparation Manila high humidity"
    )
    
    print("✅ RAG analysis completed")
    print(f"   Query: {result['query']}")
    print(f"   Knowledge sources: {result['knowledge_sources']}")
    print(f"   Analysis: {result['analysis'][:80]}...")
    
    # Test different disaster scenarios
    test_scenarios = [
        {
            "weather": {"location": "Eastern Visayas", "wind_speed": 120, "weather_condition": "Typhoon"},
            "query": "storm surge evacuation procedures"
        },
        {
            "weather": {"location": "Metro Manila", "temperature": 42, "humidity": 60},
            "query": "heat index warnings dangerous temperatures"
        },
        {
            "weather": {"location": "Northern Luzon", "precipitation": "heavy", "weather_condition": "Rain"},
            "query": "landslide warning signs mountainous areas"
        }
    ]

    print("\n🧪 Testing different disaster scenarios:")
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n--- Scenario {i}: {scenario['query'][:30]}... ---")
        result = rag_service.generate_weather_analysis(scenario["weather"], scenario["query"])
        print(f"   Knowledge sources found: {result['knowledge_sources']}")
        print(f"   Analysis preview: {result['analysis'][:60]}...")

except Exception as e:
    print(f"❌ Error: {e}")