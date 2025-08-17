"""
WeatherWise Database Models
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

Base = declarative_base()


class CurrentWeather(Base):
    """Current weather observation table."""

    __tablename__ = "current_weather"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Integer, nullable=False)
    wind_speed = Column(Float, nullable=False)
    wind_direction = Column(Integer, nullable=False)
    pressure = Column(Float, nullable=False)
    weather_condition = Column(String(50), nullable=False)
    weather_description = Column(String(255))
    visibility = Column(Float)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_current_weather_location', 'location'),
        Index('idx_current_weather_timestamp', 'timestamp'),
        Index('idx_current_weather_coordinates', 'latitude', 'longitude'),
    )


    def __repr__(self):
        return f"<CurrentWeather(location='{self.location}', temp={self.temperature}°C)>"
    

class WeatherForecast(Base):
    """Weather forecast data table."""

    __tablename__ = "weather_forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    forecast_date = Column(DateTime(timezone=True), nullable=False)
    temperature_min = Column(Float)
    temperature_max = Column(Float)
    temperature = Column(Float)
    humidity = Column(Integer)
    wind_speed = Column(Float)
    wind_direction = Column(Integer)
    pressure = Column(Float)
    weather_condition = Column(String(50))
    weather_description = Column(String(255))
    precipitation_probability = Column(Integer)  # 0-100%
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Indexes
    __table_args__ = (
        Index('idx_weather_forecasts_location', 'location'),
        Index('idx_weather_forecasts_date', 'forecast_date'),
        Index('idx_weather_forecasts_coordinates', 'latitude', 'longitude'),
    )
    
    def __repr__(self):
        return f"<WeatherForecast(location='{self.location}', date={self.forecast_date})>"


class DisasterAlert(Base):
    """Disaster alerts and warnings table."""
    
    __tablename__ = "disaster_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type = Column(String(50), nullable=False)  # TYPHOON, FLOOD, WIND, etc.
    severity_level = Column(String(20), nullable=False)  # LOW, MODERATE, HIGH, CRITICAL
    title = Column(String(255), nullable=False)
    description = Column(Text)
    affected_areas = Column(JSON)  # Store areas as JSON array
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    status = Column(String(20), default='ACTIVE')  # ACTIVE, EXPIRED, CANCELLED
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Indexes
    __table_args__ = (
        Index('idx_disaster_alerts_type', 'alert_type'),
        Index('idx_disaster_alerts_status', 'status'),
        Index('idx_disaster_alerts_severity', 'severity_level'),
        Index('idx_disaster_alerts_start_time', 'start_time'),
    )
    
    def __repr__(self):
        return f"<DisasterAlert(type='{self.alert_type}', severity='{self.severity_level}')>"


class RiskAssessment(Base):
    """AI-generated risk assessments table."""
    
    __tablename__ = "risk_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location = Column(String(255), nullable=False)
    assessment_type = Column(String(50), nullable=False)  # risk_assessment, trend_analysis
    risk_level = Column(String(20), nullable=False)  # LOW, MODERATE, HIGH, CRITICAL
    confidence_score = Column(Float)  # 0.0 to 1.0
    key_risks = Column(JSON)  # Store risks as JSON array
    summary = Column(Text)
    recommendations = Column(JSON)  # Store recommendations as JSON
    weather_data_snapshot = Column(JSON)  # Store related weather data
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Indexes
    __table_args__ = (
        Index('idx_risk_assessments_location', 'location'),
        Index('idx_risk_assessments_risk_level', 'risk_level'),
        Index('idx_risk_assessments_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<RiskAssessment(location='{self.location}', risk='{self.risk_level}')>"


class AnalysisReport(Base):
    """Generated analysis reports table."""
    
    __tablename__ = "analysis_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_type = Column(String(50), nullable=False)  # risk_assessment, action_plan
    location = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    executive_summary = Column(Text)
    content = Column(JSON)  # Store full report content as JSON
    stakeholder_level = Column(String(20))  # executive, lgu, technical
    output_format = Column(String(10))  # pdf, json, html
    status = Column(String(20), default='DRAFT')  # DRAFT, COMPLETED, ARCHIVED
    file_path = Column(String(500))  # Path to generated file
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Indexes
    __table_args__ = (
        Index('idx_analysis_reports_type', 'report_type'),
        Index('idx_analysis_reports_location', 'location'),
        Index('idx_analysis_reports_status', 'status'),
        Index('idx_analysis_reports_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AnalysisReport(type='{self.report_type}', location='{self.location}')>"