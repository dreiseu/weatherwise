# WeatherWise API Endpoints Specification

## API Design Principles

- **RESTful Design**: Standard HTTP methods and status codes
- **Versioning**: `/api/v1/` prefix for future compatibility
- **Consistent Response Format**: Standardized JSON responses
- **Error Handling**: Comprehensive error codes and messages
- **Rate Limiting**: Configured limits per endpoint type

## Base Configuration
Base URL: http://localhost:8000/api/v1
Content-Type: application/json
Authentication: Bearer JWT (for protected endpoints)

## Weather Data Endpoints

### GET /weather/current
Get current weather conditions for a specific location.

**Parameters:**
```json
{
  "location": "string", // Required: "Manila,PH" or "lat,lon"
  "units": "string"     // Optional: "metric", "imperial" (default: metric)
}

Response:
{
  "status": "success",
  "data": {
    "id": "uuid",
    "location": "Manila, PH",
    "coordinates": {
      "latitude": 14.5995,
      "longitude": 120.9842
    },
    "weather": {
      "temperature": 28.5,
      "humidity": 78,
      "wind_speed": 15.2,
      "wind_direction": 180,
      "pressure": 1013.25,
      "visibility": 10.0,
      "condition": "Partly Cloudy",
      "description": "Partly cloudy with scattered clouds"
    },
    "timestamp": "2025-08-16T12:00:00Z",
    "source": "openweather"
  }
}
```

**GET /weather/forecast**
Get weather forecast for specified location and time range.

```json
{
  "location": "string", // Required
  "days": "integer",    // Optional: 1-5 (default: 3)
  "hours": "integer"    // Optional: 1-48 (hourly forecast)
}

Response:
{
  "status": "success",
  "data": {
    "location": "Manila, PH",
    "forecast_type": "daily",
    "forecasts": [
      {
        "date": "2025-08-17",
        "temperature": {
          "min": 24.0,
          "max": 32.0,
          "morning": 26.0,
          "afternoon": 31.0,
          "evening": 28.0
        },
        "weather": {
          "condition": "Rain",
          "description": "Moderate rain",
          "humidity": 85,
          "wind_speed": 20.0,
          "precipitation_probability": 75
        }
      }
    ]
  }
}
```

**POST /weather/analyze**
Request AI-powered weather analysis and risk assessment.
Request Body:
```json
{
  "location": "Manila, PH",
  "analysis_type": "risk_assessment", // "risk_assessment", "trend_analysis", "comparison"
  "time_range": "24h",                // "24h", "48h", "72h", "7d"
  "include_historical": true,
  "focus_areas": ["flooding", "wind", "storm_surge"]
}
Response:
{
  "status": "success",
  "data": {
    "analysis_id": "uuid",
    "location": "Manila, PH",
    "risk_level": "MODERATE",
    "confidence_score": 0.85,
    "key_risks": [
      {
        "type": "flooding",
        "probability": 0.65,
        "severity": "moderate",
        "timeline": "24-48 hours"
      }
    ],
    "summary": "Moderate risk of urban flooding due to forecasted heavy rainfall...",
    "generated_at": "2025-08-16T12:00:00Z"
  }
}
```

## Alert Management Endpoints

**GET /alerts**
Retrieve active disaster alerts

Parameters:
```json
{
  "status": "string",    // Optional: "active", "expired", "all"
  "type": "string",      // Optional: "typhoon", "flood", "wind"
  "location": "string",  // Optional: filter by location
  "severity": "string"   // Optional: "low", "moderate", "high", "critical"
}
Response:
{
  "status": "success",
  "data": {
    "alerts": [
      {
        "id": "uuid",
        "type": "TYPHOON",
        "severity": "HIGH",
        "title": "Typhoon Warning Signal #3",
        "description": "Typhoon approaching eastern coast with sustained winds of 150 km/h",
        "affected_areas": [
          "Eastern Samar",
          "Northern Leyte",
          "Southern Quezon"
        ],
        "start_time": "2025-08-16T18:00:00Z",
        "estimated_end": "2025-08-18T06:00:00Z",
        "status": "ACTIVE",
        "created_at": "2025-08-16T12:00:00Z",
        "updated_at": "2025-08-16T12:00:00Z"
      }
    ],
    "total_count": 1,
    "active_count": 1
  }
}
```

**POST /alerts**
Create a new disaster alert (Admin only).

Request Body:
```json
{
  "type": "TYPHOON",
  "severity": "HIGH",
  "title": "Typhoon Warning Signal #3",
  "description": "Detailed alert description...",
  "affected_areas": ["Region1", "Region2"],
  "start_time": "2025-08-16T18:00:00Z",
  "estimated_end": "2025-08-18T06:00:00Z"
}
```

**PUT /alerts/{alert_id}**
Update existing alerts status or information

Request Body:
```json
{
  "status": "EXPIRED",
  "description": "Updated description...",
  "estimated_end": "2025-08-17T12:00:00Z"
}
```

## Report Generation Endpoints

**POST /reports/generate**
Generate comprehensive DRRM analysis report.

Request Body:
```json
{
  "location": "Metro Manila",
  "report_type": "risk_assessment", // "risk_assessment", "action_plan", "executive_summary"
  "time_range": "72h",
  "include_sections": [
    "weather_analysis",
    "risk_evaluation", 
    "recommendations",
    "resource_allocation"
  ],
  "output_format": "pdf",           // "pdf", "json", "html"
  "stakeholder_level": "lgu"        // "executive", "lgu", "technical"
}
Response:
{
  "status": "success",
  "data": {
    "report_id": "uuid",
    "status": "generating",          // "generating", "completed", "failed"
    "estimated_completion": "2025-08-16T12:05:00Z",
    "download_url": null             // Available when completed
  }
}
```

**GET /reports/{report_id}**
Retrieve generated report status and content

Response:
```json
{
  "status": "success",
  "data": {
    "report_id": "uuid",
    "status": "completed",
    "generated_at": "2025-08-16T12:04:30Z",
    "location": "Metro Manila",
    "report_type": "risk_assessment",
    "content": {
      "executive_summary": "...",
      "risk_level": "MODERATE",
      "key_findings": ["Finding 1", "Finding 2"],
      "recommendations": [
        {
          "priority": "IMMEDIATE",
          "action": "Deploy emergency teams to flood-prone areas",
          "affected_population": "~50,000 residents",
          "resources_needed": ["rescue boats", "emergency supplies"]
        }
      ]
    },
    "download_url": "/api/v1/reports/uuid/download"
  }
}
```

**GET /reports/{report_id}/download**
Download report file in requested format.

Response: Binary file (PDF/HTML) or JSON data

## AI Analysis Endpoints

**POST /ai/risk-assessment**
Get AI-powered risk assessment for specific location.

Request Body:
```json
{
  "location": "Manila, PH",
  "assessment_type": "comprehensive", // "quick", "comprehensive", "specific"
  "hazard_types": ["typhoon", "flood", "landslide"],
  "time_horizon": "48h"
}
```

**POST /ai/recommendations**
Generate actionable recommendations based on current conditions.

Request Body:
```json
{
  "location": "Manila, PH",
  "current_risk_level": "MODERATE",
  "target_audience": "lgu",         // "lgu", "emergency_services", "public"
  "resource_constraints": {
    "budget": "limited",
    "personnel": "adequate",
    "equipment": "limited"
  }
}
```

**POST /ai/chat**
Interactive chat interface for DRRM questions.

Request Body:
```json
{
  "message": "What should we do if flooding reaches 2 meters in Marikina?",
  "context": {
    "location": "Marikina City",
    "current_conditions": "heavy_rain",
    "user_role": "emergency_coordinator"
  },
  "conversation_id": "uuid" // Optional: for conversation continuity
}
```

## Utility Endpoints

**GET /health**
System health check.

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-16T12:00:00Z",
  "services": {
    "database": "healthy",
    "weather_api": "healthy", 
    "ai_service": "healthy",
    "vector_db": "healthy"
  }
}
```

**GET /status**
Detailed system status and metrics.

Response:
```json
{
  "status": "operational",
  "uptime": "72h 15m",
  "api_calls_today": 1250,
  "rate_limits": {
    "weather_api": "850/1000",
    "ai_service": "45/100"
  },
  "version": "1.0.0"
}
```

## Error Response Format
All endpoints return errors in consistent format:
```json
{
  "status": "error",
  "error": {
    "code": "WEATHER_API_UNAVAILABLE",
    "message": "Weather service temporarily unavailable",
    "details": "OpenWeather API returned 503 status",
    "timestamp": "2025-08-16T12:00:00Z",
    "request_id": "uuid"
  }
}
```

## Rate Limiting
Endpoint Category   Rate Limit      Window
Weather Data        100 requests    1 hour
AI Analysis         20 requests     1 hour
Report Generation   10 requests     1 hour
General API         1000 requests   1 hour

## Authentication
Protected endpoints require JWT token in Authorization header:
Authorization: Bearer <jwt_token>

Admin-only endpoints require additional role validation.