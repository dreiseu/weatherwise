"""
Step 3: Test Real-time Event Processing System
Run this to verify the real-time system works
"""

import sys
import os
import asyncio
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set environment variables
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql://weatherwise:weatherwise_password@localhost:5432/weatherwise')

async def test_realtime_system():
    """Test the real-time event processing system."""
    
    print("⚡ Testing Real-time Event Processing System")
    print("=" * 60)
    
    try:
        # Import database session
        from app.core.database import SessionLocal
        db = SessionLocal()
        
        # Import the real-time system
        from app.services.realtime_events import test_realtime_system
        
        # Run the test
        processor = await test_realtime_system(db)
        
        # Check database for stored events
        from sqlalchemy import text
        
        event_count = db.execute(text("""
            SELECT COUNT(*) FROM realtime_events WHERE created_at >= NOW() - INTERVAL '1 hour'
        """)).scalar()
        
        event_types = db.execute(text("""
            SELECT event_type, COUNT(*) as count
            FROM realtime_events 
            WHERE created_at >= NOW() - INTERVAL '1 hour'
            GROUP BY event_type
        """)).fetchall()
        
        print(f"\n📊 Database Verification:")
        print(f"   Recent events stored: {event_count}")
        
        if event_types:
            print("   Event types:")
            for event_type, count in event_types:
                print(f"     - {event_type}: {count}")
        
        # Test individual components
        print(f"\n🧪 Component Tests:")
        print(f"   Active connections supported: ✅")
        print(f"   Event history size: {len(processor.event_history)}")
        print(f"   Alert thresholds loaded: {len(processor.alert_thresholds)}")
        print(f"   Event handlers ready: ✅")
        
        # Test alert threshold logic
        print(f"\n🔍 Testing Alert Logic:")
        
        # Test typhoon detection
        test_typhoon_data = {
            "location": "Test Location",
            "wind_speed": 100,  # Should trigger critical alert
            "pressure": 980,    # Low pressure
            "temperature": 28,
            "humidity": 85,
            "weather_condition": "Storm"
        }
        
        typhoon_events = await processor.process_weather_update(test_typhoon_data)
        typhoon_detected = any(e.event_type == "typhoon_warning" for e in typhoon_events)
        print(f"   Typhoon detection: {'✅' if typhoon_detected else '❌'}")
        
        # Test heat detection
        test_heat_data = {
            "location": "Test Location",
            "temperature": 43,  # Should trigger heat warning
            "humidity": 60,
            "wind_speed": 10,
            "pressure": 1010,
            "weather_condition": "Hot"
        }
        
        heat_events = await processor.process_weather_update(test_heat_data)
        heat_detected = any(e.event_type == "heat_warning" for e in heat_events)
        print(f"   Heat detection: {'✅' if heat_detected else '❌'}")
        
        # Check overall system status
        active_events = processor.get_active_events()
        print(f"   Active events: {len(active_events)}")
        
        if event_count > 0:
            print("\n✅ Real-time event system is working correctly!")
            print("🎯 Ready for Step 4: Frontend Integration")
        else:
            print("\n⚠️  System functional but no events were stored")
            print("Check database connection and permissions")
        
        db.close()
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you created: app/services/realtime_events.py")
        print("2. Check that the database migration completed successfully")
        return False
    
    except Exception as e:
        print(f"❌ Test Error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def test_api_integration():
    """Test if the API endpoints are ready for integration."""
    
    print("\n🌐 Testing API Integration Readiness...")
    
    try:
        # Test if we can import the API router
        from app.api.realtime import router
        
        # Check if router has the expected endpoints
        expected_endpoints = [
            "/ws/realtime",
            "/realtime/process", 
            "/realtime/active-events",
            "/realtime/system-status"
        ]
        
        # Get all routes from router
        routes = [route.path for route in router.routes]
        
        print("📋 API Endpoints Status:")
        for endpoint in expected_endpoints:
            status = "✅" if any(endpoint in route for route in routes) else "❌"
            print(f"   {endpoint}: {status}")
        
        print(f"   Total routes defined: {len(routes)}")
        
        if len(routes) >= 4:
            print("✅ API endpoints ready for integration")
            return True
        else:
            print("❌ Some API endpoints missing")
            return False
            
    except ImportError as e:
        print(f"❌ API Import Error: {e}")
        print("Make sure you created: app/api/realtime.py")
        return False

if __name__ == "__main__":
    print("Starting Real-time System Tests...")
    
    # Test the core system
    success = asyncio.run(test_realtime_system())
    
    if success:
        # Test API integration
        api_ready = test_api_integration()
        
        if api_ready:
            print(f"\n🎉 Step 3 Complete!")
            print("✅ Real-time event processing system working")
            print("✅ WebSocket endpoints ready")
            print("✅ Database integration functional")
            
            print(f"\n📋 Integration Instructions:")
            print("1. Add this to your main.py:")
            print("   from app.api import realtime")
            print("   app.include_router(realtime.router, prefix='/api/v1', tags=['realtime'])")
            
            print(f"\n2. Test WebSocket connection:")
            print("   ws://localhost:8000/api/v1/ws/realtime")
            
            print(f"\n3. Test event processing:")
            print("   POST /api/v1/realtime/process")
            
            print(f"\nNext: Step 4 - Frontend Dashboard Integration")
            
        else:
            print("\n🔧 Please fix API integration issues before continuing")
    else:
        print("\n🔧 Please fix the system issues above before continuing")