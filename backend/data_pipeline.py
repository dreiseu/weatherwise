"""
WeatherWise Data Pipeline
Fetches weather data and stores in database
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import our services and models
from app.services.weather_service import OpenWeatherService, WeatherData
from setup_database import CurrentWeather, WeatherForecast, Base

class WeatherDataPipeline:
    """Weather data collection and storage pipeline."""
    
    def __init__(self):
        """Initialize the data pipeline."""
        # Database setup
        self.DATABASE_URL = "postgresql://weatherwise:weatherwise_password@localhost:5432/weatherwise"
        self.engine = create_engine(self.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Weather service setup
        self.weather_service = OpenWeatherService(api_key="8f7d97e1cbdf20d5ac6ae5b9660cf2bf")
        
        print("✅ Data pipeline initialized")
    
    def fetch_and_store_current_weather(self, location: str) -> bool:
        """Fetch current weather and store in database.
        
        Args:
            location: Location string (e.g., "Manila,PH")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Fetch weather data
            print(f"🌤️ Fetching weather data for {location}...")
            weather_data = self.weather_service.get_current_weather(location)
            
            # Store in database
            db = self.SessionLocal()
            try:
                db_weather = CurrentWeather(
                    location=weather_data.location,
                    latitude=weather_data.latitude,
                    longitude=weather_data.longitude,
                    temperature=weather_data.temperature,
                    humidity=weather_data.humidity,
                    wind_speed=weather_data.wind_speed,
                    wind_direction=weather_data.wind_direction,
                    pressure=weather_data.pressure,
                    weather_condition=weather_data.weather_condition,
                    weather_description=weather_data.weather_description,
                    visibility=weather_data.visibility,
                    timestamp=datetime.now(timezone.utc)
                )
                
                db.add(db_weather)
                db.commit()
                
                print(f"✅ Weather data stored for {location}")
                print(f"   Temperature: {weather_data.temperature}°C")
                print(f"   Condition: {weather_data.weather_description}")
                print(f"   Humidity: {weather_data.humidity}%")
                
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ Error in data pipeline: {e}")
            return False
    
    def fetch_and_store_forecast(self, location: str, days: int = 3) -> bool:
        """Fetch forecast data and store in database.
        
        Args:
            location: Location string
            days: Number of days to forecast
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"📅 Fetching {days}-day forecast for {location}...")
            forecast_data = self.weather_service.get_weather_forecast(location, days)
            
            db = self.SessionLocal()
            try:
                stored_count = 0
                for forecast in forecast_data:
                    db_forecast = WeatherForecast(
                        location=location,
                        latitude=0,  # We'll need to get coordinates separately
                        longitude=0,
                        forecast_date=datetime.fromisoformat(forecast['datetime'].replace(' ', 'T')),
                        temperature=forecast['temperature'],
                        temperature_min=forecast['temperature_min'],
                        temperature_max=forecast['temperature_max'],
                        humidity=forecast['humidity'],
                        wind_speed=forecast['wind_speed'],
                        wind_direction=forecast['wind_direction'],
                        pressure=forecast['pressure'],
                        weather_condition=forecast['weather_condition'],
                        weather_description=forecast['weather_description'],
                        precipitation_probability=int(forecast['precipitation_probability'])
                    )
                    
                    db.add(db_forecast)
                    stored_count += 1
                
                db.commit()
                print(f"✅ Stored {stored_count} forecast entries for {location}")
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ Error storing forecast data: {e}")
            return False
    
    def test_full_pipeline(self):
        """Test the complete data pipeline."""
        print("🚀 Testing WeatherWise Data Pipeline")
        print("=" * 50)
        
        # Test locations
        test_locations = ["Manila,PH", "Cebu,PH", "Davao,PH"]
        
        for location in test_locations:
            print(f"\n📍 Testing pipeline for {location}")
            
            # Test current weather
            if self.fetch_and_store_current_weather(location):
                print(f"   ✅ Current weather: SUCCESS")
            else:
                print(f"   ❌ Current weather: FAILED")
            
            # Test forecast
            if self.fetch_and_store_forecast(location, 2):
                print(f"   ✅ Forecast data: SUCCESS")
            else:
                print(f"   ❌ Forecast data: FAILED")
        
        print("\n🎉 Pipeline testing completed!")


if __name__ == "__main__":
    # Run the data pipeline test
    pipeline = WeatherDataPipeline()
    pipeline.test_full_pipeline()