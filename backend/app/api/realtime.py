"""
WebSocket API Endpoints for Real-time Events
"""

import json
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

class WeatherUpdateRequest(BaseModel):
    """Request model for weather updates."""
    location: str
    temperature: float
    humidity: int
    wind_speed: float
    pressure: float
    weather_condition: str
    wind_direction: int = 0
    visibility: float = 10.0

class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.event_processor = None
    
    def get_event_processor(self, db: Session):
        """Get or create event processor."""
        if self.event_processor is None:
            from ..services.realtime_events import get_event_processor
            self.event_processor = get_event_processor(db)
        return self.event_processor
    
    async def connect(self, websocket: WebSocket, db: Session):
        """Accept new WebSocket connection."""
        processor = self.get_event_processor(db)
        await processor.add_connection(websocket)
        return processor
    
    def disconnect(self, websocket: WebSocket, db: Session):
        """Remove WebSocket connection."""
        if self.event_processor:
            self.event_processor.remove_connection(websocket)

# Global connection manager
manager = ConnectionManager()

@router.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time weather alerts."""
    
    processor = await manager.connect(websocket, db)
    
    try:
        logger.info("New WebSocket connection established")
        
        # Send welcome message
        welcome_message = {
            "type": "connection_established",
            "message": "Connected to WeatherWise real-time alerts",
            "active_events_count": len(processor.get_active_events())
        }
        await websocket.send_text(json.dumps(welcome_message))
        
        while True:
            # Keep connection alive and handle incoming messages
            try:
                data = await websocket.receive_text()
                
                # Handle client messages (like subscription preferences)
                try:
                    message = json.loads(data)
                    await handle_client_message(websocket, message, processor)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {data}")
                    
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket connection disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket, db)

async def handle_client_message(websocket: WebSocket, message: Dict, processor):
    """Handle messages from WebSocket clients."""
    
    message_type = message.get('type')
    
    if message_type == 'subscribe':
        # Handle subscription to specific locations or alert types
        locations = message.get('locations', [])
        alert_types = message.get('alert_types', [])
        
        response = {
            "type": "subscription_confirmed",
            "data": {
                "locations": locations,
                "alert_types": alert_types,
                "status": "subscribed"
            }
        }
        await websocket.send_text(json.dumps(response))
        
    elif message_type == 'get_active_events':
        # Send current active events
        active_events = processor.get_active_events()
        response = {
            "type": "active_events",
            "events": active_events,
            "count": len(active_events)
        }
        await websocket.send_text(json.dumps(response))
        
    elif message_type == 'ping':
        # Respond to ping with pong
        response = {"type": "pong", "timestamp": message.get('timestamp')}
        await websocket.send_text(json.dumps(response))

@router.post("/realtime/process")
async def process_weather_update(
    weather_data: WeatherUpdateRequest,
    db: Session = Depends(get_db)
):
    """Endpoint to process incoming weather data and generate real-time alerts."""
    
    try:
        processor = manager.get_event_processor(db)
        
        # Convert Pydantic model to dict
        weather_dict = weather_data.dict()
        
        # Process weather data through real-time system
        events = await processor.process_weather_update(weather_dict)
        
        return {
            "status": "success",
            "location": weather_data.location,
            "events_generated": len(events),
            "events": [
                {
                    "id": event.event_id,
                    "type": event.event_type,
                    "severity": event.severity.value,
                    "location": event.location,
                    "conditions": event.data.get("conditions", ""),
                    "recommendations_count": len(event.data.get("recommendations", []))
                } for event in events
            ],
            "active_connections": len(processor.active_connections),
            "processed_at": weather_dict.get("timestamp", "now")
        }
        
    except Exception as e:
        logger.error(f"Failed to process weather update: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.get("/realtime/active-events")
async def get_active_events(db: Session = Depends(get_db)):
    """Get currently active real-time events."""
    
    try:
        processor = manager.get_event_processor(db)
        active_events = processor.get_active_events()
        
        return {
            "status": "success",
            "active_events": active_events,
            "count": len(active_events),
            "active_connections": len(processor.active_connections)
        }
        
    except Exception as e:
        logger.error(f"Failed to get active events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve events: {str(e)}")

@router.get("/realtime/system-status")
async def get_system_status(db: Session = Depends(get_db)):
    """Get real-time system status."""
    
    try:
        processor = manager.get_event_processor(db)
        
        # Get database event counts
        from sqlalchemy import text
        
        total_events = db.execute(text("""
            SELECT COUNT(*) FROM realtime_events
        """)).scalar()
        
        recent_events = db.execute(text("""
            SELECT COUNT(*) FROM realtime_events 
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)).scalar()
        
        active_workflows = db.execute(text("""
            SELECT COUNT(*) FROM agent_workflows 
            WHERE status IN ('pending', 'running')
        """)).scalar()
        
        return {
            "status": "operational",
            "real_time_system": {
                "active_connections": len(processor.active_connections),
                "active_events": len(processor.get_active_events()),
                "event_history_size": len(processor.event_history),
                "alert_thresholds_loaded": len(processor.alert_thresholds)
            },
            "database_stats": {
                "total_events": total_events,
                "events_24h": recent_events,
                "active_workflows": active_workflows
            },
            "system_health": "healthy"
        }
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        return {
            "status": "error",
            "message": str(e),
            "system_health": "degraded"
        }

@router.post("/realtime/simulate-event")
async def simulate_weather_event(
    event_type: str,
    location: str = "Manila,PH",
    severity: str = "warning",
    db: Session = Depends(get_db)
):
    """Simulate a weather event for testing (development only)."""
    
    # Only allow in development
    import os
    if os.getenv('DEBUG', 'False').lower() != 'true':
        raise HTTPException(status_code=403, detail="Simulation only available in debug mode")
    
    try:
        processor = manager.get_event_processor(db)
        
        # Create test weather data based on event type
        if event_type == "typhoon":
            test_data = {
                "location": location,
                "temperature": 28.0,
                "humidity": 85,
                "wind_speed": 95 if severity == "critical" else 65,
                "pressure": 980 if severity == "critical" else 995,
                "weather_condition": "Severe Storm",
                "wind_direction": 180,
                "visibility": 5.0
            }
        elif event_type == "heat":
            test_data = {
                "location": location,
                "temperature": 42.0 if severity == "critical" else 37.0,
                "humidity": 65,
                "wind_speed": 10,
                "pressure": 1010,
                "weather_condition": "Hot",
                "wind_direction": 90,
                "visibility": 8.0
            }
        elif event_type == "flood":
            test_data = {
                "location": location,
                "temperature": 30.0,
                "humidity": 95,
                "wind_speed": 25,
                "pressure": 990,
                "weather_condition": "Heavy Rain",
                "wind_direction": 270,
                "visibility": 3.0
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid event type. Use: typhoon, heat, or flood")
        
        # Process the simulated data
        events = await processor.process_weather_update(test_data)
        
        return {
            "status": "success",
            "message": f"Simulated {event_type} event",
            "test_data": test_data,
            "events_generated": len(events),
            "events": [
                {
                    "id": event.event_id,
                    "type": event.event_type,
                    "severity": event.severity.value,
                    "conditions": event.data.get("conditions", ""),
                    "recommendations": event.data.get("recommendations", [])[:3]  # First 3 recommendations
                } for event in events
            ],
            "broadcasted_to": len(processor.active_connections)
        }
        
    except Exception as e:
        logger.error(f"Failed to simulate event: {e}")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

@router.delete("/realtime/clear-events")
async def clear_all_events(db: Session = Depends(get_db)):
    """Clear all events (development only)."""
    
    # Only allow in development
    import os
    if os.getenv('DEBUG', 'False').lower() != 'true':
        raise HTTPException(status_code=403, detail="Clear events only available in debug mode")
    
    try:
        processor = manager.get_event_processor(db)
        
        # Clear in-memory events
        events_cleared = len(processor.event_history)
        processor.event_history.clear()
        
        # Clear database events (keep for audit, just mark as resolved)
        from sqlalchemy import text
        db.execute(text("""
            UPDATE realtime_events 
            SET auto_resolved = true, resolved_at = NOW() 
            WHERE auto_resolved = false
        """))
        db.commit()
        
        return {
            "status": "success",
            "message": "All events cleared",
            "events_cleared": events_cleared
        }
        
    except Exception as e:
        logger.error(f"Failed to clear events: {e}")
        raise HTTPException(status_code=500, detail=f"Clear failed: {str(e)}")

# Add the database dependency import at the top of the file
def get_db():
    """Database dependency - import from your main app."""
    from ..core.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()