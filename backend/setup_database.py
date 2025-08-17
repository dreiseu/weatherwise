"""
Standalone database setup script
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set environment variables for database connection
os.environ['DATABASE_URL'] = 'postgresql://weatherwise:weatherwise_password@localhost:5432/weatherwise'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

# Create Base
Base = declarative_base()

# Database models (copied directly to avoid import issues)
class CurrentWeather(Base):
    """Current weather observations table."""
    
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
    
    __table_args__ = (
        Index('idx_current_weather_location', 'location'),
        Index('idx_current_weather_timestamp', 'timestamp'),
        Index('idx_current_weather_coordinates', 'latitude', 'longitude'),
    )


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
    precipitation_probability = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('idx_weather_forecasts_location', 'location'),
        Index('idx_weather_forecasts_date', 'forecast_date'),
        Index('idx_weather_forecasts_coordinates', 'latitude', 'longitude'),
    )


class DisasterAlert(Base):
    """Disaster alerts and warnings table."""
    
    __tablename__ = "disaster_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type = Column(String(50), nullable=False)
    severity_level = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    affected_areas = Column(JSON)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    status = Column(String(20), default='ACTIVE')
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('idx_disaster_alerts_type', 'alert_type'),
        Index('idx_disaster_alerts_status', 'status'),
        Index('idx_disaster_alerts_severity', 'severity_level'),
        Index('idx_disaster_alerts_start_time', 'start_time'),
    )


class RiskAssessment(Base):
    """AI-generated risk assessments table."""
    
    __tablename__ = "risk_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location = Column(String(255), nullable=False)
    assessment_type = Column(String(50), nullable=False)
    risk_level = Column(String(20), nullable=False)
    confidence_score = Column(Float)
    key_risks = Column(JSON)
    summary = Column(Text)
    recommendations = Column(JSON)
    weather_data_snapshot = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('idx_risk_assessments_location', 'location'),
        Index('idx_risk_assessments_risk_level', 'risk_level'),
        Index('idx_risk_assessments_created_at', 'created_at'),
    )


class AnalysisReport(Base):
    """Generated analysis reports table."""
    
    __tablename__ = "analysis_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_type = Column(String(50), nullable=False)
    location = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    executive_summary = Column(Text)
    content = Column(JSON)
    stakeholder_level = Column(String(20))
    output_format = Column(String(10))
    status = Column(String(20), default='DRAFT')
    file_path = Column(String(500))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('idx_analysis_reports_type', 'report_type'),
        Index('idx_analysis_reports_location', 'location'),
        Index('idx_analysis_reports_status', 'status'),
        Index('idx_analysis_reports_created_at', 'created_at'),
    )


def create_database_tables():
    """Create all database tables."""
    
    # Database connection
    DATABASE_URL = "postgresql://weatherwise:weatherwise_password@localhost:5432/weatherwise"
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL, echo=True)
        
        # Create all tables
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database tables created successfully!")
        print("\nCreated tables:")
        print("- current_weather")
        print("- weather_forecasts") 
        print("- disaster_alerts")
        print("- risk_assessments")
        print("- analysis_reports")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False


if __name__ == "__main__":
    create_database_tables()