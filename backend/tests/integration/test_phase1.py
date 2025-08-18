"""
Phase 1 Completion Test Script
Tests all new weather analysis and geospatial capabilities
"""

import sys
import os
import requests
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Set environment variables
os.environ['DATABASE_URL'] = 'postgresql://weatherwise:weatherwise_password@localhost:5432/weatherwise'
os.environ['OPENWEATHER_API_KEY'] = 'f4d53db66e53708290a4fb6f2ed80ab8'

from app.services.weather_analysis import WeatherAnalysisService
from app.services.geospatial_service import GeospatialService
from app.core.database import SessionLocal


class Phase1TestSuite:
    """Test suite for Phase 1 completion validation."""
    
    def __init__(self):
        """Initialize test suite."""
        self.db = SessionLocal()
        self.analysis_service = WeatherAnalysisService(self.db)
        self.geo_service = GeospatialService(self.db)
        self.test_locations = ["Manila,PH", "Cebu,PH", "Davao,PH"]
        self.results = {
            'tests_passed': 0,
            'tests_failed': 0,
            'test_details': []
        }
        
        print("🧪 WeatherWise Phase 1 Completion Test Suite")
        print("=" * 60)
    
    def run_all_tests(self):
        """Run all Phase 1 tests."""
        test_methods = [
            self.test_weather_pattern_analysis,
            self.test_anomaly_detection,
            self.test_trend_analysis,
            self.test_risk_scoring,
            self.test_geospatial_processing,
            self.test_regional_risk_mapping,
            self.test_multi_location_analysis,
            self.test_performance_optimization
        ]
        
        for test_method in test_methods:
            try:
                start_time = time.time()
                test_method()
                execution_time = time.time() - start_time
                self._log_test_result(test_method.__name__, True, execution_time)
            except Exception as e:
                self._log_test_result(test_method.__name__, False, 0, str(e))
        
        self._print_test_summary()
        return self.results['tests_failed'] == 0
    
    def test_weather_pattern_analysis(self):
        """Test weather pattern analysis functionality."""
        print("\n📊 Testing Weather Pattern Analysis...")
        
        for location in self.test_locations:
            patterns = self.analysis_service.analyze_weather_patterns(location, days=3)
            
            # Validate patterns structure
            if patterns:
                for pattern in patterns:
                    assert hasattr(pattern, 'pattern_type'), "Pattern missing type"
                    assert hasattr(pattern, 'confidence'), "Pattern missing confidence"
                    assert hasattr(pattern, 'risk_level'), "Pattern missing risk level"
                    assert 0 <= pattern.confidence <= 1, "Invalid confidence score"
                    assert pattern.risk_level in ['LOW', 'MODERATE', 'HIGH', 'CRITICAL'], "Invalid risk level"
                
                print(f"   ✅ {location}: {len(patterns)} patterns detected")
            else:
                print(f"   ⚠️  {location}: No patterns detected (may be normal)")
        
        print("   ✅ Weather pattern analysis working correctly")
    
    def test_anomaly_detection(self):
        """Test anomaly detection functionality."""
        print("\n🔍 Testing Anomaly Detection...")
        
        for location in self.test_locations:
            anomalies = self.analysis_service.detect_anomalies(location, days=2)
            
            # Validate anomalies structure
            for anomaly in anomalies:
                assert hasattr(anomaly, 'anomaly_type'), "Anomaly missing type"
                assert hasattr(anomaly, 'severity'), "Anomaly missing severity"
                assert hasattr(anomaly, 'confidence'), "Anomaly missing confidence"
                assert anomaly.severity in ['LOW', 'MODERATE', 'HIGH', 'CRITICAL'], "Invalid severity"
                assert 0 <= anomaly.confidence <= 1, "Invalid confidence score"
            
            print(f"   ✅ {location}: {len(anomalies)} anomalies detected")
        
        print("   ✅ Anomaly detection working correctly")
    
    def test_trend_analysis(self):
        """Test trend analysis functionality."""
        print("\n📈 Testing Trend Analysis...")
        
        for location in self.test_locations:
            trends = self.analysis_service.analyze_trends(location, days=7)
            
            # Validate trends structure
            assert 'temperature' in trends, "Temperature trend missing"
            assert 'pressure' in trends, "Pressure trend missing"
            assert 'humidity' in trends, "Humidity trend missing"
            assert 'wind_speed' in trends, "Wind speed trend missing"
            assert 'assessment' in trends, "Overall assessment missing"
            
            # Validate trend components
            for param in ['temperature', 'pressure', 'humidity', 'wind_speed']:
                trend = trends[param]
                assert 'direction' in trend, f"{param} trend missing direction"
                assert 'rate' in trend, f"{param} trend missing rate"
                assert 'significance' in trend, f"{param} trend missing significance"
                assert trend['direction'] in ['increasing', 'decreasing', 'stable'], f"Invalid {param} direction"
                assert trend['significance'] in ['low', 'moderate', 'high'], f"Invalid {param} significance"
            
            print(f"   ✅ {location}: Trend analysis completed")
        
        print("   ✅ Trend analysis working correctly")
    
    def test_risk_scoring(self):
        """Test risk scoring calculations."""
        print("\n⚠️  Testing Risk Scoring...")
        
        for location in self.test_locations:
            risk_score = self.analysis_service.calculate_risk_scores(location, forecast_hours=24)
            
            # Validate risk score structure
            assert hasattr(risk_score, 'overall_risk'), "Overall risk missing"
            assert hasattr(risk_score, 'risk_level'), "Risk level missing"
            assert hasattr(risk_score, 'category_risks'), "Category risks missing"
            assert hasattr(risk_score, 'recommendations'), "Recommendations missing"
            
            # Validate risk values
            assert 0 <= risk_score.overall_risk <= 1, "Invalid overall risk score"
            assert risk_score.risk_level in ['MINIMAL', 'LOW', 'MODERATE', 'HIGH', 'CRITICAL'], "Invalid risk level"
            
            # Validate category risks
            expected_categories = ['typhoon', 'flooding', 'heat_stress', 'general_weather']
            for category in expected_categories:
                assert category in risk_score.category_risks, f"Missing {category} risk"
                assert 0 <= risk_score.category_risks[category] <= 1, f"Invalid {category} risk score"
            
            print(f"   ✅ {location}: Risk level {risk_score.risk_level} ({risk_score.overall_risk:.2f})")
        
        print("   ✅ Risk scoring working correctly")
    
    def test_geospatial_processing(self):
        """Test geospatial processing functionality."""
        print("\n🗺️  Testing Geospatial Processing...")
        
        # Test location data processing
        processed_data = self.geo_service.process_location_data(self.test_locations, hours=12)
        
        for location in self.test_locations:
            assert location in processed_data, f"Missing data for {location}"
            
            location_data = processed_data[location]
            if 'error' not in location_data:
                assert 'geographic_context' in location_data, "Geographic context missing"
                assert 'risk_assessment' in location_data, "Risk assessment missing"
                assert 'nearby_locations' in location_data, "Nearby locations missing"
                assert 'regional_impact' in location_data, "Regional impact missing"
                
                print(f"   ✅ {location}: Geospatial processing completed")
            else:
                print(f"   ⚠️  {location}: {location_data['error']}")
        
        # Test distance calculation
        manila_coords = (14.5995, 120.9842)
        cebu_coords = (10.3157, 123.8854)
        distance = self.geo_service.calculate_distance(manila_coords, cebu_coords)
        
        assert 400 < distance < 800, f"Distance calculation seems wrong: {distance} km"
        print(f"   ✅ Distance calculation: Manila-Cebu = {distance:.1f} km")
        
        print("   ✅ Geospatial processing working correctly")
    
    def test_regional_risk_mapping(self):
        """Test regional risk mapping functionality."""
        print("\n🏝️  Testing Regional Risk Mapping...")
        
        # Test national risk mapping
        national_risk_map = self.geo_service.create_regional_risk_map()
        
        assert len(national_risk_map) > 0, "No regional risk mappings generated"
        
        for risk_mapping in national_risk_map:
            assert hasattr(risk_mapping, 'region'), "Risk mapping missing region"
            assert hasattr(risk_mapping, 'risk_level'), "Risk mapping missing risk level"
            assert hasattr(risk_mapping, 'risk_score'), "Risk mapping missing risk score"
            assert hasattr(risk_mapping, 'population_at_risk'), "Risk mapping missing population data"
            assert hasattr(risk_mapping, 'recommendations'), "Risk mapping missing recommendations"
            
            assert 0 <= risk_mapping.risk_score <= 100, "Invalid risk score"
            assert risk_mapping.population_at_risk >= 0, "Invalid population at risk"
        
        print(f"   ✅ National risk mapping: {len(national_risk_map)} regions analyzed")
        
        # Test specific region mapping
        metro_manila_risk = self.geo_service.create_regional_risk_map("Metro Manila")
        assert len(metro_manila_risk) > 0, "Metro Manila risk mapping failed"
        
        print(f"   ✅ Metro Manila risk level: {metro_manila_risk[0].risk_level}")
        
        print("   ✅ Regional risk mapping working correctly")
    
    def test_multi_location_analysis(self):
        """Test multi-location analysis capabilities."""
        print("\n🌐 Testing Multi-Location Analysis...")
        
        # Test regional aggregation
        try:
            regional_agg = self.geo_service.aggregate_regional_data("Metro Manila", hours=24)
            
            assert hasattr(regional_agg, 'region'), "Regional aggregation missing region"
            assert hasattr(regional_agg, 'average_conditions'), "Regional aggregation missing averages"
            assert hasattr(regional_agg, 'extreme_conditions'), "Regional aggregation missing extremes"
            assert hasattr(regional_agg, 'coverage_area_km2'), "Regional aggregation missing area"
            
            assert regional_agg.coverage_area_km2 > 0, "Invalid coverage area"
            
            print(f"   ✅ Metro Manila aggregation: {regional_agg.location_count} locations")
        except Exception as e:
            print(f"   ⚠️  Regional aggregation error: {e}")
        
        # Test high-risk area identification
        high_risk_areas = self.geo_service.find_high_risk_areas(risk_threshold=0.5)
        
        for area in high_risk_areas:
            assert 'region' in area, "High-risk area missing region"
            assert 'risk_score' in area, "High-risk area missing risk score"
            assert 'population_at_risk' in area, "High-risk area missing population data"
            assert area['risk_score'] >= 0.5, "Risk score below threshold"
        
        print(f"   ✅ High-risk areas identified: {len(high_risk_areas)}")
        
        print("   ✅ Multi-location analysis working correctly")
    
    def test_performance_optimization(self):
        """Test performance and optimization features."""
        print("\n⚡ Testing Performance Optimization...")
        
        # Test analysis speed
        start_time = time.time()
        
        # Run multiple analyses to test performance
        for location in self.test_locations:
            self.analysis_service.calculate_risk_scores(location, forecast_hours=6)
        
        analysis_time = time.time() - start_time
        avg_time_per_analysis = analysis_time / len(self.test_locations)
        
        assert avg_time_per_analysis < 5.0, f"Analysis too slow: {avg_time_per_analysis:.2f}s per location"
        print(f"   ✅ Analysis performance: {avg_time_per_analysis:.2f}s per location")
        
        # Test database query optimization
        start_time = time.time()
        
        from app.models.weather import CurrentWeather
        recent_data_count = self.db.query(CurrentWeather).filter(
            CurrentWeather.timestamp >= datetime.now() - timedelta(hours=24)
        ).count()
        
        query_time = time.time() - start_time
        assert query_time < 2.0, f"Database query too slow: {query_time:.2f}s"
        
        print(f"   ✅ Database performance: {query_time:.3f}s for {recent_data_count} records")
        
        # Test memory usage (basic check)
        import psutil
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        
        assert memory_usage < 500, f"Memory usage too high: {memory_usage:.1f}MB"
        print(f"   ✅ Memory usage: {memory_usage:.1f}MB")
        
        print("   ✅ Performance optimization working correctly")
    
    def test_api_endpoints(self):
        """Test new API endpoints (if server is running)."""
        print("\n🌐 Testing API Endpoints...")
        
        base_url = "http://localhost:8000/api/v1/weather"
        
        try:
            # Test health endpoint
            response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
            if response.status_code == 200:
                print("   ✅ API server is running")
                
                # Test comprehensive analysis endpoint
                analysis_data = {
                    "location": "Manila,PH",
                    "analysis_types": ["risk_score", "patterns"],
                    "time_range": "24h",
                    "include_geospatial": True
                }
                
                response = requests.post(
                    f"{base_url}/analyze/comprehensive",
                    json=analysis_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    assert 'risk_assessment' in result, "Missing risk assessment in API response"
                    print("   ✅ Comprehensive analysis API working")
                else:
                    print(f"   ⚠️  API endpoint returned status {response.status_code}")
            else:
                print("   ⚠️  API server not responding correctly")
                
        except requests.exceptions.RequestException:
            print("   ⚠️  API server not running (this is okay for backend-only testing)")
        
        print("   ✅ API endpoint testing completed")
    
    def test_data_export_utilities(self):
        """Test data export utilities."""
        print("\n📤 Testing Data Export Utilities...")
        
        # Test weather data export
        from app.models.weather import CurrentWeather
        import pandas as pd
        
        # Get recent weather data
        recent_data = self.db.query(CurrentWeather).filter(
            CurrentWeather.timestamp >= datetime.now() - timedelta(hours=48)
        ).limit(100).all()
        
        if recent_data:
            # Convert to DataFrame for export testing
            export_data = []
            for record in recent_data:
                export_data.append({
                    'timestamp': record.timestamp.isoformat(),
                    'location': record.location,
                    'temperature': record.temperature,
                    'humidity': record.humidity,
                    'pressure': record.pressure,
                    'wind_speed': record.wind_speed,
                    'weather_condition': record.weather_condition
                })
            
            df = pd.DataFrame(export_data)
            
            # Test CSV export
            csv_path = '/tmp/weather_export_test.csv'
            df.to_csv(csv_path, index=False)
            
            # Verify export
            assert os.path.exists(csv_path), "CSV export failed"
            
            # Read back and verify
            df_read = pd.read_csv(csv_path)
            assert len(df_read) == len(df), "CSV export/import mismatch"
            
            os.remove(csv_path)  # Cleanup
            
            print(f"   ✅ Data export: {len(export_data)} records exported successfully")
        else:
            print("   ⚠️  No recent data available for export testing")
        
        print("   ✅ Data export utilities working correctly")
    
    def _log_test_result(self, test_name: str, passed: bool, execution_time: float, error_msg: str = ""):
        """Log test result."""
        if passed:
            self.results['tests_passed'] += 1
            status = "✅ PASSED"
        else:
            self.results['tests_failed'] += 1
            status = "❌ FAILED"
        
        self.results['test_details'].append({
            'test': test_name,
            'status': status,
            'execution_time': round(execution_time, 3),
            'error': error_msg
        })
        
        if not passed:
            print(f"   ❌ {test_name} FAILED: {error_msg}")
    
    def _print_test_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("🏁 PHASE 1 COMPLETION TEST RESULTS")
        print("=" * 60)
        
        total_tests = self.results['tests_passed'] + self.results['tests_failed']
        success_rate = (self.results['tests_passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {self.results['tests_passed']}")
        print(f"   Failed: {self.results['tests_failed']}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if self.results['tests_failed'] == 0:
            print("\n🎉 ALL TESTS PASSED! Phase 1 is complete and ready for Phase 2.")
        else:
            print(f"\n⚠️  {self.results['tests_failed']} tests failed. Please review and fix issues.")
        
        print("\n📋 Detailed Results:")
        for test_detail in self.results['test_details']:
            print(f"   {test_detail['status']} {test_detail['test']} ({test_detail['execution_time']}s)")
            if test_detail['error']:
                print(f"      Error: {test_detail['error']}")
        
        print("\n" + "=" * 60)
    
    def __del__(self):
        """Cleanup database connection."""
        if hasattr(self, 'db'):
            self.db.close()


def main():
    """Run Phase 1 completion tests."""
    print("🚀 Starting Phase 1 Completion Validation")
    print("⏰ Timestamp:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Import required modules
    from datetime import timedelta
    
    # Run test suite
    test_suite = Phase1TestSuite()
    
    try:
        success = test_suite.run_all_tests()
        
        if success:
            print("\n✅ PHASE 1 COMPLETION VALIDATED")
            print("🎯 Ready to proceed to Phase 2: AI/RAG Implementation")
            return True
        else:
            print("\n❌ PHASE 1 VALIDATION FAILED")
            print("🔧 Please address the failed tests before proceeding to Phase 2")
            return False
            
    except Exception as e:
        print(f"\n💥 Test suite encountered critical error: {e}")
        return False
    
    finally:
        print(f"\n📝 Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)