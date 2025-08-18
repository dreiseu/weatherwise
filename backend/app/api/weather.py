"""
Weather API Endpoints
Handles weather data retrieval and analysis
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from uuid import UUID
import logging

from ..core.database import get_db
from ..models.weather import CurrentWeather, WeatherForecast
from ..services.weather_service import OpenWeatherService
from ..services.data_validator import WeatherDataValidator
from ..services.monitoring import WeatherMonitoring
from ..services.weather_analysis import WeatherAnalysisService
from ..services.geospatial_service import GeospatialService

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize services
weather_service = OpenWeatherService()
validator = WeatherDataValidator()
monitor = WeatherMonitoring()

# Pydantic models for API responses
class WeatherResponse(BaseModel):
    """Weather data response model."""
    id: UUID  
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
    timestamp: datetime
    
    class Config:
        from_attributes = True


class ForecastResponse(BaseModel):
    """Forecast data response model."""
    id: str
    location: str
    forecast_date: datetime
    temperature_min: float
    temperature_max: float
    humidity: int
    wind_speed: float
    pressure: float
    weather_condition: str
    weather_description: str
    precipitation_probability: int
    
    class Config:
        from_attributes = True


class WeatherAnalysisRequest(BaseModel):
    """Weather analysis request model."""
    location: str
    analysis_type: str = "risk_assessment"
    time_range: str = "24h"
    include_historical: bool = True

class AdvancedAnalysisRequest(BaseModel):
    """Advanced weather analysis request model."""
    location: str = Field(..., description="Location to analyze")
    analysis_types: List[str] = Field(
        default=["patterns", "anomalies", "risk_score", "trends"],
        description="Types of analysis to perform"
    )
    time_range: str = Field(default="24h", description="Time range for analysis")
    include_geospatial: bool = Field(default=True, description="Include geospatial context")
    include_forecasts: bool = Field(default=True, description="Include forecast analysis")


class WeatherAnalysisResponse(BaseModel):
    """Weather analysis response model."""
    analysis_id: str
    location: str
    risk_level: str
    confidence_score: float
    summary: str
    recommendations: List[str]
    generated_at: datetime

class ComprehensiveAnalysisResponse(BaseModel):
    """Comprehensive analysis response model."""
    location: str
    analysis_period: str
    risk_assessment: Dict[str, Any]
    weather_patterns: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    trend_analysis: Dict[str, Any]
    geospatial_context: Optional[Dict[str, Any]] = None
    recommendations: List[str]
    confidence_score: float
    generated_at: datetime

class MultiLocationRequest(BaseModel):
    """Multi-location analysis request."""
    locations: List[str] = Field(..., min_items=1, max_items=10)
    analysis_type: str = Field(default="comparison", description="Type of multi-location analysis")
    hours: int = Field(default=24, ge=1, le=168, description="Hours of data to analyze")


class RegionalRiskRequest(BaseModel):
    """Regional risk assessment request."""
    region: Optional[str] = Field(None, description="Specific region (optional for all Philippines)")
    risk_threshold: float = Field(default=0.6, ge=0.0, le=1.0, description="Risk threshold")
    include_population_data: bool = Field(default=True, description="Include population impact")
    include_historical: bool = Field(default=True, description="Include historical events")


@router.get("/current", response_model=List[WeatherResponse])
async def get_current_weather(
    location: Optional[str] = Query(None, description="Filter by location"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    db: Session = Depends(get_db)
):
    """Get current weather data from database."""
    
    query = db.query(CurrentWeather)
    
    if location:
        query = query.filter(CurrentWeather.location.ilike(f"%{location}%"))
    
    # Get most recent records
    weather_data = query.order_by(desc(CurrentWeather.timestamp)).limit(limit).all()
    
    if not weather_data:
        raise HTTPException(status_code=404, detail="No weather data found")
    
    return weather_data


@router.get("/current/{location}")
async def get_current_weather_by_location(
    location: str,
    db: Session = Depends(get_db)
):
    """Get latest weather data for specific location."""
    
    weather_data = db.query(CurrentWeather).filter(
        CurrentWeather.location == location
    ).order_by(desc(CurrentWeather.timestamp)).first()
    
    if not weather_data:
        raise HTTPException(status_code=404, detail=f"No weather data found for {location}")
    
    return weather_data


@router.post("/current/fetch")
async def fetch_current_weather(
    location: str = Query(..., description="Location to fetch weather for"),
    db: Session = Depends(get_db)
):
    """Fetch fresh weather data from API and store in database."""
    
    try:
        # Fetch from weather API
        weather_data = weather_service.get_current_weather(location)
        
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
        
        # Validate data
        validation_result = validator.validate_current_weather(weather_dict)
        
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=422, 
                detail=f"Data validation failed: {validation_result.errors}"
            )
        
        # Store in database
        cleaned_data = validation_result.cleaned_data
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
            timestamp=datetime.now()
        )
        
        db.add(db_weather)
        db.commit()
        db.refresh(db_weather)
        
        return {
            "message": f"Weather data fetched and stored for {location}",
            "data": db_weather,
            "warnings": validation_result.warnings
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather data: {str(e)}")


@router.get("/forecast", response_model=List[ForecastResponse])
async def get_weather_forecast(
    location: Optional[str] = Query(None, description="Filter by location"),
    days: int = Query(3, ge=1, le=7, description="Number of days"),
    db: Session = Depends(get_db)
):
    """Get weather forecast data from database."""
    
    # Calculate date range
    start_date = datetime.now()
    end_date = start_date + timedelta(days=days)
    
    query = db.query(WeatherForecast).filter(
        and_(
            WeatherForecast.forecast_date >= start_date,
            WeatherForecast.forecast_date <= end_date
        )
    )
    
    if location:
        query = query.filter(WeatherForecast.location.ilike(f"%{location}%"))
    
    forecast_data = query.order_by(WeatherForecast.forecast_date).all()
    
    if not forecast_data:
        raise HTTPException(status_code=404, detail="No forecast data found")
    
    return forecast_data


@router.post("/forecast/fetch")
async def fetch_weather_forecast(
    location: str = Query(..., description="Location to fetch forecast for"),
    days: int = Query(3, ge=1, le=5, description="Number of days to forecast"),
    db: Session = Depends(get_db)
):
    """Fetch fresh forecast data from API and store in database."""
    
    try:
        # Fetch forecast from weather API
        forecast_data = weather_service.get_weather_forecast(location, days)
        
        # Store each forecast entry
        stored_count = 0
        for forecast in forecast_data:
            db_forecast = WeatherForecast(
                location=location,
                latitude=0,  # We'll need coordinates from location lookup
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
        
        return {
            "message": f"Forecast data fetched and stored for {location}",
            "entries_stored": stored_count,
            "days": days
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to fetch forecast data: {str(e)}")


@router.get("/locations")
async def get_available_locations(db: Session = Depends(get_db)):
    """Get list of available weather data locations."""
    
    # Get unique locations from current weather data
    locations = db.query(CurrentWeather.location).distinct().all()
    location_list = [loc[0] for loc in locations]
    
    if not location_list:
        return {"locations": [], "count": 0}
    
    return {
        "locations": location_list,
        "count": len(location_list)
    }


@router.get("/statistics/{location}")
async def get_weather_statistics(
    location: str,
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get weather statistics for a location."""
    
    # Calculate date range
    start_date = datetime.now() - timedelta(days=days)
    
    weather_data = db.query(CurrentWeather).filter(
        and_(
            CurrentWeather.location == location,
            CurrentWeather.timestamp >= start_date
        )
    ).all()
    
    if not weather_data:
        raise HTTPException(status_code=404, detail=f"No weather data found for {location}")
    
    # Calculate statistics
    temperatures = [w.temperature for w in weather_data]
    humidities = [w.humidity for w in weather_data]
    pressures = [w.pressure for w in weather_data]
    wind_speeds = [w.wind_speed for w in weather_data]
    
    statistics = {
        "location": location,
        "period_days": days,
        "total_records": len(weather_data),
        "temperature": {
            "min": min(temperatures),
            "max": max(temperatures),
            "average": sum(temperatures) / len(temperatures)
        },
        "humidity": {
            "min": min(humidities),
            "max": max(humidities),
            "average": sum(humidities) / len(humidities)
        },
        "pressure": {
            "min": min(pressures),
            "max": max(pressures),
            "average": sum(pressures) / len(pressures)
        },
        "wind_speed": {
            "min": min(wind_speeds),
            "max": max(wind_speeds),
            "average": sum(wind_speeds) / len(wind_speeds)
        }
    }
    
    return statistics


@router.post("/analyze", response_model=WeatherAnalysisResponse)
async def analyze_weather_data(
    request: WeatherAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze weather data and provide risk assessment."""
    
    # This is a placeholder for AI analysis integration
    # In a full implementation, this would use your AI agents
    
    import uuid
    
    # Get recent weather data for the location
    recent_data = db.query(CurrentWeather).filter(
        CurrentWeather.location == request.location
    ).order_by(desc(CurrentWeather.timestamp)).limit(10).all()
    
    if not recent_data:
        raise HTTPException(status_code=404, detail=f"No weather data available for {request.location}")
    
    # Simple risk assessment based on current conditions
    latest = recent_data[0]
    risk_level = "LOW"
    recommendations = []
    
    # Basic risk assessment logic
    if latest.temperature > 35 or latest.temperature < 15:
        risk_level = "MODERATE"
        recommendations.append("Monitor temperature extremes")
    
    if latest.wind_speed > 40:
        risk_level = "HIGH"
        recommendations.append("Prepare for strong winds")
    
    if latest.humidity > 85:
        risk_level = "MODERATE"
        recommendations.append("High humidity may indicate storm conditions")
    
    if not recommendations:
        recommendations.append("Current weather conditions are within normal ranges")
    
    return WeatherAnalysisResponse(
        analysis_id=str(uuid.uuid4()),
        location=request.location,
        risk_level=risk_level,
        confidence_score=0.85,
        summary=f"Weather analysis for {request.location} shows {risk_level.lower()} risk conditions",
        recommendations=recommendations,
        generated_at=datetime.now()
    )

@router.post("/analyze/comprehensive", response_model=ComprehensiveAnalysisResponse)
async def comprehensive_weather_analysis(
    request: AdvancedAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Perform comprehensive weather analysis including patterns, anomalies, risks, and trends."""
    
    try:
        logger.info(f"Starting comprehensive analysis for {request.location}")
        
        # Initialize analysis services
        analysis_service = WeatherAnalysisService(db)
        geo_service = GeospatialService(db) if request.include_geospatial else None
        
        # Parse time range
        hours = parse_time_range(request.time_range)
        
        # Perform different types of analysis based on request
        results = {}
        
        # 1. Risk Assessment
        if "risk_score" in request.analysis_types:
            risk_assessment = analysis_service.calculate_risk_scores(
                request.location, 
                forecast_hours=hours if request.include_forecasts else 0
            )
            results['risk_assessment'] = {
                "overall_risk": risk_assessment.overall_risk,
                "risk_level": risk_assessment.risk_level,
                "confidence": risk_assessment.confidence,
                "category_risks": risk_assessment.category_risks,
                "contributing_factors": risk_assessment.contributing_factors,
                "recommendations": risk_assessment.recommendations
            }
        
        # 2. Weather Patterns
        if "patterns" in request.analysis_types:
            patterns = analysis_service.analyze_weather_patterns(
                request.location, 
                days=hours // 24 or 1
            )
            results['weather_patterns'] = [
                {
                    "type": p.pattern_type,
                    "confidence": p.confidence,
                    "description": p.description,
                    "risk_level": p.risk_level,
                    "indicators": p.indicators,
                    "timeline": p.timeline
                } for p in patterns
            ]
        
        # 3. Anomaly Detection
        if "anomalies" in request.analysis_types:
            anomalies = analysis_service.detect_anomalies(
                request.location,
                days=min(7, hours // 24 or 3)
            )
            results['anomalies'] = [
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
        
        # 4. Trend Analysis
        if "trends" in request.analysis_types:
            trends = analysis_service.analyze_trends(
                request.location,
                days=min(14, hours // 24 or 7)
            )
            results['trend_analysis'] = trends
        
        # 5. Geospatial Context
        geospatial_context = None
        if request.include_geospatial and geo_service:
            location_data = geo_service.process_location_data([request.location], hours)
            geospatial_context = location_data.get(request.location, {})
        
        # Compile comprehensive recommendations
        all_recommendations = []
        if 'risk_assessment' in results:
            all_recommendations.extend(results['risk_assessment']['recommendations'])
        if 'trend_analysis' in results and 'assessment' in results['trend_analysis']:
            trend_rec = results['trend_analysis']['assessment'].get('recommendation')
            if trend_rec:
                all_recommendations.append(trend_rec)
        
        # Calculate overall confidence score
        confidence_scores = []
        if 'risk_assessment' in results:
            confidence_scores.append(results['risk_assessment']['confidence'])
        if 'weather_patterns' in results:
            pattern_confidences = [p['confidence'] for p in results['weather_patterns']]
            if pattern_confidences:
                confidence_scores.append(sum(pattern_confidences) / len(pattern_confidences))
        if 'anomalies' in results:
            anomaly_confidences = [a['confidence'] for a in results['anomalies']]
            if anomaly_confidences:
                confidence_scores.append(sum(anomaly_confidences) / len(anomaly_confidences))
        
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.7
        
        # Log analysis completion in background
        background_tasks.add_task(
            log_analysis_completion,
            request.location,
            request.analysis_types,
            len(all_recommendations)
        )
        
        return ComprehensiveAnalysisResponse(
            location=request.location,
            analysis_period=request.time_range,
            risk_assessment=results.get('risk_assessment', {}),
            weather_patterns=results.get('weather_patterns', []),
            anomalies=results.get('anomalies', []),
            trend_analysis=results.get('trend_analysis', {}),
            geospatial_context=geospatial_context,
            recommendations=list(set(all_recommendations)),  # Remove duplicates
            confidence_score=round(overall_confidence, 2),
            generated_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Comprehensive analysis failed for {request.location}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/analyze/multi-location")
async def multi_location_analysis(
    request: MultiLocationRequest,
    db: Session = Depends(get_db)
):
    """Analyze multiple locations for comparison and regional assessment."""
    
    try:
        logger.info(f"Multi-location analysis for {len(request.locations)} locations")
        
        geo_service = GeospatialService(db)
        analysis_service = WeatherAnalysisService(db)
        
        if request.analysis_type == "comparison":
            # Process all locations
            location_data = geo_service.process_location_data(request.locations, request.hours)
            
            # Create comparison matrix
            comparison_results = []
            for location, data in location_data.items():
                if 'error' not in data:
                    comparison_results.append({
                        'location': location,
                        'risk_assessment': data.get('risk_assessment', {}),
                        'geographic_context': data.get('geographic_context', {}),
                        'nearby_locations_count': len(data.get('nearby_locations', [])),
                        'regional_impact': data.get('regional_impact', {})
                    })
            
            # Sort by risk level
            comparison_results.sort(
                key=lambda x: x['risk_assessment'].get('overall_risk', 0), 
                reverse=True
            )
            
            return {
                "status": "success",
                "analysis_type": "comparison",
                "locations_analyzed": len(comparison_results),
                "hours_analyzed": request.hours,
                "comparison_results": comparison_results,
                "summary": {
                    "highest_risk_location": comparison_results[0]['location'] if comparison_results else None,
                    "average_risk": round(
                        sum(r['risk_assessment'].get('overall_risk', 0) for r in comparison_results) / 
                        len(comparison_results), 2
                    ) if comparison_results else 0,
                    "locations_with_high_risk": len([
                        r for r in comparison_results 
                        if r['risk_assessment'].get('overall_risk', 0) > 0.6
                    ])
                },
                "analyzed_at": datetime.now().isoformat()
            }
            
        elif request.analysis_type == "regional_aggregation":
            # Group locations by region and aggregate
            regional_data = {}
            
            for location in request.locations:
                try:
                    # Determine region for location
                    location_processed = geo_service.process_location_data([location], request.hours)
                    if location in location_processed and 'geographic_context' in location_processed[location]:
                        region = location_processed[location]['geographic_context'].get('region', 'Unknown')
                        
                        if region not in regional_data:
                            regional_data[region] = {
                                'locations': [],
                                'total_risk': 0,
                                'risk_factors': set()
                            }
                        
                        regional_data[region]['locations'].append(location)
                        risk_data = location_processed[location].get('risk_assessment', {})
                        regional_data[region]['total_risk'] += risk_data.get('overall_risk', 0)
                        regional_data[region]['risk_factors'].update(risk_data.get('risk_factors', []))
                        
                except Exception as e:
                    logger.warning(f"Could not process {location}: {e}")
            
            # Calculate regional averages
            regional_summary = {}
            for region, data in regional_data.items():
                location_count = len(data['locations'])
                avg_risk = data['total_risk'] / location_count if location_count > 0 else 0
                
                regional_summary[region] = {
                    'location_count': location_count,
                    'average_risk': round(avg_risk, 2),
                    'risk_level': categorize_risk_level(avg_risk),
                    'locations': data['locations'],
                    'common_risk_factors': list(data['risk_factors'])[:5]  # Top 5
                }
            
            return {
                "status": "success",
                "analysis_type": "regional_aggregation",
                "regions_analyzed": len(regional_summary),
                "total_locations": len(request.locations),
                "regional_summary": regional_summary,
                "analyzed_at": datetime.now().isoformat()
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown analysis type: {request.analysis_type}")
            
    except Exception as e:
        logger.error(f"Multi-location analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze/regional-risk")
async def regional_risk_assessment(
    request: RegionalRiskRequest,
    db: Session = Depends(get_db)
):
    """Perform regional risk assessment across Philippine regions."""
    
    try:
        logger.info(f"Regional risk assessment for: {request.region or 'All Philippines'}")
        
        geo_service = GeospatialService(db)
        
        # Get regional risk mappings
        risk_mappings = geo_service.create_regional_risk_map(request.region)
        
        # Filter by risk threshold
        high_risk_mappings = [
            rm for rm in risk_mappings 
            if rm.risk_score >= request.risk_threshold * 100
        ]
        
        # Calculate statistics
        total_population_at_risk = sum(rm.population_at_risk for rm in high_risk_mappings)
        
        # Get high-risk areas
        high_risk_areas = geo_service.find_high_risk_areas(request.risk_threshold)
        
        # Compile regional insights
        regional_insights = []
        for rm in risk_mappings[:5]:  # Top 5 regions by risk
            insights = {
                'region': rm.region,
                'risk_score': rm.risk_score,
                'risk_level': rm.risk_level,
                'population_at_risk': rm.population_at_risk,
                'key_vulnerabilities': rm.vulnerability_factors[:3],
                'immediate_recommendations': rm.recommendations[:3],
                'historical_events_impact': len(rm.historical_events) > 0
            }
            regional_insights.append(insights)
        
        return {
            "status": "success",
            "assessment_scope": request.region or "National (Philippines)",
            "risk_threshold": request.risk_threshold,
            "total_regions_assessed": len(risk_mappings),
            "high_risk_regions_count": len(high_risk_mappings),
            "total_population_at_risk": total_population_at_risk,
            "regional_insights": regional_insights,
            "high_risk_areas": high_risk_areas[:10],  # Top 10 high-risk areas
            "national_summary": {
                "average_risk_score": round(
                    sum(rm.risk_score for rm in risk_mappings) / len(risk_mappings), 1
                ) if risk_mappings else 0,
                "highest_risk_region": risk_mappings[0].region if risk_mappings else None,
                "regions_requiring_immediate_attention": len([
                    rm for rm in risk_mappings if rm.risk_score >= 80
                ])
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Regional risk assessment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")


@router.get("/analyze/quick-risk/{location}")
async def quick_risk_assessment(
    location: str,
    db: Session = Depends(get_db)
):
    """Get quick risk assessment for a specific location."""
    
    try:
        analysis_service = WeatherAnalysisService(db)
        
        # Get quick risk score
        risk_score = analysis_service.calculate_risk_scores(location, forecast_hours=6)
        
        # Get recent anomalies
        anomalies = analysis_service.detect_anomalies(location, days=1)
        high_severity_anomalies = [a for a in anomalies if a.severity in ['HIGH', 'CRITICAL']]
        
        # Quick pattern check
        patterns = analysis_service.analyze_weather_patterns(location, days=2)
        urgent_patterns = [p for p in patterns if p.risk_level in ['HIGH', 'CRITICAL']]
        
        return {
            "status": "success",
            "location": location,
            "quick_assessment": {
                "overall_risk": risk_score.overall_risk,
                "risk_level": risk_score.risk_level,
                "confidence": risk_score.confidence,
                "immediate_concerns": [
                    f"High severity anomalies: {len(high_severity_anomalies)}",
                    f"Urgent patterns: {len(urgent_patterns)}"
                ],
                "top_recommendations": risk_score.recommendations[:3],
                "category_breakdown": risk_score.category_risks
            },
            "alerts": {
                "high_severity_anomalies": len(high_severity_anomalies),
                "urgent_patterns": len(urgent_patterns),
                "requires_immediate_attention": (
                    risk_score.overall_risk > 0.7 or 
                    len(high_severity_anomalies) > 0 or 
                    len(urgent_patterns) > 0
                )
            },
            "assessed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Quick risk assessment failed for {location}: {e}")
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")


@router.get("/analyze/performance-metrics")
async def get_analysis_performance_metrics(db: Session = Depends(get_db)):
    """Get performance metrics for the analysis system."""
    
    try:
        # Get monitoring data
        performance_summary = monitor.get_performance_summary()
        
        # Database query performance
        db_performance = {}
        try:
            # Test query performance
            start_time = datetime.now()
            recent_count = db.query(CurrentWeather).filter(
                CurrentWeather.timestamp >= datetime.now() - timedelta(hours=24)
            ).count()
            query_time = (datetime.now() - start_time).total_seconds()
            
            db_performance = {
                "recent_records_count": recent_count,
                "query_response_time_ms": round(query_time * 1000, 2),
                "database_status": "healthy" if query_time < 1.0 else "slow"
            }
        except Exception as e:
            db_performance = {"error": str(e), "database_status": "error"}
        
        # Analysis capabilities status
        analysis_status = {
            "weather_patterns": "operational",
            "anomaly_detection": "operational", 
            "risk_assessment": "operational",
            "trend_analysis": "operational",
            "geospatial_processing": "operational"
        }
        
        return {
            "status": "success",
            "system_performance": performance_summary,
            "database_performance": db_performance,
            "analysis_capabilities": analysis_status,
            "system_health": {
                "overall_status": "healthy",
                "last_updated": datetime.now().isoformat(),
                "uptime_info": "System operational"
            }
        }
        
    except Exception as e:
        logger.error(f"Performance metrics retrieval failed: {e}")
        return {
            "status": "error", 
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


# Helper functions
def parse_time_range(time_range: str) -> int:
    """Parse time range string to hours."""
    if time_range.endswith('h'):
        return int(time_range[:-1])
    elif time_range.endswith('d'):
        return int(time_range[:-1]) * 24
    elif time_range.endswith('w'):
        return int(time_range[:-1]) * 24 * 7
    else:
        return 24  # Default to 24 hours


def categorize_risk_level(risk_score: float) -> str:
    """Categorize risk level based on score."""
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


async def log_analysis_completion(location: str, analysis_types: List[str], recommendations_count: int):
    """Background task to log analysis completion."""
    logger.info(
        f"Analysis completed for {location}: "
        f"types={analysis_types}, recommendations={recommendations_count}"
    )

@router.post("/rag/analyze")
async def rag_weather_analysis(
    location: str,
    query: str,
    db: Session = Depends(get_db)
):
    """Get AI-powered weather analysis using RAG system."""
    
    try:
        from ..services.rag_service import RAGService
        
        rag_service = RAGService()
        
        # Get current weather data for the location
        weather_data = db.query(CurrentWeather).filter(
            CurrentWeather.location == location
        ).order_by(desc(CurrentWeather.timestamp)).first()
        
        if not weather_data:
            raise HTTPException(status_code=404, detail=f"No weather data found for {location}")
        
        # Convert to dict for RAG analysis
        weather_dict = {
            "location": weather_data.location,
            "temperature": weather_data.temperature,
            "humidity": weather_data.humidity,
            "wind_speed": weather_data.wind_speed,
            "pressure": weather_data.pressure,
            "weather_condition": weather_data.weather_condition
        }
        
        # Generate RAG analysis
        result = rag_service.generate_weather_analysis(weather_dict, query)
        
        return {
            "status": "success",
            "location": location,
            "query": query,
            "weather_conditions": weather_dict,
            "knowledge_sources_found": result["knowledge_sources"],
            "relevant_knowledge": result["relevant_knowledge"],
            "ai_analysis": result["analysis"],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"RAG analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")