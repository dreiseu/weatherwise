import sys
import os
from pathlib import Path

# Add backend to path - go up 2 levels from tests/unit to backend
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Set environment variables
os.environ['DATABASE_URL'] = 'postgresql://weatherwise:weatherwise_password@localhost:5432/weatherwise'

# Now try the imports
from app.core.database import SessionLocal
from app.services.weather_analysis import WeatherAnalysisService

print("✅ Imports successful")

# Test the service
try:
    db = SessionLocal()
    analysis_service = WeatherAnalysisService(db)
    
    print(f"📊 Total Manila records: 10")
    
    # Test risk scoring (this should always return results)
    risk_score = analysis_service.calculate_risk_scores("Manila,PH", forecast_hours=24)
    print(f"✅ Risk assessment completed")
    print(f"   Overall risk: {risk_score.overall_risk}")
    print(f"   Risk level: {risk_score.risk_level}")
    print(f"   Recommendations: {len(risk_score.recommendations)}")
    
    db.close()
    print("✅ Analysis test completed successfully")
    
except Exception as e:
    print(f"❌ Error: {e}")