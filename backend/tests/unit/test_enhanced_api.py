import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Set environment variables
os.environ['DATABASE_URL'] = 'postgresql://weatherwise:weatherwise_password@localhost:5432/weatherwise'

from app.core.database import SessionLocal
from app.api.weather import AdvancedAnalysisRequest, comprehensive_weather_analysis
from fastapi import BackgroundTasks

print("✅ Imports successful")

# Test the enhanced analysis
async def test_comprehensive_analysis():
    try:
        db = SessionLocal()
        
        # Create request
        request = AdvancedAnalysisRequest(
            location="Manila,PH",
            analysis_types=["risk_score"],
            time_range="24h"
        )
        
        # Create background tasks (mock)
        background_tasks = BackgroundTasks()
        
        # Call the comprehensive analysis
        result = await comprehensive_weather_analysis(request, background_tasks, db)
        
        print(f"✅ Analysis completed for {result.location}")
        print(f"   Risk level: {result.risk_assessment.get('risk_level', 'N/A')}")
        print(f"   Confidence: {result.confidence_score}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

# Run the async test
import asyncio
asyncio.run(test_comprehensive_analysis())