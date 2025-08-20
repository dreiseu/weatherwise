"""
Real-time Event Processing System
Handles streaming weather data and immediate alert generation
"""

import asyncio
import json
import uuid
import logging
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import WebSocket, WebSocketDisconnect
import time

# Configure logging
logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class RealTimeEvent:
    event_id: str
    event_type: str
    location: str
    severity: AlertSeverity
    data: Dict[str, Any]
    timestamp: datetime
    expires_at: Optional[datetime] = None
    triggered_by: Optional[str] = None

class EventProcessor:
    """Processes real-time weather events and triggers alerts."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.active_connections: List[WebSocket] = []
        self.event_handlers: Dict[str, Callable] = {}
        self.alert_thresholds = self._load_alert_thresholds()
        self.event_history: List[RealTimeEvent] = []
    
    def _load_alert_thresholds(self) -> Dict[str, Dict]:
        """Load alert thresholds for different weather parameters."""
        return {
            "typhoon": {
                "wind_speed": {"warning": 60, "critical": 90, "emergency": 120},
                "pressure_drop": {"warning": 10, "critical": 20, "emergency": 30}
            },
            "flooding": {
                "rainfall_rate": {"warning": 20, "critical": 50, "emergency": 100},
                "water_level": {"warning": 1.0, "critical": 2.0, "emergency": 3.0},
                "humidity": {"warning": 85, "critical": 90, "emergency": 95}
            },
            "heat": {
                "temperature": {"warning": 35, "critical": 40, "emergency": 45},
                "heat_index": {"warning": 40, "critical": 52, "emergency": 55}
            }
        }
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register event handler for specific event types."""
        self.event_handlers[event_type] = handler
        logger.info(f"Registered handler for {event_type}")
    
    async def add_connection(self, websocket: WebSocket):
        """Add new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection added. Total: {len(self.active_connections)}")
        
        # Send recent events to new connection
        await self._send_recent_events(websocket)
    
    def remove_connection(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket connection removed. Total: {len(self.active_connections)}")
    
    async def _send_recent_events(self, websocket: WebSocket):
        """Send recent events to newly connected client."""
        recent_events = self.event_history[-5:]  # Last 5 events
        
        for event in recent_events:
            message = {
                "type": "recent_event",
                "event": {
                    "id": event.event_id,
                    "type": event.event_type,
                    "location": event.location,
                    "severity": event.severity.value,
                    "data": event.data,
                    "timestamp": event.timestamp.isoformat()
                }
            }
            
            try:
                await websocket.send_text(json.dumps(message))
            except:
                break
    
    async def process_weather_update(self, weather_data: Dict[str, Any]) -> List[RealTimeEvent]:
        """Process incoming weather data and generate alerts if needed."""
        
        events = []
        location = weather_data.get('location', 'Unknown')
        
        logger.info(f"Processing weather update for {location}")
        
        # Check for typhoon conditions
        typhoon_event = self._check_typhoon_conditions(weather_data, location)
        if typhoon_event:
            events.append(typhoon_event)
        
        # Check for heat conditions
        heat_event = self._check_heat_conditions(weather_data, location)
        if heat_event:
            events.append(heat_event)
        
        # Check for flooding potential
        flood_event = self._check_flood_conditions(weather_data, location)
        if flood_event:
            events.append(flood_event)
        
        # Process and broadcast events
        for event in events:
            await self.broadcast_event(event)
            await self.trigger_automated_response(event)
        
        logger.info(f"Generated {len(events)} events for {location}")
        return events
    
    def _check_typhoon_conditions(self, data: Dict, location: str) -> Optional[RealTimeEvent]:
        """Check for typhoon warning conditions."""
        wind_speed = data.get('wind_speed', 0)
        pressure = data.get('pressure', 1013)
        
        # Get baseline pressure (simplified - in production use historical averages)
        baseline_pressure = 1013.25
        pressure_drop = baseline_pressure - pressure
        
        thresholds = self.alert_thresholds['typhoon']
        
        # Determine severity
        severity = None
        conditions = []
        
        if wind_speed >= thresholds['wind_speed']['emergency']:
            severity = AlertSeverity.EMERGENCY
            conditions.append(f"Extreme winds: {wind_speed} km/h")
        elif wind_speed >= thresholds['wind_speed']['critical']:
            severity = AlertSeverity.CRITICAL
            conditions.append(f"Very strong winds: {wind_speed} km/h")
        elif wind_speed >= thresholds['wind_speed']['warning']:
            severity = AlertSeverity.WARNING
            conditions.append(f"Strong winds: {wind_speed} km/h")
        
        if pressure_drop >= thresholds['pressure_drop']['emergency']:
            if not severity or severity.value == 'warning':
                severity = AlertSeverity.EMERGENCY
            conditions.append(f"Extreme pressure drop: {pressure_drop:.1f} hPa")
        elif pressure_drop >= thresholds['pressure_drop']['critical']:
            if not severity or severity.value == 'warning':
                severity = AlertSeverity.CRITICAL
            conditions.append(f"Significant pressure drop: {pressure_drop:.1f} hPa")
        elif pressure_drop >= thresholds['pressure_drop']['warning']:
            if not severity:
                severity = AlertSeverity.WARNING
            conditions.append(f"Pressure drop detected: {pressure_drop:.1f} hPa")
        
        if severity and conditions:
            return RealTimeEvent(
                event_id=str(uuid.uuid4()),
                event_type="typhoon_warning",
                location=location,
                severity=severity,
                data={
                    "wind_speed": wind_speed,
                    "pressure": pressure,
                    "pressure_drop": pressure_drop,
                    "conditions": "; ".join(conditions),
                    "recommendations": self._get_typhoon_recommendations(severity),
                    "pagasa_signal": self._estimate_pagasa_signal(wind_speed)
                },
                timestamp=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=6),
                triggered_by="WeatherMonitor"
            )
        
        return None
    
    def _check_heat_conditions(self, data: Dict, location: str) -> Optional[RealTimeEvent]:
        """Check for dangerous heat conditions."""
        temperature = data.get('temperature', 25)
        humidity = data.get('humidity', 50)
        
        # Calculate heat index
        heat_index = self._calculate_heat_index(temperature, humidity)
        
        thresholds = self.alert_thresholds['heat']
        severity = None
        
        if heat_index >= thresholds['heat_index']['emergency']:
            severity = AlertSeverity.EMERGENCY
        elif heat_index >= thresholds['heat_index']['critical']:
            severity = AlertSeverity.CRITICAL
        elif heat_index >= thresholds['heat_index']['warning']:
            severity = AlertSeverity.WARNING
        elif temperature >= thresholds['temperature']['warning']:
            severity = AlertSeverity.WARNING
        
        if severity:
            return RealTimeEvent(
                event_id=str(uuid.uuid4()),
                event_type="heat_warning",
                location=location,
                severity=severity,
                data={
                    "temperature": temperature,
                    "humidity": humidity,
                    "heat_index": heat_index,
                    "conditions": f"Dangerous heat conditions - Heat Index: {heat_index:.1f}°C",
                    "recommendations": self._get_heat_recommendations(severity),
                    "health_risk": self._get_health_risk_level(heat_index)
                },
                timestamp=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
                triggered_by="HeatMonitor"
            )
        
        return None
    
    def _check_flood_conditions(self, data: Dict, location: str) -> Optional[RealTimeEvent]:
        """Check for flooding potential."""
        humidity = data.get('humidity', 50)
        pressure = data.get('pressure', 1013)
        temperature = data.get('temperature', 25)
        
        # Simple flood risk calculation (in production, use more sophisticated models)
        flood_risk_score = 0
        risk_factors = []
        
        if humidity > 90:
            flood_risk_score += 0.4
            risk_factors.append(f"Very high humidity: {humidity}%")
        elif humidity > 85:
            flood_risk_score += 0.2
            risk_factors.append(f"High humidity: {humidity}%")
        
        if pressure < 995:
            flood_risk_score += 0.3
            risk_factors.append(f"Low pressure: {pressure} hPa")
        elif pressure < 1005:
            flood_risk_score += 0.1
            risk_factors.append(f"Below normal pressure: {pressure} hPa")
        
        # Add temperature factor (warm, humid air holds more moisture)
        if temperature > 30 and humidity > 80:
            flood_risk_score += 0.2
            risk_factors.append("Warm, humid conditions")
        
        # Get recent rainfall data (placeholder - in production, integrate with rainfall sensors)
        recent_rainfall = self._get_recent_rainfall(location)
        if recent_rainfall > 50:  # mm in last 24 hours
            flood_risk_score += 0.4
            risk_factors.append(f"Recent heavy rainfall: {recent_rainfall}mm")
        
        if flood_risk_score >= 0.7:
            severity = AlertSeverity.CRITICAL
        elif flood_risk_score >= 0.5:
            severity = AlertSeverity.WARNING
        else:
            severity = None
        
        if severity and risk_factors:
            return RealTimeEvent(
                event_id=str(uuid.uuid4()),
                event_type="flood_warning",
                location=location,
                severity=severity,
                data={
                    "flood_risk_score": round(flood_risk_score, 2),
                    "risk_factors": risk_factors,
                    "recent_rainfall": recent_rainfall,
                    "conditions": f"Flood risk detected - Score: {flood_risk_score:.1f}",
                    "recommendations": self._get_flood_recommendations(severity),
                    "affected_areas": self._get_flood_prone_areas(location)
                },
                timestamp=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
                triggered_by="FloodMonitor"
            )
        
        return None
    
    def _calculate_heat_index(self, temp_c: float, humidity: float) -> float:
        """Calculate heat index in Celsius."""
        # Convert to Fahrenheit for calculation
        temp_f = (temp_c * 9/5) + 32
        
        # Heat index formula (simplified)
        if temp_f < 80:
            return temp_c
        
        hi = (
            -42.379 + 2.04901523 * temp_f + 10.14333127 * humidity
            - 0.22475541 * temp_f * humidity - 6.83783e-3 * temp_f**2
            - 5.481717e-2 * humidity**2 + 1.22874e-3 * temp_f**2 * humidity
            + 8.5282e-4 * temp_f * humidity**2 - 1.99e-6 * temp_f**2 * humidity**2
        )
        
        # Convert back to Celsius
        return (hi - 32) * 5/9
    
    def _get_recent_rainfall(self, location: str) -> float:
        """Get recent rainfall data for location (placeholder)."""
        # In production, this would query rainfall sensors or weather stations
        # For now, return simulated data based on humidity
        return 0.0
    
    def _estimate_pagasa_signal(self, wind_speed: float) -> str:
        """Estimate PAGASA typhoon signal based on wind speed."""
        if wind_speed >= 185:
            return "Signal #5"
        elif wind_speed >= 118:
            return "Signal #4"
        elif wind_speed >= 89:
            return "Signal #3"
        elif wind_speed >= 62:
            return "Signal #2"
        elif wind_speed >= 39:
            return "Signal #1"
        else:
            return "No Signal"
    
    def _get_health_risk_level(self, heat_index: float) -> str:
        """Get health risk level based on heat index."""
        if heat_index >= 54:
            return "Extreme Danger"
        elif heat_index >= 52:
            return "Danger"
        elif heat_index >= 40:
            return "Extreme Caution"
        elif heat_index >= 32:
            return "Caution"
        else:
            return "Normal"
    
    def _get_flood_prone_areas(self, location: str) -> List[str]:
        """Get flood-prone areas for a location."""
        flood_areas = {
            "Manila,PH": ["Tondo", "Malate", "Ermita", "Quiapo"],
            "Marikina,PH": ["Riverbanks", "Tumana", "Nangka"],
            "Quezon City,PH": ["Commonwealth", "Fairview", "Novaliches"]
        }
        return flood_areas.get(location, ["Low-lying areas", "River basins"])
    
    def _get_typhoon_recommendations(self, severity: AlertSeverity) -> List[str]:
        """Get typhoon-specific recommendations."""
        base_recommendations = [
            "Monitor PAGASA updates continuously",
            "Secure loose objects outdoors",
            "Check emergency supplies (food, water, flashlight)"
        ]
        
        if severity == AlertSeverity.CRITICAL:
            base_recommendations.extend([
                "Evacuate coastal and low-lying areas",
                "Activate emergency response teams",
                "Prepare for extended power outages",
                "Cancel outdoor activities and classes"
            ])
        elif severity == AlertSeverity.EMERGENCY:
            base_recommendations.extend([
                "IMMEDIATE EVACUATION REQUIRED for danger zones",
                "Activate all emergency protocols",
                "Deploy rescue teams to standby positions",
                "Suspend all transportation services"
            ])
        elif severity == AlertSeverity.WARNING:
            base_recommendations.extend([
                "Prepare evacuation plans",
                "Monitor local government announcements",
                "Avoid unnecessary travel"
            ])
        
        return base_recommendations
    
    def _get_heat_recommendations(self, severity: AlertSeverity) -> List[str]:
        """Get heat-specific recommendations."""
        recommendations = [
            "Stay hydrated with plenty of water",
            "Avoid outdoor activities during peak hours (10 AM - 4 PM)",
            "Wear light-colored, loose-fitting clothing"
        ]
        
        if severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
            recommendations.extend([
                "Open emergency cooling centers",
                "Check on elderly and vulnerable populations",
                "Activate heat emergency protocols",
                "Seek immediate medical attention for heat exhaustion"
            ])
        elif severity == AlertSeverity.WARNING:
            recommendations.extend([
                "Use cooling centers if available",
                "Take frequent breaks in shade/AC",
                "Monitor for signs of heat exhaustion"
            ])
        
        return recommendations
    
    def _get_flood_recommendations(self, severity: AlertSeverity) -> List[str]:
        """Get flood-specific recommendations."""
        base_recommendations = [
            "Avoid low-lying and flood-prone areas",
            "Do not drive through flooded roads",
            "Monitor water levels closely"
        ]
        
        if severity == AlertSeverity.CRITICAL:
            base_recommendations.extend([
                "Evacuate flood-prone areas immediately",
                "Move to higher ground",
                "Prepare emergency supplies",
                "Contact local emergency services if stranded"
            ])
        else:
            base_recommendations.extend([
                "Prepare evacuation routes",
                "Check drainage systems",
                "Monitor rainfall updates"
            ])
        
        return base_recommendations
    
    async def broadcast_event(self, event: RealTimeEvent):
        """Broadcast event to all connected WebSocket clients."""
        if not self.active_connections:
            logger.info("No active connections to broadcast to")
            return
        
        # Store event in history
        self.event_history.append(event)
        if len(self.event_history) > 50:  # Keep last 50 events
            self.event_history = self.event_history[-50:]
        
        message = {
            "type": "real_time_alert",
            "event": {
                "id": event.event_id,
                "type": event.event_type,
                "location": event.location,
                "severity": event.severity.value,
                "data": event.data,
                "timestamp": event.timestamp.isoformat(),
                "expires_at": event.expires_at.isoformat() if event.expires_at else None
            }
        }
        
        # Store in database
        await self._store_event_in_database(event)
        
        # Broadcast to all connections
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
                logger.debug(f"Sent event {event.event_id} to WebSocket client")
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.remove_connection(connection)
        
        logger.info(f"Broadcasted {event.event_type} event to {len(self.active_connections)} clients")
    
    async def _store_event_in_database(self, event: RealTimeEvent):
        """Store event in database for historical tracking."""
        try:
            insert_sql = text("""
                INSERT INTO realtime_events (
                    id, event_type, location, severity, event_data,
                    triggered_by, expires_at
                ) VALUES (
                    :event_id, :event_type, :location, :severity, :event_data,
                    :triggered_by, :expires_at
                )
            """)
            
            self.db.execute(insert_sql, {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "location": event.location,
                "severity": event.severity.value,
                "event_data": json.dumps(event.data),
                "triggered_by": event.triggered_by,
                "expires_at": event.expires_at
            })
            self.db.commit()
            
            logger.debug(f"Stored event {event.event_id} in database")
            
        except Exception as e:
            logger.error(f"Failed to store event in database: {e}")
            self.db.rollback()
    
    async def trigger_automated_response(self, event: RealTimeEvent):
        """Trigger automated responses based on event type and severity."""
        
        # Trigger specific handler if registered
        if event.event_type in self.event_handlers:
            try:
                await self.event_handlers[event.event_type](event)
            except Exception as e:
                logger.error(f"Error in event handler for {event.event_type}: {e}")
        
        # For critical/emergency events, trigger immediate agent analysis
        if event.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
            await self._trigger_emergency_analysis(event)
    
    async def _trigger_emergency_analysis(self, event: RealTimeEvent):
        """Trigger emergency analysis workflow."""
        try:
            # Import here to avoid circular imports
            from ..agents.enhanced_communication import WorkflowOrchestrator
            
            orchestrator = WorkflowOrchestrator(self.db)
            
            # Trigger emergency workflow
            result = await orchestrator.execute_emergency_workflow(
                location=event.location,
                trigger_event=f"{event.event_type}_{event.severity.value}"
            )
            
            logger.info(f"Emergency workflow triggered for {event.location}: {result.get('status')}")
            
        except Exception as e:
            logger.error(f"Failed to trigger emergency analysis: {e}")
    
    def get_active_events(self) -> List[Dict]:
        """Get currently active events."""
        now = datetime.now(timezone.utc)
        active_events = []
        
        for event in self.event_history:
            if not event.expires_at or event.expires_at > now:
                active_events.append({
                    "id": event.event_id,
                    "type": event.event_type,
                    "location": event.location,
                    "severity": event.severity.value,
                    "data": event.data,
                    "timestamp": event.timestamp.isoformat(),
                    "expires_at": event.expires_at.isoformat() if event.expires_at else None
                })
        
        return active_events

# Global instance
_event_processor = None

def get_event_processor(db_session: Session) -> EventProcessor:
    """Get the global event processor instance."""
    global _event_processor
    if _event_processor is None:
        _event_processor = EventProcessor(db_session)
    return _event_processor

async def test_realtime_system(db_session: Session):
    """Test the real-time event system."""
    
    print("🧪 Testing Real-time Event Processing System...")
    
    processor = get_event_processor(db_session)
    
    # Test typhoon conditions
    print("\n1. Testing Typhoon Detection...")
    typhoon_data = {
        "location": "Manila,PH",
        "temperature": 28.0,
        "humidity": 85,
        "wind_speed": 95,  # Strong typhoon winds
        "pressure": 985,   # Low pressure
        "weather_condition": "Severe Storm"
    }
    
    events = await processor.process_weather_update(typhoon_data)
    print(f"   Generated {len(events)} typhoon events")
    
    # Test heat conditions
    print("\n2. Testing Heat Detection...")
    heat_data = {
        "location": "Cebu,PH",
        "temperature": 42.0,  # Extreme heat
        "humidity": 65,
        "wind_speed": 15,
        "pressure": 1010,
        "weather_condition": "Hot"
    }
    
    events = await processor.process_weather_update(heat_data)
    print(f"   Generated {len(events)} heat events")
    
    # Test flood conditions
    print("\n3. Testing Flood Detection...")
    flood_data = {
        "location": "Davao,PH",
        "temperature": 30.0,
        "humidity": 95,    # Very high humidity
        "wind_speed": 20,
        "pressure": 990,   # Low pressure
        "weather_condition": "Heavy Rain"
    }
    
    events = await processor.process_weather_update(flood_data)
    print(f"   Generated {len(events)} flood events")
    
    # Check active events
    active_events = processor.get_active_events()
    print(f"\n📊 Total active events: {len(active_events)}")
    
    for event in active_events:
        print(f"   - {event['type']} ({event['severity']}) in {event['location']}")
    
    print("\n✅ Real-time system test completed!")
    return processor

if __name__ == "__main__":
    print("Real-time Event Processing System loaded successfully!")
    print("Import this module to use the real-time event processing.")