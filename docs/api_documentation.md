# WeatherWise API Documentation

## Base URL
Development: http://localhost:8000
Production: TBD

## Authentication
- API Key required for external weather data
- JWT tokens for user authentication (future feature)

## Weather Endpoints

### GET /api/weather/current
Get current weather for a location

**Parameters:**
- `location` (string): City name or coordinates
- `lat` (float): Latitude (optional)
- `lon` (float): Longitude (optional)

**Response:**
```json
{
  "id": "uuid",
  "location": "Manila, PH",
  "latitude": 14.5995,
  "longitude": 120.9842,
  "temperature": 28.5,
  "humidity": 78,
  "wind_speed": 15.2,
  "pressure": 1013.25,
  "weather_condition": "Partly Cloudy",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### GET /api/weather/forecast
Get weather forecast for a location

**Parameters:**
- `location` (string): City name
- `days` (int): Number of forecast days (1-5)

### POST /api/weather/analyze
Analyze weather data with AI

**Request Body:**
```json
{
  "location": "Manila, PH",
  "analysis_type": "risk_assessment",
  "time_range": "24h"
}
```

## Alert Endpoints

### GET /api/alerts
Get active disaster alerts

### POST /api/alerts
Create new disaster alert (admin only)

### PUT /api/alerts/{id}
Update alert status

## Report Endpoints

### POST /api/reports/generate
Generate DRRM analysis report

**Request Body:**
```json
{
  "location": "Metro Manila",
  "report_type": "risk_assessment",
  "time_range": "72h",
  "include_recommendations": true
}
```

# Error Codes
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

# Rate Limits
- Weather API: 1000 calls/day (OpenWeather free tier)
- Analysis API: 100 calls/hour per user