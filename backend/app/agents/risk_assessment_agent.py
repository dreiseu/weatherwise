"""
Risk Assessment Agent
Evaluates disaster risks based on weather analysis and generates risk scores
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

class RiskAssessmentAgent(BaseAgent):
    """Agent specialized in disaster risk assessment."""
    
    def __init__(self):
        """Initialize risk assessment agent."""
        super().__init__("RiskAssessmentAgent")
        self.db = SessionLocal()
        self.analysis_service = WeatherAnalysisService(self.db)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process weather data and assess disaster risks."""
        
        location = input_data.get("location")
        forecast_hours = input_data.get("forecast_hours", 24)
        
        if not location:
            raise ValueError("Location is required for risk assessment")
        
        # Get comprehensive risk assessment
        risk_score = self.analysis_service.calculate_risk_scores(location, forecast_hours)
        
        # Determine priority level
        priority = self._determine_priority(risk_score.overall_risk)
        
        # Generate action items based on risk level
        action_items = self._generate_action_items(risk_score)
        
        return {
            "location": location,
            "overall_risk": risk_score.overall_risk,
            "risk_level": risk_score.risk_level,
            "confidence": risk_score.confidence,
            "category_risks": risk_score.category_risks,
            "contributing_factors": risk_score.contributing_factors,
            "recommendations": risk_score.recommendations,
            "priority": priority,
            "action_items": action_items,
            "forecast_hours": forecast_hours
        }
    
    def _determine_priority(self, risk_score: float) -> str:
        """Determine response priority based on risk score."""
        if risk_score >= 0.8:
            return "IMMEDIATE"
        elif risk_score >= 0.6:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_action_items(self, risk_score) -> list:
        """Generate specific action items based on risk assessment."""
        action_items = []
        
        # High typhoon risk actions
        if risk_score.category_risks.get('typhoon', 0) > 0.6:
            action_items.extend([
                "Activate emergency operations center",
                "Issue typhoon warning to communities",
                "Prepare evacuation centers"
            ])
        
        # High flood risk actions
        if risk_score.category_risks.get('flooding', 0) > 0.6:
            action_items.extend([
                "Deploy flood monitoring teams",
                "Check drainage systems",
                "Alert flood-prone communities"
            ])
        
        # Heat stress actions
        if risk_score.category_risks.get('heat_stress', 0) > 0.6:
            action_items.extend([
                "Issue heat advisory warnings",
                "Open cooling centers",
                "Monitor vulnerable populations"
            ])
        
        # Default monitoring actions
        if not action_items:
            action_items.append("Continue routine weather monitoring")
        
        return action_items
    
    def __del__(self):
        """Cleanup database connection."""
        if hasattr(self, 'db'):
            self.db.close()

if __name__ == "__main__":
    # Test the risk assessment agent
    agent = RiskAssessmentAgent()
    
    test_input = {
        "location": "Manila,PH",
        "forecast_hours": 24
    }
    
    result = agent.execute(test_input)
    print(f"Agent: {result['agent_name']}")
    print(f"Status: {result['status']}")
    print(f"Risk Level: {result.get('risk_level', 'N/A')}")
    print(f"Priority: {result.get('priority', 'N/A')}")
    print(f"Action Items: {len(result.get('action_items', []))}")