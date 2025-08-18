"""
WeatherWise Weather Analysis Service
Implements weather pattern analysis, anomaly detection, and risk scoring
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from dataclasses import dataclass
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class WeatherPattern:
    """Weather pattern analysis result."""
    pattern_type: str
    confidence: float
    description: str
    risk_level: str
    indicators: Dict
    timeline: str


@dataclass
class AnomalyResult:
    """Anomaly detection result."""
    anomaly_type: str
    severity: str
    value: float
    expected_range: Tuple[float, float]
    confidence: float
    timestamp: datetime
    risk_implications: List[str]


@dataclass
class RiskScore:
    """Risk scoring result."""
    overall_risk: float
    category_risks: Dict[str, float]
    risk_level: str
    confidence: float
    contributing_factors: List[str]
    recommendations: List[str]


class WeatherAnalysisService:
    """Advanced weather analysis service for DRRM."""

    def __init__(self, db_session: Session):
        """Initialize weather analysis service."""
        self.db = db_session

        # Risk thresholds for Philippine context
        self.risk_thresholds = {
            'typhoon': {
                'wind_speed': [40, 60, 90, 120],  # km/h: Low, Moderate, High, Critical
                'pressure_drop': [5, 10, 15, 25],  # hPa rapid change
            },
            'flooding': {
                'rainfall_intensity': [10, 25, 50, 100],  # mm/hour
                'humidity': [70, 80, 90, 95],  # %
            },
            'heat': {
                'temperature': [32, 35, 38, 42],  # °C
                'heat_index': [32, 40, 52, 54],  # °C
            }
        }
        
        logger.info("Weather analysis service initialized")

    def analyze_weather_patterns(self, location: str, days: int = 7) -> List[WeatherPattern]:
        """Analyze weather patterns for disaster risk indicators.
        
        Args:
            location: Location to analyze
            days: Number of days to analyze

        Returns:
            List of detected weather patterns
        """
        logger.info(f"Analyzing weather patterns for {location} ({days} days)")

        # Get weather data
        weather_data = self._get_weather_data(location, days)
        if len(weather_data) < 5:
            logger.warning(f"Insufficient data for pattern analysis: {len(weather_data)} records")
            return []
        
        patterns = []
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(weather_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # 1. Pressure Pattern Analysis (Storm Development)
        pressure_pattern = self._analyze_pressure_patterns(df)
        if pressure_pattern:
            patterns.append(pressure_pattern)
        
        # 2. Temperature Trend Analysis
        temp_pattern = self._analyze_temperature_trends(df)
        if temp_pattern:
            patterns.append(temp_pattern)
        
        # 3. Humidity and Rainfall Correlation
        humidity_pattern = self._analyze_humidity_patterns(df)
        if humidity_pattern:
            patterns.append(humidity_pattern)
        
        # 4. Wind Pattern Analysis
        wind_pattern = self._analyze_wind_patterns(df)
        if wind_pattern:
            patterns.append(wind_pattern)
        
        # 5. Composite Storm Development Pattern
        storm_pattern = self._analyze_storm_development(df)
        if storm_pattern:
            patterns.append(storm_pattern)
        
        logger.info(f"Identified {len(patterns)} weather patterns")
        return patterns
    
    def detect_anomalies(self, location: str, days: int = 3) -> List[AnomalyResult]:
        """Detect weather anomalies using statistical and ML methods.
        
        Args:
            location: Location to analyze
            days: Number of days to analyze
            
        Returns:
            List of detected anomalies
        """
        logger.info(f"Detecting anomalies for {location}")
        
        # Get recent and historical data
        recent_data = self._get_weather_data(location, days)
        historical_data = self._get_historical_baseline(location, days=30)
        
        if len(recent_data) < 3 or len(historical_data) < 10:
            logger.warning("Insufficient data for anomaly detection")
            return []
        
        anomalies = []
        
        # Statistical anomaly detection
        stat_anomalies = self._statistical_anomaly_detection(recent_data, historical_data)
        anomalies.extend(stat_anomalies)
        
        # Time series anomaly detection
        ts_anomalies = self._time_series_anomaly_detection(recent_data, historical_data)
        anomalies.extend(ts_anomalies)
        
        # Multivariate anomaly detection
        mv_anomalies = self._multivariate_anomaly_detection(recent_data, historical_data)
        anomalies.extend(mv_anomalies)
        
        # Remove duplicates and sort by severity
        unique_anomalies = self._deduplicate_anomalies(anomalies)
        
        logger.info(f"Detected {len(unique_anomalies)} unique anomalies")
        return unique_anomalies
    
    def calculate_risk_scores(self, location: str, forecast_hours: int = 24) -> RiskScore:
        """Calculate comprehensive disaster risk scores.
        
        Args:
            location: Location to analyze
            forecast_hours: Hours ahead to analyze
            
        Returns:
            Comprehensive risk score
        """
        logger.info(f"Calculating risk scores for {location}")
        
        # Get current and forecast data
        current_data = self._get_weather_data(location, days=1)
        forecast_data = self._get_forecast_data(location, hours=forecast_hours)
        
        if not current_data and not forecast_data:
            logger.error("No data available for risk calculation")
            return self._default_risk_score()
        
        # Calculate individual risk components
        typhoon_risk = self._calculate_typhoon_risk(current_data, forecast_data)
        flood_risk = self._calculate_flood_risk(current_data, forecast_data)
        heat_risk = self._calculate_heat_risk(current_data, forecast_data)
        general_risk = self._calculate_general_weather_risk(current_data, forecast_data)
        
        # Combine risks with weights
        category_risks = {
            'typhoon': typhoon_risk,
            'flooding': flood_risk,
            'heat_stress': heat_risk,
            'general_weather': general_risk
        }
        
        # Calculate weighted overall risk
        risk_weights = {'typhoon': 0.4, 'flooding': 0.3, 'heat_stress': 0.2, 'general_weather': 0.1}
        overall_risk = sum(category_risks[cat] * risk_weights[cat] for cat in category_risks)
        
        # Determine risk level
        risk_level = self._categorize_risk_level(overall_risk)
        
        # Generate recommendations
        recommendations = self._generate_risk_recommendations(category_risks, overall_risk)
        
        # Identify contributing factors
        contributing_factors = self._identify_risk_factors(current_data, forecast_data, category_risks)
        
        return RiskScore(
            overall_risk=round(overall_risk, 2),
            category_risks={k: round(v, 2) for k, v in category_risks.items()},
            risk_level=risk_level,
            confidence=0.85,  # Base confidence, can be refined
            contributing_factors=contributing_factors,
            recommendations=recommendations
        )
    
    def analyze_trends(self, location: str, days: int = 14) -> Dict:
        """Analyze weather trends for predictive insights.
        
        Args:
            location: Location to analyze
            days: Number of days to analyze
            
        Returns:
            Trend analysis results
        """
        logger.info(f"Analyzing trends for {location} ({days} days)")
        
        weather_data = self._get_weather_data(location, days)
        if len(weather_data) < 7:
            return {'error': 'Insufficient data for trend analysis'}
        
        df = pd.DataFrame(weather_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        trends = {}
        
        # Temperature trend
        temp_trend = self._calculate_linear_trend(df['temperature'].values)
        trends['temperature'] = {
            'direction': 'increasing' if temp_trend > 0.1 else 'decreasing' if temp_trend < -0.1 else 'stable',
            'rate': round(temp_trend, 3),
            'significance': 'high' if abs(temp_trend) > 0.5 else 'moderate' if abs(temp_trend) > 0.2 else 'low'
        }
        
        # Pressure trend (critical for storm development)
        pressure_trend = self._calculate_linear_trend(df['pressure'].values)
        trends['pressure'] = {
            'direction': 'increasing' if pressure_trend > 0.1 else 'decreasing' if pressure_trend < -0.1 else 'stable',
            'rate': round(pressure_trend, 3),
            'significance': 'high' if abs(pressure_trend) > 2 else 'moderate' if abs(pressure_trend) > 1 else 'low'
        }
        
        # Humidity trend
        humidity_trend = self._calculate_linear_trend(df['humidity'].values)
        trends['humidity'] = {
            'direction': 'increasing' if humidity_trend > 0.5 else 'decreasing' if humidity_trend < -0.5 else 'stable',
            'rate': round(humidity_trend, 3),
            'significance': 'high' if abs(humidity_trend) > 2 else 'moderate' if abs(humidity_trend) > 1 else 'low'
        }
        
        # Wind speed trend
        wind_trend = self._calculate_linear_trend(df['wind_speed'].values)
        trends['wind_speed'] = {
            'direction': 'increasing' if wind_trend > 0.5 else 'decreasing' if wind_trend < -0.5 else 'stable',
            'rate': round(wind_trend, 3),
            'significance': 'high' if abs(wind_trend) > 5 else 'moderate' if abs(wind_trend) > 2 else 'low'
        }
        
        # Overall trend assessment
        trends['assessment'] = self._assess_overall_trends(trends)
        
        return trends
    
    # Helper methods
    def _get_weather_data(self, location: str, days: int) -> List[Dict]:
        """Get weather data from database."""
        from ..models.weather import CurrentWeather
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        query = self.db.query(CurrentWeather).filter(
            and_(
                CurrentWeather.location == location,
                CurrentWeather.timestamp >= cutoff_date
            )
        ).order_by(desc(CurrentWeather.timestamp))
        
        results = query.all()
        
        return [{
            'timestamp': r.timestamp.isoformat(),
            'temperature': r.temperature,
            'humidity': r.humidity,
            'pressure': r.pressure,
            'wind_speed': r.wind_speed,
            'wind_direction': r.wind_direction,
            'weather_condition': r.weather_condition,
            'visibility': r.visibility
        } for r in results]
    
    def _get_forecast_data(self, location: str, hours: int) -> List[Dict]:
        """Get forecast data from database."""
        from ..models.weather import WeatherForecast
        
        cutoff_date = datetime.now(timezone.utc) + timedelta(hours=hours)
        
        query = self.db.query(WeatherForecast).filter(
            and_(
                WeatherForecast.location == location,
                WeatherForecast.forecast_date <= cutoff_date,
                WeatherForecast.forecast_date >= datetime.now(timezone.utc)
            )
        ).order_by(WeatherForecast.forecast_date)
        
        results = query.all()
        
        return [{
            'timestamp': r.forecast_date.isoformat(),
            'temperature': r.temperature or r.temperature_max,
            'humidity': r.humidity,
            'pressure': r.pressure,
            'wind_speed': r.wind_speed,
            'weather_condition': r.weather_condition,
            'precipitation_probability': r.precipitation_probability
        } for r in results]
    
    def _get_historical_baseline(self, location: str, days: int) -> List[Dict]:
        """Get historical data for baseline comparison."""
        # For now, use recent data as baseline
        # In production, this would query historical weather patterns
        return self._get_weather_data(location, days)
    
    def _analyze_pressure_patterns(self, df: pd.DataFrame) -> Optional[WeatherPattern]:
        """Analyze atmospheric pressure patterns for storm indicators."""
        if 'pressure' not in df.columns or len(df) < 3:
            return None
        
        pressure_values = df['pressure'].values
        pressure_change = np.diff(pressure_values)
        
        # Rapid pressure drop (typhoon indicator)
        if len(pressure_change) > 0:
            max_drop = np.min(pressure_change)
            if max_drop < -10:  # Rapid pressure drop > 10 hPa
                return WeatherPattern(
                    pattern_type="rapid_pressure_drop",
                    confidence=0.9,
                    description=f"Rapid atmospheric pressure drop of {abs(max_drop):.1f} hPa detected",
                    risk_level="HIGH",
                    indicators={'pressure_drop': abs(max_drop), 'rate': 'rapid'},
                    timeline="immediate"
                )
        
        return None
    
    def _analyze_temperature_trends(self, df: pd.DataFrame) -> Optional[WeatherPattern]:
        """Analyze temperature patterns for heat stress indicators."""
        if 'temperature' not in df.columns:
            return None
        
        temps = df['temperature'].values
        avg_temp = np.mean(temps)
        max_temp = np.max(temps)
        
        # Heat stress pattern
        if max_temp > 35 or avg_temp > 32:
            return WeatherPattern(
                pattern_type="heat_stress",
                confidence=0.8,
                description=f"Elevated temperatures detected (max: {max_temp:.1f}°C, avg: {avg_temp:.1f}°C)",
                risk_level="MODERATE" if max_temp < 38 else "HIGH",
                indicators={'max_temp': max_temp, 'avg_temp': avg_temp},
                timeline="current"
            )
        
        return None
    
    def _analyze_humidity_patterns(self, df: pd.DataFrame) -> Optional[WeatherPattern]:
        """Analyze humidity patterns for flooding risk."""
        if 'humidity' not in df.columns:
            return None
        
        humidity = df['humidity'].values
        avg_humidity = np.mean(humidity)
        
        if avg_humidity > 85:
            return WeatherPattern(
                pattern_type="high_humidity",
                confidence=0.7,
                description=f"Sustained high humidity levels ({avg_humidity:.1f}%) indicating potential precipitation",
                risk_level="MODERATE",
                indicators={'avg_humidity': avg_humidity},
                timeline="short_term"
            )
        
        return None
    
    def _analyze_wind_patterns(self, df: pd.DataFrame) -> Optional[WeatherPattern]:
        """Analyze wind patterns for storm development."""
        if 'wind_speed' not in df.columns:
            return None
        
        wind_speeds = df['wind_speed'].values
        max_wind = np.max(wind_speeds)
        avg_wind = np.mean(wind_speeds)
        
        if max_wind > 60:  # Typhoon-level winds
            return WeatherPattern(
                pattern_type="strong_winds",
                confidence=0.95,
                description=f"Strong winds detected (max: {max_wind:.1f} km/h)",
                risk_level="CRITICAL" if max_wind > 120 else "HIGH",
                indicators={'max_wind': max_wind, 'avg_wind': avg_wind},
                timeline="immediate"
            )
        elif max_wind > 40:  # Strong wind warning level
            return WeatherPattern(
                pattern_type="moderate_winds",
                confidence=0.8,
                description=f"Moderate strong winds (max: {max_wind:.1f} km/h)",
                risk_level="MODERATE",
                indicators={'max_wind': max_wind},
                timeline="current"
            )
        
        return None
    
    def _analyze_storm_development(self, df: pd.DataFrame) -> Optional[WeatherPattern]:
        """Analyze composite indicators for storm development."""
        if len(df) < 3:
            return None
        
        # Multiple indicators suggesting storm development
        pressure_drop = np.min(np.diff(df['pressure'].values)) if 'pressure' in df.columns else 0
        wind_increase = np.max(np.diff(df['wind_speed'].values)) if 'wind_speed' in df.columns else 0
        high_humidity = np.mean(df['humidity'].values) > 80 if 'humidity' in df.columns else False
        
        storm_indicators = 0
        if pressure_drop < -5:
            storm_indicators += 1
        if wind_increase > 10:
            storm_indicators += 1
        if high_humidity:
            storm_indicators += 1
        
        if storm_indicators >= 2:
            return WeatherPattern(
                pattern_type="storm_development",
                confidence=0.85,
                description="Multiple indicators suggest storm system development",
                risk_level="HIGH",
                indicators={
                    'pressure_drop': pressure_drop,
                    'wind_increase': wind_increase,
                    'high_humidity': high_humidity
                },
                timeline="developing"
            )
        
        return None
    
    def _statistical_anomaly_detection(self, recent_data: List[Dict], historical_data: List[Dict]) -> List[AnomalyResult]:
        """Detect anomalies using statistical methods."""
        anomalies = []
        
        if not historical_data:
            return anomalies
        
        # Convert to DataFrames
        recent_df = pd.DataFrame(recent_data)
        historical_df = pd.DataFrame(historical_data)
        
        # Check each parameter
        for param in ['temperature', 'pressure', 'humidity', 'wind_speed']:
            if param in recent_df.columns and param in historical_df.columns:
                # Calculate historical statistics
                hist_mean = historical_df[param].mean()
                hist_std = historical_df[param].std()
                
                # Check recent values for outliers
                for _, row in recent_df.iterrows():
                    value = row[param]
                    z_score = abs(value - hist_mean) / hist_std if hist_std > 0 else 0
                    
                    if z_score > 2.5:  # Significant anomaly
                        severity = "HIGH" if z_score > 3.5 else "MODERATE"
                        expected_range = (hist_mean - 2*hist_std, hist_mean + 2*hist_std)
                        
                        anomalies.append(AnomalyResult(
                            anomaly_type=f"{param}_outlier",
                            severity=severity,
                            value=value,
                            expected_range=expected_range,
                            confidence=min(0.95, z_score / 4),
                            timestamp=pd.to_datetime(row['timestamp']),
                            risk_implications=self._get_risk_implications(param, value, hist_mean)
                        ))
        
        return anomalies
    
    def _time_series_anomaly_detection(self, recent_data: List[Dict], historical_data: List[Dict]) -> List[AnomalyResult]:
        """Detect anomalies in time series patterns."""
        anomalies = []
        
        if len(recent_data) < 3:
            return anomalies
        
        recent_df = pd.DataFrame(recent_data)
        recent_df['timestamp'] = pd.to_datetime(recent_df['timestamp'])
        recent_df = recent_df.sort_values('timestamp')
        
        # Detect rapid changes
        for param in ['pressure', 'temperature', 'wind_speed']:
            if param in recent_df.columns:
                values = recent_df[param].values
                changes = np.diff(values)
                
                if len(changes) > 0:
                    max_change = np.max(np.abs(changes))
                    
                    # Define thresholds for rapid changes
                    thresholds = {
                        'pressure': 15,    # hPa per hour
                        'temperature': 8,  # °C per hour  
                        'wind_speed': 30   # km/h per hour
                    }
                    
                    if max_change > thresholds.get(param, 999):
                        anomalies.append(AnomalyResult(
                            anomaly_type=f"rapid_{param}_change",
                            severity="HIGH",
                            value=max_change,
                            expected_range=(0, thresholds[param]),
                            confidence=0.9,
                            timestamp=recent_df.iloc[-1]['timestamp'],
                            risk_implications=[f"Rapid {param} change indicates unstable conditions"]
                        ))
        
        return anomalies
    
    def _multivariate_anomaly_detection(self, recent_data: List[Dict], historical_data: List[Dict]) -> List[AnomalyResult]:
        """Detect anomalies using multivariate analysis."""
        anomalies = []
        
        if len(recent_data) < 3 or len(historical_data) < 10:
            return anomalies
        
        try:
            # Prepare data
            recent_df = pd.DataFrame(recent_data)
            historical_df = pd.DataFrame(historical_data)
            
            # Select numeric columns
            numeric_cols = ['temperature', 'pressure', 'humidity', 'wind_speed']
            available_cols = [col for col in numeric_cols if col in recent_df.columns and col in historical_df.columns]
            
            if len(available_cols) < 2:
                return anomalies
            
            # Standardize data
            scaler = StandardScaler()
            historical_scaled = scaler.fit_transform(historical_df[available_cols])
            recent_scaled = scaler.transform(recent_df[available_cols])
            
            # Use DBSCAN for anomaly detection
            dbscan = DBSCAN(eps=0.5, min_samples=3)
            labels = dbscan.fit_predict(np.vstack([historical_scaled, recent_scaled]))
            
            # Check if recent points are anomalies (label = -1)
            recent_labels = labels[-len(recent_data):]
            
            for i, label in enumerate(recent_labels):
                if label == -1:  # Anomaly
                    anomalies.append(AnomalyResult(
                        anomaly_type="multivariate_anomaly",
                        severity="MODERATE",
                        value=0.0,  # No single value for multivariate
                        expected_range=(0, 1),
                        confidence=0.75,
                        timestamp=pd.to_datetime(recent_data[i]['timestamp']),
                        risk_implications=["Unusual combination of weather parameters detected"]
                    ))
        
        except Exception as e:
            logger.warning(f"Multivariate anomaly detection failed: {e}")
        
        return anomalies
    
    def _deduplicate_anomalies(self, anomalies: List[AnomalyResult]) -> List[AnomalyResult]:
        """Remove duplicate anomalies and sort by severity."""
        if not anomalies:
            return []
        
        # Sort by severity and confidence
        severity_order = {"CRITICAL": 3, "HIGH": 2, "MODERATE": 1, "LOW": 0}
        
        sorted_anomalies = sorted(anomalies, key=lambda x: (
            severity_order.get(x.severity, 0),
            x.confidence
        ), reverse=True)
        
        # Simple deduplication by type and timestamp proximity
        unique_anomalies = []
        for anomaly in sorted_anomalies:
            is_duplicate = False
            for existing in unique_anomalies:
                if (anomaly.anomaly_type == existing.anomaly_type and
                    abs((anomaly.timestamp - existing.timestamp).total_seconds()) < 3600):  # 1 hour
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_anomalies.append(anomaly)
        
        return unique_anomalies[:10]  # Limit to top 10 anomalies
    
    def _calculate_typhoon_risk(self, current_data: List[Dict], forecast_data: List[Dict]) -> float:
        """Calculate typhoon risk score."""
        if not current_data and not forecast_data:
            return 0.0
        
        all_data = current_data + forecast_data
        risk_score = 0.0
        
        # Wind speed risk
        wind_speeds = [d['wind_speed'] for d in all_data if 'wind_speed' in d and d['wind_speed']]
        if wind_speeds:
            max_wind = max(wind_speeds)
            if max_wind >= 120:
                risk_score += 0.4  # Critical
            elif max_wind >= 90:
                risk_score += 0.3  # High
            elif max_wind >= 60:
                risk_score += 0.2  # Moderate
            elif max_wind >= 40:
                risk_score += 0.1  # Low
        
        # Pressure drop risk
        pressures = [d['pressure'] for d in all_data if 'pressure' in d and d['pressure']]
        if len(pressures) > 1:
            pressure_changes = [pressures[i] - pressures[i-1] for i in range(1, len(pressures))]
            max_drop = abs(min(pressure_changes)) if pressure_changes else 0
            if max_drop >= 25:
                risk_score += 0.3
            elif max_drop >= 15:
                risk_score += 0.2
            elif max_drop >= 10:
                risk_score += 0.1
        
        return min(1.0, risk_score)
    
    def _calculate_flood_risk(self, current_data: List[Dict], forecast_data: List[Dict]) -> float:
        """Calculate flooding risk score."""
        if not current_data and not forecast_data:
            return 0.0
        
        all_data = current_data + forecast_data
        risk_score = 0.0
        
        # High humidity risk
        humidity_values = [d['humidity'] for d in all_data if 'humidity' in d and d['humidity']]
        if humidity_values:
            avg_humidity = sum(humidity_values) / len(humidity_values)
            if avg_humidity >= 95:
                risk_score += 0.3
            elif avg_humidity >= 90:
                risk_score += 0.2
            elif avg_humidity >= 80:
                risk_score += 0.1
        
        # Precipitation probability (from forecast)
        precip_probs = [d.get('precipitation_probability', 0) for d in forecast_data]
        if precip_probs:
            max_precip = max(precip_probs)
            if max_precip >= 90:
                risk_score += 0.4
            elif max_precip >= 70:
                risk_score += 0.3
            elif max_precip >= 50:
                risk_score += 0.2
        
        return min(1.0, risk_score)
    
    def _calculate_heat_risk(self, current_data: List[Dict], forecast_data: List[Dict]) -> float:
        """Calculate heat stress risk score."""
        if not current_data and not forecast_data:
            return 0.0
        
        all_data = current_data + forecast_data
        risk_score = 0.0
        
        # Temperature risk
        temperatures = [d['temperature'] for d in all_data if 'temperature' in d and d['temperature']]
        if temperatures:
            max_temp = max(temperatures)
            if max_temp >= 42:
                risk_score += 0.4  # Critical
            elif max_temp >= 38:
                risk_score += 0.3  # High
            elif max_temp >= 35:
                risk_score += 0.2  # Moderate
            elif max_temp >= 32:
                risk_score += 0.1  # Low
        
        return min(1.0, risk_score)
    
    def _calculate_general_weather_risk(self, current_data: List[Dict], forecast_data: List[Dict]) -> float:
        """Calculate general weather instability risk."""
        if not current_data and not forecast_data:
            return 0.0
        
        all_data = current_data + forecast_data
        risk_score = 0.0
        
        # Visibility risk
        visibility_values = [d.get('visibility', 10) for d in all_data if 'visibility' in d]
        if visibility_values:
            min_visibility = min(visibility_values)
            if min_visibility < 2:
                risk_score += 0.2
            elif min_visibility < 5:
                risk_score += 0.1
        
        # Weather condition risk
        conditions = [d.get('weather_condition', '') for d in all_data]
        severe_conditions = ['Thunderstorm', 'Snow', 'Tornado', 'Severe']
        if any(cond in conditions for cond in severe_conditions):
            risk_score += 0.3
        
        return min(1.0, risk_score)
    
    def _categorize_risk_level(self, risk_score: float) -> str:
        """Categorize overall risk level."""
        if risk_score >= 0.8:
            return "CRITICAL"
        elif risk_score >= 0.6:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MODERATE"
        elif risk_score >= 0.2:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _generate_risk_recommendations(self, category_risks: Dict[str, float], overall_risk: float) -> List[str]:
        """Generate actionable recommendations based on risk assessment."""
        recommendations = []
        
        # Typhoon recommendations
        if category_risks['typhoon'] >= 0.6:
            recommendations.extend([
                "Activate emergency response teams",
                "Issue typhoon warning signals",
                "Prepare evacuation centers",
                "Secure infrastructure and equipment"
            ])
        elif category_risks['typhoon'] >= 0.4:
            recommendations.extend([
                "Monitor typhoon development closely",
                "Prepare emergency supplies",
                "Review evacuation plans"
            ])
        
        # Flooding recommendations
        if category_risks['flooding'] >= 0.6:
            recommendations.extend([
                "Deploy flood monitoring teams",
                "Prepare sandbags and flood barriers",
                "Alert residents in flood-prone areas",
                "Monitor river levels and dam releases"
            ])
        elif category_risks['flooding'] >= 0.4:
            recommendations.extend([
                "Check drainage systems",
                "Monitor rainfall intensity",
                "Prepare flood emergency kits"
            ])
        
        # Heat stress recommendations
        if category_risks['heat_stress'] >= 0.6:
            recommendations.extend([
                "Issue heat advisory warnings",
                "Open cooling centers",
                "Ensure adequate water supply",
                "Monitor vulnerable populations"
            ])
        elif category_risks['heat_stress'] >= 0.4:
            recommendations.extend([
                "Advise reduced outdoor activities",
                "Increase hydration reminders",
                "Check air conditioning systems"
            ])
        
        # General recommendations
        if overall_risk >= 0.6:
            recommendations.extend([
                "Activate disaster response protocols",
                "Coordinate with all emergency services",
                "Prepare public communication systems"
            ])
        
        return list(set(recommendations))  # Remove duplicates
    
    def _identify_risk_factors(self, current_data: List[Dict], forecast_data: List[Dict], category_risks: Dict[str, float]) -> List[str]:
        """Identify specific factors contributing to risk."""
        factors = []
        
        all_data = current_data + forecast_data
        if not all_data:
            return factors
        
        # Temperature factors
        temps = [d['temperature'] for d in all_data if 'temperature' in d and d['temperature']]
        if temps and max(temps) > 35:
            factors.append(f"High temperatures up to {max(temps):.1f}°C")
        
        # Wind factors
        winds = [d['wind_speed'] for d in all_data if 'wind_speed' in d and d['wind_speed']]
        if winds and max(winds) > 40:
            factors.append(f"Strong winds up to {max(winds):.1f} km/h")
        
        # Pressure factors
        pressures = [d['pressure'] for d in all_data if 'pressure' in d and d['pressure']]
        if len(pressures) > 1:
            pressure_drop = max(pressures) - min(pressures)
            if pressure_drop > 10:
                factors.append(f"Significant pressure changes ({pressure_drop:.1f} hPa)")
        
        # Humidity factors
        humidity_values = [d['humidity'] for d in all_data if 'humidity' in d and d['humidity']]
        if humidity_values and max(humidity_values) > 85:
            factors.append(f"High humidity levels up to {max(humidity_values)}%")
        
        return factors
    
    def _get_risk_implications(self, param: str, value: float, baseline: float) -> List[str]:
        """Get risk implications for anomalous parameter values."""
        implications = []
        
        if param == 'temperature':
            if value > baseline + 5:
                implications.append("Increased heat stress risk")
                implications.append("Higher energy demand for cooling")
            elif value < baseline - 5:
                implications.append("Unusual cold conditions")
        
        elif param == 'pressure':
            if value < baseline - 10:
                implications.append("Possible storm system development")
                implications.append("Increased typhoon risk")
            elif value > baseline + 10:
                implications.append("High pressure system")
                implications.append("Stable weather expected")
        
        elif param == 'wind_speed':
            if value > baseline + 20:
                implications.append("Strong wind conditions")
                implications.append("Potential structural damage risk")
        
        elif param == 'humidity':
            if value > baseline + 15:
                implications.append("Increased precipitation likelihood")
                implications.append("Higher flood risk potential")
        
        return implications
    
    def _calculate_linear_trend(self, values: np.ndarray) -> float:
        """Calculate linear trend slope for time series data."""
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        slope, _, _, _, _ = stats.linregress(x, values)
        return slope
    
    def _assess_overall_trends(self, trends: Dict) -> Dict:
        """Assess overall trend patterns for risk implications."""
        assessment = {}
        
        # Risk indicators from trends
        risk_indicators = []
        
        if trends['pressure']['direction'] == 'decreasing' and trends['pressure']['significance'] == 'high':
            risk_indicators.append("Rapid pressure drop indicates potential storm development")
        
        if trends['wind_speed']['direction'] == 'increasing' and trends['wind_speed']['significance'] in ['high', 'moderate']:
            risk_indicators.append("Increasing wind speeds suggest strengthening weather system")
        
        if trends['temperature']['direction'] == 'increasing' and trends['temperature']['significance'] == 'high':
            risk_indicators.append("Rising temperatures increase heat stress risk")
        
        if trends['humidity']['direction'] == 'increasing' and trends['humidity']['significance'] in ['high', 'moderate']:
            risk_indicators.append("Increasing humidity suggests higher precipitation potential")
        
        # Overall stability assessment
        significant_trends = sum(1 for t in trends.values() if isinstance(t, dict) and t.get('significance') == 'high')
        
        if significant_trends >= 3:
            stability = "UNSTABLE"
        elif significant_trends >= 2:
            stability = "CHANGING"
        else:
            stability = "STABLE"
        
        assessment = {
            'overall_stability': stability,
            'risk_indicators': risk_indicators,
            'significant_trends_count': significant_trends,
            'recommendation': self._get_trend_recommendation(stability, risk_indicators)
        }
        
        return assessment
    
    def _get_trend_recommendation(self, stability: str, risk_indicators: List[str]) -> str:
        """Get recommendation based on trend analysis."""
        if stability == "UNSTABLE":
            return "Enhanced monitoring recommended due to unstable weather patterns"
        elif stability == "CHANGING" and risk_indicators:
            return "Monitor weather conditions closely as patterns suggest potential risks"
        elif risk_indicators:
            return "Continue routine monitoring with attention to identified risk factors"
        else:
            return "Weather patterns appear stable, maintain standard monitoring"
    
    def _default_risk_score(self) -> RiskScore:
        """Return default risk score when no data is available."""
        return RiskScore(
            overall_risk=0.0,
            category_risks={
                'typhoon': 0.0,
                'flooding': 0.0,
                'heat_stress': 0.0,
                'general_weather': 0.0
            },
            risk_level="UNKNOWN",
            confidence=0.0,
            contributing_factors=["No data available for analysis"],
            recommendations=["Ensure weather monitoring systems are operational"]
        )


# Integration with existing API
def add_analysis_endpoints(router, db_dependency):
    """Add weather analysis endpoints to existing router."""
    
    @router.post("/analyze/patterns")
    async def analyze_weather_patterns(
        location: str,
        days: int = 7,
        db: Session = db_dependency
    ):
        """Analyze weather patterns for disaster risk indicators."""
        try:
            analysis_service = WeatherAnalysisService(db)
            patterns = analysis_service.analyze_weather_patterns(location, days)
            
            return {
                "status": "success",
                "location": location,
                "analysis_period_days": days,
                "patterns_detected": len(patterns),
                "patterns": [
                    {
                        "type": p.pattern_type,
                        "confidence": p.confidence,
                        "description": p.description,
                        "risk_level": p.risk_level,
                        "indicators": p.indicators,
                        "timeline": p.timeline
                    } for p in patterns
                ]
            }
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            return {"status": "error", "message": str(e)}
    
    @router.post("/analyze/anomalies")
    async def detect_weather_anomalies(
        location: str,
        days: int = 3,
        db: Session = db_dependency
    ):
        """Detect weather anomalies using advanced algorithms."""
        try:
            analysis_service = WeatherAnalysisService(db)
            anomalies = analysis_service.detect_anomalies(location, days)
            
            return {
                "status": "success",
                "location": location,
                "analysis_period_days": days,
                "anomalies_detected": len(anomalies),
                "anomalies": [
                    {
                        "type": a.anomaly_type,
                        "severity": a.severity,
                        "value": a.value,
                        "expected_range": a.expected_range,
                        "confidence": a.confidence,
                        "timestamp": a.timestamp.isoformat(),
                        "risk_implications": a.risk_implications
                    } for a in anomalies
                ]
            }
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return {"status": "error", "message": str(e)}
    
    @router.post("/analyze/risk-score")
    async def calculate_risk_scores(
        location: str,
        forecast_hours: int = 24,
        db: Session = db_dependency
    ):
        """Calculate comprehensive disaster risk scores."""
        try:
            analysis_service = WeatherAnalysisService(db)
            risk_score = analysis_service.calculate_risk_scores(location, forecast_hours)
            
            return {
                "status": "success",
                "location": location,
                "forecast_hours": forecast_hours,
                "risk_assessment": {
                    "overall_risk": risk_score.overall_risk,
                    "risk_level": risk_score.risk_level,
                    "confidence": risk_score.confidence,
                    "category_risks": risk_score.category_risks,
                    "contributing_factors": risk_score.contributing_factors,
                    "recommendations": risk_score.recommendations
                },
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Risk score calculation failed: {e}")
            return {"status": "error", "message": str(e)}
    
    @router.get("/analyze/trends")
    async def analyze_weather_trends(
        location: str,
        days: int = 14,
        db: Session = db_dependency
    ):
        """Analyze weather trends for predictive insights."""
        try:
            analysis_service = WeatherAnalysisService(db)
            trends = analysis_service.analyze_trends(location, days)
            
            return {
                "status": "success",
                "location": location,
                "analysis_period_days": days,
                "trends": trends,
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return {"status": "error", "message": str(e)}