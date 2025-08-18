"""
Unit tests for Weather Service
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.weather_service import OpenWeatherService, WeatherData, WeatherAPIError
os.environ['OPENWEATHER_API_KEY'] = ''

class TestOpenWeatherService(unittest.TestCase):
    """Test cases for OpenWeatherService."""

    def setUp(self):
        """Setup test fixtures."""
        self.api_key = "test_api_key_12345"
        self.service = OpenWeatherService(api_key=self.api_key)

        # Mock response data
        self.mock_response_data = {
            'name': 'Manila',
            'sys': {'country': 'PH'},
            'coord': {'lat': 14.5995, 'lon': 120.9842},
            'main': {
                'temp': 28.5,
                'humidity': 78,
                'pressure': 1013.25
            },
            'wind': {'speed': 15.2, 'deg': 180},
            'weather': [
                {'main': 'Clouds', 'description': 'partly cloudy'}
            ],
            'visibility': 10000
        }
    
    def test_initialization(self):
        """Test service initialization."""
        self.assertEqual(self.service.api_key, self.api_key)
        self.assertEqual(self.service.base_url, "http://api.openweathermap.org/data/2.5")
        self.assertEqual(self.service.timeout, 10)
    
    def test_initialization_no_api_key(self):
        """Test initialization without API key raises error."""
        # Test with None
        with self.assertRaises(WeatherAPIError):
            OpenWeatherService(api_key=None)
        
        # Test with empty string
        with self.assertRaises(WeatherAPIError):
            OpenWeatherService(api_key="")
    
    @patch('app.services.weather_service.requests.get')
    def test_get_current_weather_success(self, mock_get):
        """Test successful weather data retrieval."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = self.mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test the method
        result = self.service.get_current_weather("Manila,PH")
        
        # Assertions
        self.assertIsInstance(result, WeatherData)
        self.assertEqual(result.location, "Manila,PH")
        self.assertEqual(result.temperature, 28.5)
        self.assertEqual(result.humidity, 78)
        self.assertEqual(result.pressure, 1013.25)
        self.assertEqual(result.weather_condition, "Clouds")
        
        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn("'q': 'Manila,PH'", str(call_args))
        self.assertIn(self.api_key, str(call_args))
    
    @patch('app.services.weather_service.requests.get')
    def test_get_current_weather_api_error(self, mock_get):
        """Test API error handling."""
       # Mock failed response
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("API Error")
        
        # Test error handling
        with self.assertRaises(WeatherAPIError):
            self.service.get_current_weather("InvalidLocation")
    
    @patch('app.services.weather_service.requests.get')
    def test_get_weather_by_coordinates(self, mock_get):
        """Test weather retrieval by coordinates."""
        mock_response = Mock()
        mock_response.json.return_value = self.mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.service.get_weather_by_coordinates(14.5995, 120.9842)
        
        self.assertIsInstance(result, WeatherData)
        self.assertEqual(result.latitude, 14.5995)
        self.assertEqual(result.longitude, 120.9842)
    
    @patch('app.services.weather_service.requests.get')
    def test_get_weather_forecast(self, mock_get):
        """Test forecast data retrieval."""
        mock_forecast_data = {
            'list': [
                {
                    'dt_txt': '2025-08-17 12:00:00',
                    'main': {'temp': 29.0, 'temp_min': 28.0, 'temp_max': 30.0, 
                            'humidity': 75, 'pressure': 1012},
                    'weather': [{'main': 'Rain', 'description': 'light rain'}],
                    'wind': {'speed': 12.5, 'deg': 200},
                    'pop': 0.8
                }
            ]
        }
        
        mock_response = Mock()
        mock_response.json.return_value = mock_forecast_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.service.get_weather_forecast("Manila,PH", days=1)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['temperature'], 29.0)
        self.assertEqual(result[0]['weather_condition'], 'Rain')
    
    def test_parse_current_weather(self):
        """Test weather data parsing."""
        result = self.service._parse_current_weather(self.mock_response_data, "Manila,PH")
        
        self.assertIsInstance(result, WeatherData)
        self.assertEqual(result.location, "Manila,PH")
        self.assertEqual(result.temperature, 28.5)
        self.assertEqual(result.humidity, 78)
        self.assertEqual(result.wind_speed, 15.2)
        self.assertEqual(result.visibility, 10.0)  # Converted from meters to km
    
    def test_parse_current_weather_missing_fields(self):
        """Test parsing with missing fields."""
        incomplete_data = {
            'name': 'Test',
            'sys': {'country': 'XX'},
            'coord': {'lat': 0, 'lon': 0},
            'main': {'temp': 25}  # Missing other fields
        }
        
        with self.assertRaises(WeatherAPIError):
            self.service._parse_current_weather(incomplete_data, "Test")


class TestWeatherData(unittest.TestCase):
    """Test cases for WeatherData dataclass."""
    
    def test_weather_data_creation(self):
        """Test WeatherData object creation."""
        weather = WeatherData(
            location="Test Location",
            latitude=14.0,
            longitude=120.0,
            temperature=25.0,
            humidity=80,
            wind_speed=10.0,
            wind_direction=180,
            pressure=1013.0,
            weather_condition="Clear",
            weather_description="clear sky",
            visibility=10.0,
            timestamp="2025-08-17T12:00:00Z",
            source="test"
        )
        
        self.assertEqual(weather.location, "Test Location")
        self.assertEqual(weather.temperature, 25.0)
        self.assertEqual(weather.humidity, 80)
        self.assertEqual(weather.source, "test")


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)