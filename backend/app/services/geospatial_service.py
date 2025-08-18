"""
WeatherWise Geospatial Integration Service
Handles location-based data processing and regional risk mapping for Philippine DRRM
"""

import logging
import math
import json
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from dataclasses import dataclass
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GeographicRegion:
    """Geographic region definition."""
    name: str
    type: str  # 'province', 'city', 'municipality', 'barangay'
    coordinates: List[Tuple[float, float]]  # Bounding box or polygon
    population: Optional[int] = None
    vulnerability_score: Optional[float] = None


@dataclass
class RiskMapping:
    """Regional risk mapping result."""
    region: str
    coordinates: Tuple[float, float]  # Center point
    risk_level: str
    risk_score: float
    population_at_risk: int
    vulnerability_factors: List[str]
    historical_events: List[Dict]
    recommendations: List[str]


@dataclass
class RegionalAggregation:
    """Regional weather data aggregation."""
    region: str
    location_count: int
    average_conditions: Dict[str, float]
    extreme_conditions: Dict[str, float]
    risk_distribution: Dict[str, int]
    coverage_area_km2: float


class GeospatialService:
    """Geospatial analysis service for weather and disaster risk mapping."""
    
    def __init__(self, db_session: Session):
        """Initialize geospatial service."""
        self.db = db_session
        
        # Philippine administrative regions and major cities
        self.philippine_regions = {
            'Metro Manila': {
                'coordinates': (14.5995, 120.9842),
                'bbox': [(14.3, 120.8), (14.8, 121.2)],
                'population': 13923452,
                'vulnerability': 0.8,  # High due to density and flood prone
                'major_cities': ['Manila', 'Quezon City', 'Makati', 'Pasig', 'Taguig']
            },
            'Central Luzon': {
                'coordinates': (15.0, 120.5),
                'bbox': [(14.5, 119.8), (16.2, 121.5)],
                'population': 12422172,
                'vulnerability': 0.7,
                'major_cities': ['Angeles', 'San Jose del Monte', 'Malolos', 'Meycauayan']
            },
            'Calabarzon': {
                'coordinates': (14.2, 121.3),
                'bbox': [(13.5, 120.8), (15.0, 122.5)],
                'population': 14414774,
                'vulnerability': 0.6,
                'major_cities': ['Antipolo', 'Dasmarinas', 'Bacoor', 'Lipa', 'Batangas City']
            },
            'Central Visayas': {
                'coordinates': (10.3, 123.9),
                'bbox': [(9.0, 123.0), (11.5, 125.5)],
                'population': 7396898,
                'vulnerability': 0.9,  # High typhoon exposure
                'major_cities': ['Cebu City', 'Mandaue', 'Lapu-Lapu', 'Talisay', 'Danao']
            },
            'Western Visayas': {
                'coordinates': (11.0, 122.5),
                'bbox': [(9.5, 121.5), (12.0, 124.0)],
                'population': 4730771,
                'vulnerability': 0.7,
                'major_cities': ['Iloilo City', 'Bacolod', 'Roxas', 'Kalibo']
            },
            'Davao Region': {
                'coordinates': (7.0, 125.5),
                'bbox': [(5.5, 124.5), (8.5, 127.0)],
                'population': 5243536,
                'vulnerability': 0.5,  # Lower typhoon frequency
                'major_cities': ['Davao City', 'Tagum', 'Panabo', 'Samal']
            }
        }
        
        # Vulnerability factors by location type
        self.vulnerability_factors = {
            'coastal': {
                'storm_surge': 0.9,
                'typhoon_exposure': 0.8,
                'flooding': 0.7,
                'sea_level_rise': 0.6
            },
            'mountainous': {
                'landslide': 0.8,
                'flash_flood': 0.7,
                'typhoon_winds': 0.6,
                'isolation': 0.5
            },
            'urban': {
                'urban_flooding': 0.8,
                'heat_island': 0.7,
                'infrastructure_overload': 0.6,
                'population_density': 0.9
            },
            'agricultural': {
                'drought': 0.6,
                'crop_damage': 0.7,
                'soil_erosion': 0.5,
                'water_scarcity': 0.6
            }
        }
        
        logger.info("Geospatial service initialized")
    
    def process_location_data(self, locations: List[str], hours: int = 24) -> Dict[str, Dict]:
        """Process weather data for multiple locations with geospatial context.
        
        Args:
            locations: List of location names
            hours: Hours of data to process
            
        Returns:
            Processed location data with geospatial information
        """
        logger.info(f"Processing location data for {len(locations)} locations")
        
        processed_data = {}
        
        for location in locations:
            try:
                # Get weather data
                weather_data = self._get_location_weather_data(location, hours)
                
                # Get geographic context
                geo_context = self._get_geographic_context(location)
                
                # Calculate location-specific risks
                location_risks = self._calculate_location_risks(location, weather_data, geo_context)
                
                # Get nearby locations for regional context
                nearby_locations = self._find_nearby_locations(location, radius_km=50)
                
                processed_data[location] = {
                    'weather_data': weather_data,
                    'geographic_context': geo_context,
                    'risk_assessment': location_risks,
                    'nearby_locations': nearby_locations,
                    'regional_impact': self._assess_regional_impact(location, location_risks)
                }
                
            except Exception as e:
                logger.error(f"Failed to process location {location}: {e}")
                processed_data[location] = {'error': str(e)}
        
        return processed_data
    
    def create_regional_risk_map(self, region_name: Optional[str] = None) -> List[RiskMapping]:
        """Create risk mapping for specified region or all Philippines.
        
        Args:
            region_name: Specific region to map (optional)
            
        Returns:
            List of risk mappings for the region
        """
        logger.info(f"Creating regional risk map for: {region_name or 'All Philippines'}")
        
        risk_mappings = []
        
        # Determine which regions to process
        if region_name and region_name in self.philippine_regions:
            regions_to_process = {region_name: self.philippine_regions[region_name]}
        else:
            regions_to_process = self.philippine_regions
        
        for region, region_data in regions_to_process.items():
            try:
                # Get regional weather data
                regional_weather = self._get_regional_weather_data(region, region_data)
                
                # Calculate regional risk
                regional_risk = self._calculate_regional_risk(region, regional_weather, region_data)
                
                # Identify vulnerability factors
                vulnerability_factors = self._identify_vulnerability_factors(region, region_data)
                
                # Get historical disaster events
                historical_events = self._get_historical_events(region)
                
                # Generate recommendations
                recommendations = self._generate_regional_recommendations(region, regional_risk, vulnerability_factors)
                
                risk_mapping = RiskMapping(
                    region=region,
                    coordinates=region_data['coordinates'],
                    risk_level=self._categorize_risk_level(regional_risk),
                    risk_score=regional_risk,
                    population_at_risk=int(region_data['population'] * (regional_risk / 100) * region_data['vulnerability']),
                    vulnerability_factors=vulnerability_factors,
                    historical_events=historical_events,
                    recommendations=recommendations
                )
                
                risk_mappings.append(risk_mapping)
                
            except Exception as e:
                logger.error(f"Failed to create risk mapping for {region}: {e}")
        
        # Sort by risk score (highest first)
        risk_mappings.sort(key=lambda x: x.risk_score, reverse=True)
        
        return risk_mappings
    
    def aggregate_regional_data(self, region_name: str, hours: int = 24) -> RegionalAggregation:
        """Aggregate weather data across a region.
        
        Args:
            region_name: Name of the region
            hours: Hours of data to aggregate
            
        Returns:
            Regional data aggregation
        """
        logger.info(f"Aggregating regional data for {region_name}")
        
        if region_name not in self.philippine_regions:
            raise ValueError(f"Unknown region: {region_name}")
        
        region_data = self.philippine_regions[region_name]
        
        # Get weather data for major cities in the region
        cities = region_data.get('major_cities', [])
        weather_data_by_city = {}
        
        for city in cities:
            try:
                city_weather = self._get_location_weather_data(f"{city}, PH", hours)
                if city_weather:
                    weather_data_by_city[city] = city_weather
            except Exception as e:
                logger.warning(f"Could not get data for {city}: {e}")
        
        if not weather_data_by_city:
            raise ValueError(f"No weather data available for region {region_name}")
        
        # Calculate averages across all cities
        all_weather_data = []
        for city_data in weather_data_by_city.values():
            all_weather_data.extend(city_data)
        
        average_conditions = self._calculate_average_conditions(all_weather_data)
        extreme_conditions = self._calculate_extreme_conditions(all_weather_data)
        risk_distribution = self._calculate_risk_distribution(weather_data_by_city)
        
        # Calculate coverage area (approximate)
        bbox = region_data['bbox']
        coverage_area = self._calculate_bbox_area(bbox)
        
        return RegionalAggregation(
            region=region_name,
            location_count=len(weather_data_by_city),
            average_conditions=average_conditions,
            extreme_conditions=extreme_conditions,
            risk_distribution=risk_distribution,
            coverage_area_km2=coverage_area
        )
    
    def find_high_risk_areas(self, risk_threshold: float = 0.7) -> List[Dict]:
        """Identify areas with high disaster risk across Philippines.
        
        Args:
            risk_threshold: Minimum risk score to consider high risk
            
        Returns:
            List of high-risk areas with details
        """
        logger.info(f"Finding high-risk areas (threshold: {risk_threshold})")
        
        high_risk_areas = []
        
        # Check all regions
        for region_name in self.philippine_regions:
            try:
                # Get current risk assessment for region
                regional_risk_maps = self.create_regional_risk_map(region_name)
                
                for risk_map in regional_risk_maps:
                    if risk_map.risk_score >= risk_threshold:
                        high_risk_areas.append({
                            'region': risk_map.region,
                            'coordinates': risk_map.coordinates,
                            'risk_score': risk_map.risk_score,
                            'risk_level': risk_map.risk_level,
                            'population_at_risk': risk_map.population_at_risk,
                            'primary_threats': risk_map.vulnerability_factors[:3],  # Top 3
                            'immediate_actions': risk_map.recommendations[:2]  # Top 2
                        })
                        
            except Exception as e:
                logger.error(f"Error assessing risk for {region_name}: {e}")
        
        # Sort by risk score and population at risk
        high_risk_areas.sort(key=lambda x: (x['risk_score'], x['population_at_risk']), reverse=True)
        
        return high_risk_areas
    
    def calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates in kilometers.
        
        Args:
            coord1: First coordinate (lat, lon)
            coord2: Second coordinate (lat, lon)
            
        Returns:
            Distance in kilometers
        """
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    # Helper methods
    def _get_location_weather_data(self, location: str, hours: int) -> List[Dict]:
        """Get weather data for a specific location."""
        from ..models.weather import CurrentWeather
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        query = self.db.query(CurrentWeather).filter(
            and_(
                CurrentWeather.location.ilike(f"%{location.split(',')[0]}%"),
                CurrentWeather.timestamp >= cutoff_time
            )
        ).order_by(CurrentWeather.timestamp.desc())
        
        results = query.all()
        
        return [{
            'timestamp': r.timestamp.isoformat(),
            'temperature': r.temperature,
            'humidity': r.humidity,
            'pressure': r.pressure,
            'wind_speed': r.wind_speed,
            'wind_direction': r.wind_direction,
            'weather_condition': r.weather_condition,
            'coordinates': (r.latitude, r.longitude)
        } for r in results]
    
    def _get_geographic_context(self, location: str) -> Dict:
        """Get geographic context for a location."""
        # Determine which region this location belongs to
        location_name = location.split(',')[0].strip()
        
        for region, region_data in self.philippine_regions.items():
            if location_name in region_data.get('major_cities', []):
                return {
                    'region': region,
                    'region_center': region_data['coordinates'],
                    'vulnerability_score': region_data['vulnerability'],
                    'population': region_data['population'],
                    'geographic_type': self._determine_geographic_type(location_name),
                    'coastal_proximity': self._calculate_coastal_proximity(location_name),
                    'elevation_category': self._estimate_elevation_category(location_name)
                }
        
        # Default context for unknown locations
        return {
            'region': 'Unknown',
            'vulnerability_score': 0.5,
            'geographic_type': 'general',
            'coastal_proximity': 'unknown',
            'elevation_category': 'lowland'
        }
    
    def _calculate_location_risks(self, location: str, weather_data: List[Dict], geo_context: Dict) -> Dict:
        """Calculate location-specific risks based on weather and geography."""
        if not weather_data:
            return {'overall_risk': 0.0, 'risk_factors': []}
        
        base_risk = 0.0
        risk_factors = []
        
        # Get latest weather data
        latest_weather = weather_data[0] if weather_data else {}
        
        # Base weather risks
        if latest_weather.get('wind_speed', 0) > 60:
            base_risk += 0.3
            risk_factors.append('Strong winds')
        
        if latest_weather.get('temperature', 25) > 35:
            base_risk += 0.2
            risk_factors.append('Extreme heat')
        
        if latest_weather.get('humidity', 50) > 85:
            base_risk += 0.2
            risk_factors.append('High humidity')
        
        # Geographic vulnerability multiplier
        vulnerability_multiplier = geo_context.get('vulnerability_score', 0.5)
        total_risk = min(1.0, base_risk * (1 + vulnerability_multiplier))
        
        # Add geographic risk factors
        geographic_type = geo_context.get('geographic_type', 'general')
        if geographic_type in self.vulnerability_factors:
            for factor, score in self.vulnerability_factors[geographic_type].items():
                if score > 0.6:  # Only significant factors
                    risk_factors.append(factor.replace('_', ' ').title())
        
        return {
            'overall_risk': round(total_risk, 2),
            'base_weather_risk': round(base_risk, 2),
            'vulnerability_multiplier': vulnerability_multiplier,
            'risk_factors': risk_factors,
            'risk_level': self._categorize_risk_level(total_risk * 100)
        }
    
    def _find_nearby_locations(self, location: str, radius_km: float = 50) -> List[Dict]:
        """Find nearby locations within specified radius."""
        location_coords = self._get_location_coordinates(location)
        if not location_coords:
            return []
        
        nearby_locations = []
        
        # Check against all known regions and cities
        for region, region_data in self.philippine_regions.items():
            region_coords = region_data['coordinates']
            distance = self.calculate_distance(location_coords, region_coords)
            
            if distance <= radius_km:
                nearby_locations.append({
                    'name': region,
                    'type': 'region',
                    'distance_km': round(distance, 1),
                    'coordinates': region_coords
                })
            
            # Check major cities in the region
            for city in region_data.get('major_cities', []):
                city_coords = self._estimate_city_coordinates(city, region_coords)
                city_distance = self.calculate_distance(location_coords, city_coords)
                
                if city_distance <= radius_km and city_distance > 0:  # Exclude same location
                    nearby_locations.append({
                        'name': city,
                        'type': 'city',
                        'distance_km': round(city_distance, 1),
                        'coordinates': city_coords,
                        'region': region
                    })
        
        # Sort by distance
        nearby_locations.sort(key=lambda x: x['distance_km'])
        
        return nearby_locations[:10]  # Return closest 10
    
    def _assess_regional_impact(self, location: str, location_risks: Dict) -> Dict:
        """Assess potential regional impact of risks from this location."""
        overall_risk = location_risks.get('overall_risk', 0)
        
        if overall_risk < 0.3:
            impact_level = 'LOCAL'
            impact_description = 'Risks are likely contained to immediate area'
        elif overall_risk < 0.6:
            impact_level = 'PROVINCIAL'
            impact_description = 'Risks may affect surrounding municipalities'
        elif overall_risk < 0.8:
            impact_level = 'REGIONAL'
            impact_description = 'Risks may affect multiple provinces in the region'
        else:
            impact_level = 'INTER_REGIONAL'
            impact_description = 'Risks may affect multiple regions'
        
        return {
            'impact_level': impact_level,
            'description': impact_description,
            'estimated_affected_radius_km': min(200, overall_risk * 300),
            'coordination_required': impact_level in ['REGIONAL', 'INTER_REGIONAL']
        }
    
    def _get_regional_weather_data(self, region: str, region_data: Dict) -> List[Dict]:
        """Get aggregated weather data for a region."""
        major_cities = region_data.get('major_cities', [])
        all_regional_data = []
        
        for city in major_cities:
            try:
                city_data = self._get_location_weather_data(f"{city}, PH", 24)
                all_regional_data.extend(city_data)
            except Exception as e:
                logger.warning(f"Could not get data for {city}: {e}")
        
        return all_regional_data
    
    def _calculate_regional_risk(self, region: str, weather_data: List[Dict], region_data: Dict) -> float:
        """Calculate overall risk score for a region."""
        if not weather_data:
            return 0.0
        
        # Base risk from weather conditions
        base_risk = 0.0
        
        # Temperature risk
        temperatures = [w.get('temperature', 25) for w in weather_data]
        if temperatures:
            max_temp = max(temperatures)
            avg_temp = sum(temperatures) / len(temperatures)
            if max_temp > 38:
                base_risk += 30
            elif avg_temp > 32:
                base_risk += 20
        
        # Wind risk
        wind_speeds = [w.get('wind_speed', 0) for w in weather_data]
        if wind_speeds:
            max_wind = max(wind_speeds)
            if max_wind > 120:
                base_risk += 40
            elif max_wind > 90:
                base_risk += 30
            elif max_wind > 60:
                base_risk += 20
        
        # Humidity/precipitation risk
        humidity_values = [w.get('humidity', 50) for w in weather_data]
        if humidity_values:
            avg_humidity = sum(humidity_values) / len(humidity_values)
            if avg_humidity > 90:
                base_risk += 20
            elif avg_humidity > 80:
                base_risk += 10
        
        # Apply regional vulnerability multiplier
        vulnerability = region_data.get('vulnerability', 0.5)
        total_risk = min(100, base_risk * (1 + vulnerability))
        
        return total_risk
    
    def _identify_vulnerability_factors(self, region: str, region_data: Dict) -> List[str]:
        """Identify key vulnerability factors for a region."""
        factors = []
        
        vulnerability_score = region_data.get('vulnerability', 0.5)
        population = region_data.get('population', 0)
        
        # Population density factor
        if population > 10000000:
            factors.append('High population density')
        
        # Geographic factors based on region
        if 'Metro Manila' in region or 'Central Luzon' in region:
            factors.extend(['Urban flooding risk', 'Infrastructure vulnerability', 'Traffic congestion during evacuation'])
        
        if 'Visayas' in region:
            factors.extend(['Typhoon corridor exposure', 'Island isolation', 'Storm surge vulnerability'])
        
        if 'Mindanao' in region:
            factors.extend(['Flood plains', 'Agricultural vulnerability'])
        
        # Coastal areas
        coastal_regions = ['Metro Manila', 'Central Visayas', 'Western Visayas']
        if any(coastal in region for coastal in coastal_regions):
            factors.extend(['Storm surge risk', 'Sea level rise impact'])
        
        # High vulnerability regions
        if vulnerability_score > 0.7:
            factors.append('High historical disaster frequency')
        
        return factors[:5]  # Return top 5 factors
    
    def _get_historical_events(self, region: str) -> List[Dict]:
        """Get historical disaster events for a region."""
        # Philippine historical disaster data (simplified)
        historical_events = {
            'Metro Manila': [
                {'year': 2009, 'event': 'Typhoon Ondoy', 'impact': 'Severe flooding', 'casualties': 464},
                {'year': 2020, 'event': 'Typhoon Ulysses', 'impact': 'Metro-wide flooding', 'casualties': 73},
                {'year': 2012, 'event': 'Habagat flooding', 'impact': 'Widespread flooding', 'casualties': 95}
            ],
            'Central Visayas': [
                {'year': 2013, 'event': 'Typhoon Yolanda', 'impact': 'Catastrophic damage', 'casualties': 6300},
                {'year': 2021, 'event': 'Typhoon Rai', 'impact': 'Severe infrastructure damage', 'casualties': 405}
            ],
            'Western Visayas': [
                {'year': 2013, 'event': 'Typhoon Yolanda', 'impact': 'Severe damage', 'casualties': 500},
                {'year': 2020, 'event': 'Typhoon Molave', 'impact': 'Agricultural damage', 'casualties': 22}
            ],
            'Davao Region': [
                {'year': 2012, 'event': 'Typhoon Pablo', 'impact': 'Landslides and flooding', 'casualties': 1000},
                {'year': 2019, 'event': 'Earthquake series', 'impact': 'Infrastructure damage', 'casualties': 24}
            ]
        }
        
        return historical_events.get(region, [])
    
    def _generate_regional_recommendations(self, region: str, risk_score: float, vulnerability_factors: List[str]) -> List[str]:
        """Generate region-specific recommendations."""
        recommendations = []
        
        # High risk recommendations
        if risk_score >= 70:
            recommendations.extend([
                'Activate regional emergency response protocols',
                'Coordinate with national disaster agencies',
                'Prepare mass evacuation if necessary'
            ])
        elif risk_score >= 50:
            recommendations.extend([
                'Enhance monitoring and early warning systems',
                'Prepare emergency supplies and equipment',
                'Review evacuation plans and routes'
            ])
        
        # Vulnerability-specific recommendations
        if 'High population density' in vulnerability_factors:
            recommendations.append('Focus on mass communication and traffic management')
        
        if 'Storm surge risk' in vulnerability_factors:
            recommendations.append('Monitor sea levels and prepare coastal evacuations')
        
        if 'Urban flooding risk' in vulnerability_factors:
            recommendations.append('Clear drainage systems and deploy flood barriers')
        
        if 'Typhoon corridor exposure' in vulnerability_factors:
            recommendations.append('Track storm development and prepare for sustained winds')
        
        # Region-specific recommendations
        if 'Metro Manila' in region:
            recommendations.append('Coordinate with MMDA for traffic and evacuation management')
        elif 'Visayas' in region:
            recommendations.append('Ensure inter-island communication and transport readiness')
        elif 'Mindanao' in region:
            recommendations.append('Focus on agricultural protection and rural area communication')
        
        return recommendations[:6]  # Return top 6 recommendations
    
    def _calculate_average_conditions(self, weather_data: List[Dict]) -> Dict[str, float]:
        """Calculate average weather conditions."""
        if not weather_data:
            return {}
        
        temp_values = [w.get('temperature', 0) for w in weather_data if w.get('temperature')]
        humidity_values = [w.get('humidity', 0) for w in weather_data if w.get('humidity')]
        pressure_values = [w.get('pressure', 0) for w in weather_data if w.get('pressure')]
        wind_values = [w.get('wind_speed', 0) for w in weather_data if w.get('wind_speed')]
        
        return {
            'temperature': round(sum(temp_values) / len(temp_values), 1) if temp_values else 0,
            'humidity': round(sum(humidity_values) / len(humidity_values), 1) if humidity_values else 0,
            'pressure': round(sum(pressure_values) / len(pressure_values), 1) if pressure_values else 0,
            'wind_speed': round(sum(wind_values) / len(wind_values), 1) if wind_values else 0
        }
    
    def _calculate_extreme_conditions(self, weather_data: List[Dict]) -> Dict[str, float]:
        """Calculate extreme weather conditions."""
        if not weather_data:
            return {}
        
        temp_values = [w.get('temperature', 0) for w in weather_data if w.get('temperature')]
        humidity_values = [w.get('humidity', 0) for w in weather_data if w.get('humidity')]
        pressure_values = [w.get('pressure', 0) for w in weather_data if w.get('pressure')]
        wind_values = [w.get('wind_speed', 0) for w in weather_data if w.get('wind_speed')]
        
        return {
            'max_temperature': max(temp_values) if temp_values else 0,
            'min_temperature': min(temp_values) if temp_values else 0,
            'max_humidity': max(humidity_values) if humidity_values else 0,
            'min_pressure': min(pressure_values) if pressure_values else 0,
            'max_wind_speed': max(wind_values) if wind_values else 0
        }
    
    def _calculate_risk_distribution(self, weather_data_by_city: Dict[str, List[Dict]]) -> Dict[str, int]:
        """Calculate risk level distribution across cities."""
        risk_distribution = {'LOW': 0, 'MODERATE': 0, 'HIGH': 0, 'CRITICAL': 0}
        
        for city, weather_data in weather_data_by_city.items():
            if not weather_data:
                continue
            
            # Simple risk calculation based on latest data
            latest = weather_data[0] if weather_data else {}
            
            risk_score = 0
            if latest.get('wind_speed', 0) > 60:
                risk_score += 30
            if latest.get('temperature', 25) > 35:
                risk_score += 20
            if latest.get('humidity', 50) > 85:
                risk_score += 20
            
            if risk_score >= 50:
                risk_level = 'CRITICAL' if risk_score >= 70 else 'HIGH'
            elif risk_score >= 20:
                risk_level = 'MODERATE'
            else:
                risk_level = 'LOW'
            
            risk_distribution[risk_level] += 1
        
        return risk_distribution
    
    def _calculate_bbox_area(self, bbox: List[Tuple[float, float]]) -> float:
        """Calculate approximate area of bounding box in km²."""
        if len(bbox) != 2:
            return 0.0
        
        # Simple rectangular area calculation
        lat1, lon1 = bbox[0]
        lat2, lon2 = bbox[1]
        
        # Convert to kilometers (rough approximation)
        lat_km = abs(lat2 - lat1) * 111  # 1 degree lat ≈ 111 km
        lon_km = abs(lon2 - lon1) * 111 * math.cos(math.radians((lat1 + lat2) / 2))
        
        return lat_km * lon_km
    
    def _categorize_risk_level(self, risk_score: float) -> str:
        """Categorize risk level based on score."""
        if risk_score >= 80:
            return "CRITICAL"
        elif risk_score >= 60:
            return "HIGH"
        elif risk_score >= 40:
            return "MODERATE"
        elif risk_score >= 20:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _get_location_coordinates(self, location: str) -> Optional[Tuple[float, float]]:
        """Get coordinates for a location."""
        location_name = location.split(',')[0].strip()
        
        # Check if it's a major city
        for region_data in self.philippine_regions.values():
            if location_name in region_data.get('major_cities', []):
                # Estimate city coordinates near region center
                return self._estimate_city_coordinates(location_name, region_data['coordinates'])
        
        # Check if it's a region
        for region, region_data in self.philippine_regions.items():
            if location_name.lower() in region.lower():
                return region_data['coordinates']
        
        return None
    
    def _estimate_city_coordinates(self, city_name: str, region_center: Tuple[float, float]) -> Tuple[float, float]:
        """Estimate city coordinates based on region center."""
        # Add small random offset to region center for cities
        lat, lon = region_center
        
        # City-specific offsets (simplified)
        city_offsets = {
            'Manila': (0.05, 0.0),
            'Quezon City': (0.1, 0.05),
            'Makati': (0.02, 0.02),
            'Cebu City': (0.0, 0.1),
            'Davao City': (0.0, 0.0),
            'Iloilo City': (0.1, 0.0),
            'Bacolod': (0.3, 0.1)
        }
        
        offset = city_offsets.get(city_name, (0.05, 0.05))  # Default small offset
        return (lat + offset[0], lon + offset[1])
    
    def _determine_geographic_type(self, location_name: str) -> str:
        """Determine geographic type of location."""
        # Simple classification based on location name
        coastal_cities = ['Manila', 'Cebu City', 'Iloilo City', 'Bacolod', 'Davao City']
        mountainous_cities = ['Baguio', 'Tagaytay']
        urban_centers = ['Manila', 'Quezon City', 'Makati', 'Cebu City', 'Davao City']
        
        if location_name in coastal_cities:
            return 'coastal'
        elif location_name in mountainous_cities:
            return 'mountainous'
        elif location_name in urban_centers:
            return 'urban'
        else:
            return 'general'
    
    def _calculate_coastal_proximity(self, location_name: str) -> str:
        """Calculate proximity to coast."""
        coastal_cities = ['Manila', 'Cebu City', 'Iloilo City', 'Bacolod', 'Davao City']
        inland_cities = ['Angeles', 'San Jose del Monte', 'Antipolo']
        
        if location_name in coastal_cities:
            return 'coastal'
        elif location_name in inland_cities:
            return 'inland'
        else:
            return 'moderate'
    
    def _estimate_elevation_category(self, location_name: str) -> str:
        """Estimate elevation category."""
        highland_cities = ['Baguio', 'Tagaytay']
        lowland_cities = ['Manila', 'Cebu City', 'Davao City']
        
        if location_name in highland_cities:
            return 'highland'
        elif location_name in lowland_cities:
            return 'lowland'
        else:
            return 'moderate'


# Integration with API
def add_geospatial_endpoints(router, db_dependency):
    """Add geospatial endpoints to existing router."""
    
    @router.post("/geospatial/process-locations")
    async def process_multiple_locations(
        locations: List[str],
        hours: int = 24,
        db: Session = db_dependency
    ):
        """Process weather data for multiple locations with geospatial context."""
        try:
            geo_service = GeospatialService(db)
            processed_data = geo_service.process_location_data(locations, hours)
            
            return {
                "status": "success",
                "locations_processed": len(locations),
                "hours_analyzed": hours,
                "data": processed_data,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Location processing failed: {e}")
            return {"status": "error", "message": str(e)}
    
    @router.get("/geospatial/regional-risk-map")
    async def get_regional_risk_map(
        region: Optional[str] = None,
        db: Session = db_dependency
    ):
        """Get risk mapping for specified region or all Philippines."""
        try:
            geo_service = GeospatialService(db)
            risk_mappings = geo_service.create_regional_risk_map(region)
            
            return {
                "status": "success",
                "region": region or "All Philippines",
                "risk_mappings": [
                    {
                        "region": rm.region,
                        "coordinates": rm.coordinates,
                        "risk_level": rm.risk_level,
                        "risk_score": rm.risk_score,
                        "population_at_risk": rm.population_at_risk,
                        "vulnerability_factors": rm.vulnerability_factors,
                        "recommendations": rm.recommendations,
                        "historical_events_count": len(rm.historical_events)
                    } for rm in risk_mappings
                ],
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Regional risk mapping failed: {e}")
            return {"status": "error", "message": str(e)}
    
    @router.get("/geospatial/regional-aggregation/{region_name}")
    async def get_regional_aggregation(
        region_name: str,
        hours: int = 24,
        db: Session = db_dependency
    ):
        """Get aggregated weather data for a region."""
        try:
            geo_service = GeospatialService(db)
            aggregation = geo_service.aggregate_regional_data(region_name, hours)
            
            return {
                "status": "success",
                "regional_data": {
                    "region": aggregation.region,
                    "location_count": aggregation.location_count,
                    "average_conditions": aggregation.average_conditions,
                    "extreme_conditions": aggregation.extreme_conditions,
                    "risk_distribution": aggregation.risk_distribution,
                    "coverage_area_km2": aggregation.coverage_area_km2
                },
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Regional aggregation failed: {e}")
            return {"status": "error", "message": str(e)}
    
    @router.get("/geospatial/high-risk-areas")
    async def get_high_risk_areas(
        risk_threshold: float = 0.7,
        db: Session = db_dependency
    ):
        """Identify areas with high disaster risk."""
        try:
            geo_service = GeospatialService(db)
            high_risk_areas = geo_service.find_high_risk_areas(risk_threshold)
            
            return {
                "status": "success",
                "risk_threshold": risk_threshold,
                "high_risk_areas_count": len(high_risk_areas),
                "areas": high_risk_areas,
                "total_population_at_risk": sum(area['population_at_risk'] for area in high_risk_areas),
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"High risk area identification failed: {e}")
            return {"status": "error", "message": str(e)}