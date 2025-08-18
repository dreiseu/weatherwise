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
import time

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import our services and models
from app.services.weather_service import OpenWeatherService, WeatherData
from setup_database import CurrentWeather, WeatherForecast, Base
from app.services.data_validator import WeatherDataValidator
from app.services.monitoring import WeatherMonitoring

class WeatherDataPipeline:
    """Weather data collection and storage pipeline."""
    
    def __init__(self):
        """Initialize the data pipeline."""
        # Database setup
        self.DATABASE_URL = os.getenv('DATABASE_URL')
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required for production")
        self.engine = create_engine(self.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Weather service setup
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            raise ValueError("OPENWEATHER_API_KEY environment variable not found")
        self.weather_service = OpenWeatherService(api_key=api_key)
        
        # Data validation setup
        self.validator = WeatherDataValidator()

        # Monitoring setup
        self.monitor = WeatherMonitoring()

        print("Data pipeline with validation initialized")
    
    def fetch_and_store_current_weather(self, location: str) -> bool:
        """Fetch current weather and store in database with validation and monitoring.
        
        Args:
            location: Location string (e.g., "Manila,PH")
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()

        try:
            # Fetch weather data
            print(f"Fetching weather data for {location}...")
            weather_data = self.weather_service.get_current_weather(location)
            
            # Log API request timing
            api_time = time.time() - start_time
            self.monitor.log_api_requests(location, True, api_time)

            # Convert to dictionary for validation
            weather_dict = {
                'location': weather_data.location,
                'latitude': weather_data.latitude,
                'longitude': weather_data.longitude,
                'temperature': weather_data.temperature,
                'humidity': weather_data.humidity,
                'wind_speed': weather_data.wind_speed,
                'wind_direction': weather_data.wind_direction,
                'pressure': weather_data.pressure,
                'weather_condition': weather_data.weather_condition,
                'weather_description': weather_data.weather_description,
                'visibility': weather_data.visibility,
                'timestamp': weather_data.timestamp
            }

            # Validate the data
            print(f"Validating weather data for {location}...")
            validation_result = self.validator.validate_current_weather(weather_dict)

            # Log validation results
            self.monitor.log_validation_result(
                location, 
                validation_result.is_valid,
                validation_result.warnings,
                validation_result.errors
            )

            if not validation_result.is_valid:
                print(f"Data validation failed for {location}:")
                for error in validation_result.errors:
                    print(f"   • {error}")
                return False
            
            if validation_result.warnings:
                print(f"Data validation warnings for {location}:")
                for warning in validation_result.warnings:
                    print(f"   • {warning}")

            # Use cleaned data for storage
            cleaned_data = validation_result.cleaned_data
            print(f"Data validation passed for {location}")

            # Store in database
            db = self.SessionLocal()
            try:
                db_weather = CurrentWeather(
                    location=cleaned_data['location'],
                    latitude=cleaned_data['latitude'],
                    longitude=cleaned_data['longitude'],
                    temperature=cleaned_data['temperature'],
                    humidity=cleaned_data['humidity'],
                    wind_speed=cleaned_data['wind_speed'],
                    wind_direction=cleaned_data['wind_direction'],
                    pressure=cleaned_data['pressure'],
                    weather_condition=cleaned_data['weather_condition'],
                    weather_description=cleaned_data['weather_description'],
                    visibility=cleaned_data['visibility'],
                    timestamp=datetime.now(timezone.utc)
                )
                
                db.add(db_weather)
                db.commit()

                # Log successful database operation
                self.monitor.log_database_operation("insert", location, True, 1)

                print(f"   Validated weather data stored for {location}")
                print(f"   Temperature: {cleaned_data['temperature']}°C")
                print(f"   Condition: {cleaned_data['weather_description']}")
                print(f"   Humidity: {cleaned_data['humidity']}%")
                
                return True
            
            except Exception as db_error:
                # Log database error
                self.monitor.log_database_operation("insert", location, False, 0, str(db_error))
                raise db_error
                            
            finally:
                db.close()
                
        except Exception as e:
             # Log API request failure
            api_time = time.time() - start_time
            self.monitor.log_api_requests(location, False, api_time, str(e))
            print(f"Error in data pipeline: {e}")
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
                print(f"Stored {stored_count} forecast entries for {location}")
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error storing forecast data: {e}")
            return False
    
    def test_full_pipeline(self):
        """Test the complete data pipeline."""
        print("Testing WeatherWise Data Pipeline")
        print("=" * 50)
        
        # Test locations
        test_locations = ["Manila,PH", "Cebu,PH", "Davao,PH"]
        
        for location in test_locations:
            print(f"\nTesting pipeline for {location}")
            
            # Test current weather
            if self.fetch_and_store_current_weather(location):
                print(f"   Current weather: SUCCESS")
            else:
                print(f"   Current weather: FAILED")
            
            # Test forecast
            if self.fetch_and_store_forecast(location, 2):
                print(f"   Forecast data: SUCCESS")
            else:
                print(f"   Forecast data: FAILED")
        
        print("\nPipeline testing completed!")

        # Generate and display monitoring report
        print("\n" + self.monitor.get_performance_summary())


if __name__ == "__main__":
    # Run the data pipeline test
    pipeline = WeatherDataPipeline()
    pipeline.test_full_pipeline()