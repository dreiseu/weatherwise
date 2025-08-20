"""
Weather Analysis Agent
Specialized agent for processing weather data and generating analysis
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.agents.base_agent import BaseAgent
from app.services.weather_analysis import WeatherAnalysisService
from app.core.database import SessionLocal

class WeatherAnalysisAgent(BaseAgent):
    """Agent specialized in weather data analysis."""
    
    def __init__(self):
        """Initialize weather analysis agent."""
        super().__init__("WeatherAnalysisAgent")
        self.db = SessionLocal()
        self.analysis_service = WeatherAnalysisService(self.db)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process weather data and generate analysis."""
        
        location = input_data.get("location")
        analysis_type = input_data.get("analysis_type", "comprehensive")
        
        if not location:
            raise ValueError("Location is required for weather analysis")
        
        results = {}
        
        if analysis_type in ["comprehensive", "patterns"]:
            patterns = self.analysis_service.analyze_weather_patterns(location, days=3)
            results["weather_patterns"] = [
                {
                    "type": p.pattern_type,
                    "confidence": p.confidence,
                    "risk_level": p.risk_level,
                    "description": p.description
                } for p in patterns
            ]
        
        if analysis_type in ["comprehensive", "anomalies"]:
            anomalies = self.analysis_service.detect_anomalies(location, days=2)
            results["anomalies"] = [
                {
                    "type": a.anomaly_type,
                    "severity": a.severity,
                    "value": a.value,
                    "confidence": a.confidence
                } for a in anomalies
            ]
        
        if analysis_type in ["comprehensive", "trends"]:
            trends = self.analysis_service.analyze_trends(location, days=7)
            results["trends"] = trends
        
        return {
            "location": location,
            "analysis_results": results,
            "patterns_count": len(results.get("weather_patterns", [])),
            "anomalies_count": len(results.get("anomalies", [])),
            "analysis_type": analysis_type
        }
    
    def __del__(self):
        """Cleanup database connection."""
        if hasattr(self, 'db'):
            self.db.close()

if __name__ == "__main__":
    # Test the weather analysis agent
    agent = WeatherAnalysisAgent()
    
    test_input = {
        "location": "Manila,PH",
        "analysis_type": "comprehensive"
    }
    
    result = agent.execute(test_input)
    print(f"Agent: {result['agent_name']}")
    print(f"Status: {result['status']}")
    print(f"Patterns found: {result.get('patterns_count', 0)}")
    print(f"Anomalies found: {result.get('anomalies_count', 0)}")