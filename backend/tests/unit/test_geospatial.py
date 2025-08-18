import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.services.geospatial_service import GeospatialService

print("✅ Imports successful")

# Test the service
try:
    db = SessionLocal()
    geo_service = GeospatialService(db)
    
    # Test distance calculation
    manila_coords = (14.5995, 120.9842)
    cebu_coords = (10.3157, 123.8854)
    distance = geo_service.calculate_distance(manila_coords, cebu_coords)
    print(f"✅ Distance Manila-Cebu: {distance:.1f} km")
    
    db.close()
    print("✅ Geospatial test completed successfully")
    
except Exception as e:
    print(f"❌ Error: {e}")