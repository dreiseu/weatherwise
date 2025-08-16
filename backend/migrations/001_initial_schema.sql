-- WeatherWise Initial Database Schema Migration
-- Migration: 001_initial_schema.sql

-- Create current_weather table
CREATE TABLE current_weather (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    temperature DECIMAL(5, 2) NOT NULL,
    humidity INTEGER CHECK (humidity >= 0 AND humidity <= 100),
    wind_speed DECIMAL(5, 2) NOT NULL,
    wind_direction INTEGER CHECK (wind_direction >= 0 AND wind_direction <= 360),
    pressure DECIMAL(7, 2) NOT NULL,
    weather_condition VARCHAR(50) NOT NULL,
    weather_description VARCHAR(255),
    visibility DECIMAL(5, 2),
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create weather_forecasts table
CREATE TABLE weather_forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    forecast_date TIMESTAMPTZ NOT NULL,
    temperature_min DECIMAL(5, 2),
    temperature_max DECIMAL(5, 2),
    humidity INTEGER CHECK (humidity >= 0 AND humidity <= 100),
    wind_speed DECIMAL(5, 2),
    pressure DECIMAL(7, 2),
    weather_condition VARCHAR(50),
    precipitation_probability INTEGER CHECK (precipitation_probability >= 0 AND precipitation_probability <= 100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create disaster_alerts table  
CREATE TABLE disaster_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type VARCHAR(50) NOT NULL,
    severity_level VARCHAR(20) CHECK (severity_level IN ('LOW', 'MODERATE', 'HIGH', 'CRITICAL')),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    affected_areas JSONB,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    status VARCHAR(20) CHECK (status IN ('ACTIVE', 'EXPIRED', 'CANCELLED')) DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_current_weather_location ON current_weather(location);
CREATE INDEX idx_current_weather_timestamp ON current_weather(timestamp);
CREATE INDEX idx_weather_forecasts_location ON weather_forecasts(location);
CREATE INDEX idx_weather_forecasts_date ON weather_forecasts(forecast_date);
CREATE INDEX idx_disaster_alerts_type ON disaster_alerts(alert_type);
CREATE INDEX idx_disaster_alerts_status ON disaster_alerts(status);