"""
WeatherWise FastAPI Application
Main entry point for the API server
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import uvicorn
import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.api import weather, alerts, agents, realtime
from app.core.database import get_db, create_tables

app = FastAPI(
    title="WeatherWise API",
    description="DRRM Weather Analytics Platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include API routes
app.include_router(weather.router, prefix="/api/v1/weather", tags=["weather"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(realtime.router, prefix="/api/v1", tags=["realtime"])

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    create_tables()
    print("WeatherWise API with Real-time Processing started!")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "WeatherWise DRRM Analytics API",
        "version": "1.0.0",
        "features": [
            "Weather data analysis",
            "AI agent system", 
            "Real-time event processing",
            "WebSocket connections",
            "DRRM protocols"
        ],
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/api/v1/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Test database connection
        result = db.execute(text("SELECT 1 as test"))

        # Check agent system tables
        agent_tables = db.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name LIKE '%agent%'
        """)).scalar()
        
        # Check recent activity
        recent_events = db.execute(text("""
            SELECT COUNT(*) FROM realtime_events 
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)).scalar()

        return {
            "status": "healthy",
            "database": "connected",
            "api": "operational",
            "agent_system": f"{agent_tables} tables ready",
            "realtime_events_24h": recent_events,
            "features": {
                "weather_analysis": "enabled",
                "agent_system": "enabled", 
                "realtime_processing": "enabled",
                "websocket": "enabled"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


if __name__ == "__main__":
    # Run the development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )