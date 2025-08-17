"""
WeatherWise OpenWeather API Client
Handles all interactions with OpenWeather API
"""

import requests
import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone
import os
from dataclasses import dataclass
from ..core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class WeatherData:
    """Data class for weather information"""
    location: str
    latitude: float
    longitude: float
    temperature: float
    humidity: int
    wind_speed: float
    wind_direction: int
    pressure: float
    weather_condition: str
    weather_description: str
    visibility: float
    timestamp: str
    source: str = "openweather"


class WeatherAPIError(Exception):
    """Custom exception for weather API errors."""
    pass


class OpenWeatherService:
    """OpenWeather API service client."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the OpenWeather service.

        Args:
            api_key: OpenWeather API key. If None, reads from settings.
        """
        self.api_key = api_key or settings.OPENWEATHER_API_KEY
        if not self.api_key:
            raise WeatherAPIError("OpenWeather API key not provided")
        
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.timeout = 10 # seconds

        logger.info("OpenWeather service initialized")

    def get_current_weather(self, location: str, units: str = "metric") -> WeatherData:
        """Get current weather for a location.

        Args:
            location: Location string (e.g., "Manila, PH" or "lat,lon")
            units: Units for temperature (metric, imperial, kelvin)

        Returns:
            WeatherData object with current weather information

        Raises:
            WeatherAPIError: If API request fails
        """
        url = f"{self.base_url}/weather"
        params = {
            'q': location,
            'appid': self.api_key,
            'units': units
        }

        try:
            logger.info(f"Fetching current weather for {location}")
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            return self._parse_current_weather(data, location)
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise WeatherAPIError(f"Failed to fetch weather data: {e}")
        except KeyError as e:
            logger.error(f"Unexpected API response format: {e}")
            raise WeatherAPIError(f"Invalid API response format: {e}")
        
    def get_weather_by_coordinates(self, lat: float, lon: float, units: str = "metric") -> WeatherData:
        """Get current weather by coordinates.

        Args:
            lat: Latitude
            lon: Longitude
            units: Units for temperature

        Returns:
            WeatherData object with current weather information
        """
        url = f"{self.base_url}/weather"
        params = {
            'lat': lat,
            'long': lon,
            'appid': self.api_key,
            'units': units
        }

        try:
            logger.info(f"Fetching weather for coordinates {lat}, {lon}")
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            location = f"{data['name']}, {data['sys']['country']}"
            return self._parse_current_weather(data, location)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise WeatherAPIError(f"Failed to fetch weather data: {e}")
        
    def get_weather_forecast(self, location: str, days: int = 5, units: str = "metric") -> List[Dict]:
        """Get weather forecast for a location
        
        Args:
            location: Location string
            days: Number of days (1-5)
            units: Units for temperature

        Returns:
            List of forecast data dictionaries
        """
        if days > 5:
            logger.warning("Free tier limited to 5 days forecast, adjusting...")
            days = 5
        
        url = f"{self.base_url}/forecast"
        params = {
            'q': location,
            'appid': self.api_key,
            'units': units,
            'cnt': days * 8  # 8 forecasts per day (3-hour intervals)
        }
        
        try:
            logger.info(f"Fetching {days}-day forecast for {location}")
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_forecast_data(data)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Forecast API request failed: {e}")
            raise WeatherAPIError(f"Failed to fetch forecast data: {e}")
        
    def _parse_current_weather(self, data: Dict, location: str) -> WeatherData:
        """Parse OpenWeather API response into WeatherData object.

        Args:
            data: Raw API response data
            location: Location string

        Returns:
            WeatherData object
        """
        try:
            return WeatherData(
                location=location,
                latitude=data['coord']['lat'],
                longitude=data['coord']['lon'],
                temperature=data['main']['temp'],
                humidity=data['main']['humidity'],
                wind_speed=data['wind'].get('speed', 0),
                wind_direction=data['wind'].get('deg', 0),
                pressure=data['main']['pressure'],
                weather_condition=data['weather'][0]['main'],
                weather_description=data['weather'][0]['description'],
                visibility=data.get('visibility', 0) / 1000,  # Convert to km
                timestamp=datetime.now(timezone.utc).isoformat(),
                source="openweather"
            )
        except KeyError as e:
            logger.error(f"Missing required field in API response: {e}")
            raise WeatherAPIError(f"Invalid API response structure: {e}")
        
    def _parse_forecast_data(self, data: Dict) -> List[Dict]:
        """Parse forecast API response.
        
        Args:
            data: Raw forecast API response
            
        Returns:
            List of forecast dictionaries
        """
        forecasts = []
        
        for item in data['list']:
            forecast = {
                'datetime': item['dt_txt'],
                'temperature': item['main']['temp'],
                'temperature_min': item['main']['temp_min'],
                'temperature_max': item['main']['temp_max'],
                'humidity': item['main']['humidity'],
                'pressure': item['main']['pressure'],
                'weather_condition': item['weather'][0]['main'],
                'weather_description': item['weather'][0]['description'],
                'wind_speed': item['wind'].get('speed', 0),
                'wind_direction': item['wind'].get('deg', 0),
                'precipitation_probability': item.get('pop', 0) * 100  # Convert to percentage
            }
            forecasts.append(forecast)
        
        return forecasts
    
    def test_api_connection(self) -> bool:
        """Test if the API connection is working.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.get_current_weather("London,UK")
            logger.info("✅ API connection test successful")
            return True
        except WeatherAPIError:
            logger.error("❌ API connection test failed")
            return False
        
if __name__ == "__main__":
    # Test the weather service
    service = OpenWeatherService()

    try:
        # Test API connection
        if service.test_api_connection():
            print("Weather service is working!")
            
            # Get weather for Manila
            manila_weather = service.get_current_weather("Manila,PH")
            print(f"\nCurrent weather in {manila_weather.location}:")
            print(f"Temperature: {manila_weather.temperature}°C")
            print(f"Condition: {manila_weather.weather_description}")
            print(f"Humidity: {manila_weather.humidity}%")
            print(f"Wind: {manila_weather.wind_speed} m/s")
            
        else:
            print("Weather service test failed")
            
    except Exception as e:
        print(f"Error testing weather service: {e}")