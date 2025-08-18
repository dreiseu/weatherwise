import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.llm_service import LLMService

print("✅ LLM service imports successful")

# Test with mock data
try:
    llm_service = LLMService()
    
    # Test weather data
    weather_data = {
        "location": "Manila,PH",
        "temperature": 32.5,
        "humidity": 85,
        "wind_speed": 25,
        "pressure": 1010,
        "weather_condition": "Cloudy"
    }
    
    # Test context documents
    context_docs = [
        "High humidity above 85% indicates potential storm development",
        "Wind speeds above 20 km/h require monitoring for typhoon formation"
    ]
    
    # Generate analysis (will use fallback without API key)
    analysis = llm_service.generate_drrm_analysis(weather_data, context_docs)
    
    print("✅ LLM service test completed")
    print(f"Analysis result: {analysis[:50]}...")
    
except Exception as e:
    print(f"❌ Error: {e}")