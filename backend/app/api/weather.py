"""
Weather API Endpoints
Handles weather data retrieval and analysis
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from uuid import UUID

from ..core.database import get_db
from ..models.weather import CurrentWeather, WeatherForecast
from ..services.weather_service import OpenWeatherService
from ..services.data_validator import WeatherDataValidator

# Create router
router = APIRouter()

# Initialize services
weather_service = OpenWeatherService()
validator = WeatherDataValidator()


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


class WeatherAnalysisResponse(BaseModel):
    """Weather analysis response model."""
    analysis_id: str
    location: str
    risk_level: str
    confidence_score: float
    summary: str
    recommendations: List[str]
    generated_at: datetime


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