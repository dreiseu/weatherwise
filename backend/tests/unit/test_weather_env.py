"""
Test script for weather service with environment loading
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path (go up 2 levels from tests/unit)
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path=backend_dir / ".." / ".env")  # .env is in project root

# Now import our weather service
from app.services.weather_service import OpenWeatherService

def test_weather_service():
    """Test the weather service."""
    try:
        # Create service with API key from environment
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            print("❌ OPENWEATHER_API_KEY not found in environment")
            return
        
        service = OpenWeatherService(api_key=api_key)
        
        # Test API connection
        if service.test_api_connection():
            print("✅ Weather service is working!")
            
            # Get weather for Manila
            manila_weather = service.get_current_weather("Manila,PH")
            print(f"\n🌤️ Current weather in {manila_weather.location}:")
            print(f"Temperature: {manila_weather.temperature}°C")
            print(f"Condition: {manila_weather.weather_description}")
            print(f"Humidity: {manila_weather.humidity}%")
            print(f"Wind: {manila_weather.wind_speed} m/s")
            
        else:
            print("❌ Weather service test failed")
            
    except Exception as e:
        print(f"Error testing weather service: {e}")

if __name__ == "__main__":
    test_weather_service()