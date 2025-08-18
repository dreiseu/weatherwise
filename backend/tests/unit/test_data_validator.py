"""
Unit tests for Data Validator
"""

import unittest
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.data_validator import WeatherDataValidator, ValidationResult


class TestWeatherDataValidator(unittest.TestCase):
    """Test cases for WeatherDataValidator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = WeatherDataValidator()
        
        self.valid_weather_data = {
            'location': 'Manila, PH',
            'latitude': 14.5995,
            'longitude': 120.9842,
            'temperature': 28.5,
            'humidity': 78,
            'pressure': 1013.25,
            'wind_speed': 15.2,
            'wind_direction': 180,
            'weather_condition': 'Clouds',
            'weather_description': 'partly cloudy',
            'visibility': 10.0
        }
    
    def test_validator_initialization(self):
        """Test validator initialization."""
        self.assertIsInstance(self.validator, WeatherDataValidator)
        self.assertIn('temperature', self.validator.VALIDATION_RANGES)
        self.assertIn('humidity', self.validator.VALIDATION_RANGES)
    
    def test_validate_current_weather_valid_data(self):
        """Test validation with valid data."""
        result = self.validator.validate_current_weather(self.valid_weather_data)
        
        self.assertIsInstance(result, ValidationResult)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertIsNotNone(result.cleaned_data)
        self.assertIn('validated_at', result.cleaned_data)
    
    def test_validate_current_weather_missing_required_fields(self):
        """Test validation with missing required fields."""
        incomplete_data = {
            'temperature': 25.0,
            'humidity': 60
            # Missing required fields: location, latitude, longitude, etc.
        }
        
        result = self.validator.validate_current_weather(incomplete_data)
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        self.assertIsNone(result.cleaned_data)
        
        # Check that missing fields are reported
        error_text = ' '.join(result.errors)
        self.assertIn('location', error_text)
        self.assertIn('latitude', error_text)
    
    def test_validate_current_weather_invalid_ranges(self):
        """Test validation with values outside valid ranges."""
        invalid_data = self.valid_weather_data.copy()
        invalid_data.update({
            'temperature': 150,  # Too high
            'humidity': 200,     # Too high
            'pressure': 500,     # Too low
            'latitude': 200,     # Invalid latitude
            'longitude': 400     # Invalid longitude
        })
        
        result = self.validator.validate_current_weather(invalid_data)
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        
        # Check specific errors
        error_text = ' '.join(result.errors)
        self.assertIn('temperature', error_text)
        self.assertIn('pressure', error_text)
        self.assertIn('latitude', error_text)
        self.assertIn('longitude', error_text)
    
    def test_validate_current_weather_warnings(self):
        """Test validation that generates warnings."""
        warning_data = self.valid_weather_data.copy()
        warning_data.update({
            'wind_speed': 250,  # Very high wind speed (should warn but not fail)
            'weather_condition': 'UnusualCondition'  # Unusual condition
        })
        
        result = self.validator.validate_current_weather(warning_data)
        
        self.assertTrue(result.is_valid)  # Should still be valid
        self.assertGreater(len(result.warnings), 0)  # But should have warnings
        
        warning_text = ' '.join(result.warnings)
        self.assertIn('wind_speed', warning_text.lower())
    
    def test_validate_forecast_data(self):
        """Test forecast data validation."""
        forecast_list = [
            self.valid_weather_data.copy(),
            self.valid_weather_data.copy()
        ]
        
        cleaned_forecasts, errors = self.validator.validate_forecast_data(forecast_list)
        
        self.assertEqual(len(cleaned_forecasts), 2)
        self.assertEqual(len(errors), 0)
    
    def test_detect_anomalies_temperature(self):
        """Test temperature anomaly detection."""
        # Create data with temperature anomaly
        weather_list = []
        for i in range(10):
            data = self.valid_weather_data.copy()
            data['temperature'] = 25.0 + i * 0.5  # Normal progression
            data['timestamp'] = f"2025-08-17T{i:02d}:00:00Z"
            weather_list.append(data)
        
        # Add anomalous temperature
        anomaly_data = self.valid_weather_data.copy()
        anomaly_data['temperature'] = 50.0  # Very high temperature
        anomaly_data['timestamp'] = "2025-08-17T10:00:00Z"
        weather_list.append(anomaly_data)
        
        anomalies = self.validator.detect_anomalies(weather_list, "Test Location")
        
        self.assertGreater(len(anomalies), 0)
        temp_anomalies = [a for a in anomalies if a['type'] == 'temperature_anomaly']
        self.assertGreater(len(temp_anomalies), 0)
        self.assertEqual(temp_anomalies[0]['value'], 50.0)
    
    def test_detect_anomalies_pressure_change(self):
        """Test pressure change anomaly detection."""
        weather_list = []
        for i in range(5):
            data = self.valid_weather_data.copy()
            data['pressure'] = 1013.0  # Stable pressure
            data['timestamp'] = f"2025-08-17T{i:02d}:00:00Z"
            weather_list.append(data)
        
        # Add rapid pressure drop
        drop_data = self.valid_weather_data.copy()
        drop_data['pressure'] = 990.0  # 23 hPa drop
        drop_data['timestamp'] = "2025-08-17T05:00:00Z"
        weather_list.append(drop_data)
        
        anomalies = self.validator.detect_anomalies(weather_list, "Test Location")
        
        pressure_anomalies = [a for a in anomalies if a['type'] == 'pressure_change_anomaly']
        self.assertGreater(len(pressure_anomalies), 0)
        self.assertGreater(pressure_anomalies[0]['pressure_change'], 20)
    
    def test_clean_duplicate_data(self):
        """Test duplicate data removal."""
        # Create duplicate entries
        weather_list = [
            self.valid_weather_data.copy(),
            self.valid_weather_data.copy(),  # Duplicate
            self.valid_weather_data.copy()   # Another duplicate
        ]
        
        # Add timestamps
        for i, data in enumerate(weather_list):
            data['timestamp'] = f"2025-08-17T12:{i:02d}:00Z"  # Close timestamps
        
        cleaned = self.validator.clean_duplicate_data(weather_list, time_threshold_minutes=10)
        
        self.assertLess(len(cleaned), len(weather_list))  # Should remove duplicates
        self.assertGreater(len(cleaned), 0)  # But keep at least one
    
    def test_data_cleaning_and_normalization(self):
        """Test data cleaning and normalization."""
        messy_data = self.valid_weather_data.copy()
        messy_data.update({
            'location': '  Manila, PH  ',  # Extra spaces
            'weather_description': '  PARTLY CLOUDY  ',  # Uppercase with spaces
            'humidity': '78',  # String instead of number
            'temperature': '28.5'  # String instead of number
        })
        
        result = self.validator.validate_current_weather(messy_data)
        
        self.assertTrue(result.is_valid)
        cleaned = result.cleaned_data
        
        # Check cleaning
        self.assertEqual(cleaned['location'], 'Manila, PH')  # Spaces trimmed
        self.assertEqual(cleaned['weather_description'], 'partly cloudy')  # Lowercase, trimmed
        self.assertIsInstance(cleaned['humidity'], (int, float))  # Converted to number
        self.assertIsInstance(cleaned['temperature'], (int, float))  # Converted to number


if __name__ == '__main__':
    unittest.main(verbosity=2)