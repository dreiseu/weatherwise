"""
Integration tests for complete data pipeline
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, Mock

backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

os.environ['DATABASE_URL'] = 'postgresql://weatherwise:weatherwise_password@localhost:5432/weatherwise'
os.environ['OPENWEATHER_API_KEY'] = 'test_key_integration'
os.environ['DEBUG'] = 'true'


class TestDataPipelineIntegration(unittest.TestCase):
    """Integration tests for the complete data pipeline."""
    
    @patch('data_pipeline.OpenWeatherService')
    @patch('data_pipeline.create_engine')
    def test_pipeline_initialization(self, mock_engine, mock_weather_service):
        """Test pipeline initialization with all components."""
        # Mock database engine
        mock_engine.return_value = Mock()
        
        # Mock weather service
        mock_weather_service.return_value = Mock()
        
        # Import and test
        from data_pipeline import WeatherDataPipeline
        
        pipeline = WeatherDataPipeline()
        
        # Verify initialization
        self.assertIsNotNone(pipeline.DATABASE_URL)
        self.assertIsNotNone(pipeline.weather_service)
        self.assertIsNotNone(pipeline.validator)
        self.assertIsNotNone(pipeline.monitor)
    
    @patch('data_pipeline.OpenWeatherService')
    @patch('data_pipeline.create_engine')
    @patch('data_pipeline.sessionmaker')
    def test_pipeline_data_flow(self, mock_sessionmaker, mock_engine, mock_weather_service):
        """Test complete data flow through pipeline."""
        # Mock weather service response
        mock_weather_data = Mock()
        mock_weather_data.location = "Test Location"
        mock_weather_data.latitude = 14.0
        mock_weather_data.longitude = 120.0
        mock_weather_data.temperature = 25.0
        mock_weather_data.humidity = 80
        mock_weather_data.wind_speed = 10.0
        mock_weather_data.wind_direction = 180
        mock_weather_data.pressure = 1013.0
        mock_weather_data.weather_condition = "Clear"
        mock_weather_data.weather_description = "clear sky"
        mock_weather_data.visibility = 10.0
        mock_weather_data.timestamp = "2025-08-17T12:00:00Z"
        
        mock_weather_service_instance = Mock()
        mock_weather_service_instance.get_current_weather.return_value = mock_weather_data
        mock_weather_service.return_value = mock_weather_service_instance
        
        # Mock database
        mock_db_session = Mock()
        mock_sessionmaker.return_value = lambda: mock_db_session
        mock_engine.return_value = Mock()
        
        # Import and test
        from data_pipeline import WeatherDataPipeline
        
        pipeline = WeatherDataPipeline()
        result = pipeline.fetch_and_store_current_weather("Test Location")
        
        # Verify the flow
        self.assertTrue(result)
        mock_weather_service_instance.get_current_weather.assert_called_once_with("Test Location")
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()


class TestVisualizationIntegration(unittest.TestCase):
    """Integration tests for visualization with real data."""
    
    @patch('app.services.visualization.create_engine')
    @patch('app.services.visualization.pd.read_sql')
    def test_chart_generation_with_data(self, mock_read_sql, mock_engine):
        """Test chart generation with mock data."""
        import pandas as pd
        
        # Mock data
        mock_data = pd.DataFrame({
            'timestamp': ['2025-08-17 10:00:00', '2025-08-17 11:00:00'],
            'temperature': [25.0, 26.0],
            'weather_condition': ['Clear', 'Clouds']
        })
        mock_read_sql.return_value = mock_data
        
        # Mock engine
        mock_engine.return_value = Mock()
        
        from app.services.visualization import WeatherVisualization
        
        viz = WeatherVisualization()
        result = viz.create_temperature_trend("Test Location", days=1)
        
        # Should generate a chart file
        self.assertIsNotNone(result)
        self.assertTrue(result.endswith('.png'))


class TestSystemHealthCheck(unittest.TestCase):
    """Test overall system health and readiness."""
    
    def test_all_imports_work(self):
        """Test that all main modules can be imported."""
        try:
            from app.services.weather_service import OpenWeatherService
            from app.services.data_validator import WeatherDataValidator
            from app.services.monitoring import WeatherMonitoring
            from app.services.visualization import WeatherVisualization
            from data_pipeline import WeatherDataPipeline
            
            # If we get here, all imports worked
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Import failed: {e}")
    
    def test_environment_configuration(self):
        """Test environment configuration."""
        # Check required environment variables
        self.assertIn('DATABASE_URL', os.environ)
        self.assertIn('OPENWEATHER_API_KEY', os.environ)
        self.assertIn('DEBUG', os.environ)
        
        # Check they're not empty
        self.assertTrue(os.environ['DATABASE_URL'])
        self.assertTrue(os.environ['OPENWEATHER_API_KEY'])
    
    @patch('sys.path', [])
    def test_module_path_setup(self):
        """Test module path configuration."""
        # This tests that our path setup works correctly
        backend_dir = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(backend_dir))
        
        # Should be able to import our modules
        try:
            from app.services.weather_service import OpenWeatherService
            self.assertTrue(True)
        except ImportError:
            self.fail("Module path setup failed")


if __name__ == '__main__':
    print("🔧 Running Integration Tests")
    print("=" * 50)
    
    # Run the tests
    unittest.main(verbosity=2)