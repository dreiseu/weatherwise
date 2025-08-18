"""
WeatherWise Data Validation and Cleaning Service
Ensures data quality and consistency
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    cleaned_data: Optional[Dict] = None


class WeatherDataValidator:
    """Validates and cleans weather data."""
    
    # Reasonable ranges for weather parameters
    VALIDATION_RANGES = {
        'temperature': (-50, 60),      # Celsius
        'humidity': (0, 100),          # Percentage
        'pressure': (800, 1200),       # hPa
        'wind_speed': (0, 200),        # km/h
        'wind_direction': (0, 360),    # Degrees
        'visibility': (0, 50),         # km
        'precipitation_probability': (0, 100)  # Percentage
    }
    
    def __init__(self):
        """Initialize the validator."""
        logger.info("Weather data validator initialized")
    
    def validate_current_weather(self, weather_data: Dict) -> ValidationResult:
        """Validate current weather data.
        
        Args:
            weather_data: Dictionary containing weather data
            
        Returns:
            ValidationResult with validation status and cleaned data
        """
        errors = []
        warnings = []
        cleaned_data = weather_data.copy()
        
        # Required fields check
        required_fields = [
            'location', 'latitude', 'longitude', 'temperature', 
            'humidity', 'pressure', 'weather_condition'
        ]
        
        for field in required_fields:
            if field not in weather_data or weather_data[field] is None:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        # Validate numeric ranges
        for param, (min_val, max_val) in self.VALIDATION_RANGES.items():
            if param in weather_data and weather_data[param] is not None:
                value = weather_data[param]
                
                if not isinstance(value, (int, float)):
                    try:
                        value = float(value)
                        cleaned_data[param] = value
                    except (ValueError, TypeError):
                        errors.append(f"Invalid {param}: must be numeric")
                        continue
                
                if value < min_val or value > max_val:
                    if param in ['temperature', 'pressure']:
                        errors.append(f"Invalid {param}: {value} outside range [{min_val}, {max_val}]")
                    else:
                        warnings.append(f"Unusual {param}: {value} outside typical range [{min_val}, {max_val}]")
                        # Clean extreme values for non-critical parameters
                        if value < min_val:
                            cleaned_data[param] = min_val
                        elif value > max_val:
                            cleaned_data[param] = max_val
        
        # Validate coordinates
        if 'latitude' in weather_data:
            lat = weather_data['latitude']
            if not (-90 <= lat <= 90):
                errors.append(f"Invalid latitude: {lat} must be between -90 and 90")
        
        if 'longitude' in weather_data:
            lon = weather_data['longitude']
            if not (-180 <= lon <= 180):
                errors.append(f"Invalid longitude: {lon} must be between -180 and 180")
        
        # Validate weather condition
        if 'weather_condition' in weather_data:
            condition = weather_data['weather_condition']
            valid_conditions = [
                'Clear', 'Clouds', 'Rain', 'Drizzle', 'Thunderstorm', 
                'Snow', 'Mist', 'Fog', 'Haze', 'Smoke', 'Dust', 'Sand'
            ]
            if condition not in valid_conditions:
                warnings.append(f"Unusual weather condition: {condition}")
        
        # Clean and normalize text fields
        if 'location' in cleaned_data:
            cleaned_data['location'] = str(cleaned_data['location']).strip()
        
        if 'weather_description' in cleaned_data:
            cleaned_data['weather_description'] = str(cleaned_data['weather_description']).strip().lower()
        
        # Add validation timestamp
        cleaned_data['validated_at'] = datetime.now(timezone.utc).isoformat()
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info(f"Weather data validation passed for {weather_data.get('location', 'unknown')}")
        else:
            logger.error(f"Weather data validation failed: {'; '.join(errors)}")
        
        if warnings:
            logger.warning(f"Weather data warnings: {'; '.join(warnings)}")
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            cleaned_data=cleaned_data if is_valid else None
        )
    
    def validate_forecast_data(self, forecast_list: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """Validate and clean forecast data.
        
        Args:
            forecast_list: List of forecast dictionaries
            
        Returns:
            Tuple of (cleaned_forecast_list, error_messages)
        """
        cleaned_forecasts = []
        all_errors = []
        
        for i, forecast in enumerate(forecast_list):
            result = self.validate_current_weather(forecast)
            
            if result.is_valid:
                cleaned_forecasts.append(result.cleaned_data)
            else:
                all_errors.extend([f"Forecast {i+1}: {error}" for error in result.errors])
        
        logger.info(f"Validated {len(cleaned_forecasts)}/{len(forecast_list)} forecast entries")
        
        return cleaned_forecasts, all_errors
    
    def detect_anomalies(self, weather_data_list: List[Dict], location: str) -> List[Dict]:
        """Detect anomalies in weather data series.
        
        Args:
            weather_data_list: List of weather data points
            location: Location identifier
            
        Returns:
            List of detected anomalies
        """
        if len(weather_data_list) < 5:
            return []  # Need minimum data points for anomaly detection
        
        anomalies = []
        
        # Extract temperature values
        temperatures = [data.get('temperature') for data in weather_data_list if data.get('temperature') is not None]
        
        if len(temperatures) >= 5:
            mean_temp = statistics.mean(temperatures)
            std_temp = statistics.stdev(temperatures) if len(temperatures) > 1 else 0
            
            # Detect temperature anomalies (values beyond 2 standard deviations)
            for i, data in enumerate(weather_data_list):
                temp = data.get('temperature')
                if temp is not None and std_temp > 0:
                    z_score = abs(temp - mean_temp) / std_temp
                    if z_score > 2:
                        anomalies.append({
                            'type': 'temperature_anomaly',
                            'location': location,
                            'value': temp,
                            'mean': round(mean_temp, 2),
                            'z_score': round(z_score, 2),
                            'timestamp': data.get('timestamp'),
                            'severity': 'high' if z_score > 3 else 'moderate'
                        })
        
        # Detect rapid pressure changes (indicator of severe weather)
        pressures = [(data.get('pressure'), data.get('timestamp')) for data in weather_data_list 
                    if data.get('pressure') is not None]
        
        for i in range(1, len(pressures)):
            if pressures[i][0] and pressures[i-1][0]:
                pressure_change = abs(pressures[i][0] - pressures[i-1][0])
                if pressure_change > 10:  # Rapid pressure change > 10 hPa
                    anomalies.append({
                        'type': 'pressure_change_anomaly',
                        'location': location,
                        'pressure_change': round(pressure_change, 2),
                        'current_pressure': pressures[i][0],
                        'previous_pressure': pressures[i-1][0],
                        'timestamp': pressures[i][1],
                        'severity': 'high' if pressure_change > 20 else 'moderate'
                    })
        
        if anomalies:
            logger.warning(f"Detected {len(anomalies)} anomalies for {location}")
        
        return anomalies
    
    def clean_duplicate_data(self, weather_data_list: List[Dict], time_threshold_minutes: int = 30) -> List[Dict]:
        """Remove duplicate weather data entries.
        
        Args:
            weather_data_list: List of weather data
            time_threshold_minutes: Time threshold for considering entries as duplicates
            
        Returns:
            List of deduplicated weather data
        """
        if not weather_data_list:
            return []
        
        # Sort by timestamp
        sorted_data = sorted(weather_data_list, key=lambda x: x.get('timestamp', ''))
        
        cleaned_data = [sorted_data[0]]  # Keep first entry
        
        for data in sorted_data[1:]:
            last_entry = cleaned_data[-1]
            
            # Check if entries are too similar (same location and close timestamp)
            if (data.get('location') == last_entry.get('location') and
                self._are_timestamps_close(data.get('timestamp'), last_entry.get('timestamp'), time_threshold_minutes)):
                
                # Keep the entry with more complete data
                if self._count_non_null_fields(data) > self._count_non_null_fields(last_entry):
                    cleaned_data[-1] = data
                # else keep the existing entry
            else:
                cleaned_data.append(data)
        
        removed_count = len(weather_data_list) - len(cleaned_data)
        if removed_count > 0:
            logger.info(f"🧹 Removed {removed_count} duplicate entries")
        
        return cleaned_data
    
    def _are_timestamps_close(self, ts1: str, ts2: str, threshold_minutes: int) -> bool:
        """Check if two timestamps are within threshold."""
        try:
            dt1 = datetime.fromisoformat(ts1.replace('Z', '+00:00'))
            dt2 = datetime.fromisoformat(ts2.replace('Z', '+00:00'))
            diff_minutes = abs((dt1 - dt2).total_seconds()) / 60
            return diff_minutes <= threshold_minutes
        except (ValueError, AttributeError):
            return False
    
    def _count_non_null_fields(self, data: Dict) -> int:
        """Count non-null fields in data dictionary."""
        return sum(1 for value in data.values() if value is not None)


# Example usage and testing
if __name__ == "__main__":
    validator = WeatherDataValidator()
    
    # Test with sample data
    sample_weather = {
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
    
    result = validator.validate_current_weather(sample_weather)
    print(f"Validation result: {result.is_valid}")
    if result.errors:
        print(f"Errors: {result.errors}")
    if result.warnings:
        print(f"Warnings: {result.warnings}")
    
    # Test with invalid data
    invalid_weather = {
        'location': 'Test Location',
        'temperature': 150,  # Invalid temperature
        'humidity': 200,     # Invalid humidity
        'pressure': 500      # Invalid pressure
    }
    
    result2 = validator.validate_current_weather(invalid_weather)
    print(f"\nInvalid data validation: {result2.is_valid}")
    print(f"Errors: {result2.errors}")