"""
Simple weather service test without environment file
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import weather service
from app.services.weather_service import OpenWeatherService

def test_weather_service():
    """Test the weather service with direct API key."""
    try:
        # Use API key directly
        api_key = "8f7d97e1cbdf20d5ac6ae5b9660cf2bf"
        
        service = OpenWeatherService(api_key=api_key)
        
        # Test API connection
        print("Testing weather service...")
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