"""
Agent Coordinator
Orchestrates multiple agents and manages their interactions
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.agents.weather_analysis_agent import WeatherAnalysisAgent
from app.agents.risk_assessment_agent import RiskAssessmentAgent
from app.agents.action_planning_agent import ActionPlanningAgent

class AgentCoordinator:
    """Coordinates multiple agents for comprehensive analysis."""
    
    def __init__(self):
        """Initialize agent coordinator."""
        self.weather_agent = WeatherAnalysisAgent()
        self.risk_agent = RiskAssessmentAgent()
        self.action_agent = ActionPlanningAgent()
    
    def run_full_analysis(self, location: str) -> Dict[str, Any]:
        """Run complete analysis using all agents."""
        
        # Step 1: Weather Analysis
        weather_input = {
            "location": location,
            "analysis_type": "comprehensive"
        }
        weather_result = self.weather_agent.execute(weather_input)
        
        # Step 2: Risk Assessment
        risk_input = {
            "location": location,
            "forecast_hours": 24
        }
        risk_result = self.risk_agent.execute(risk_input)
        
        # Step 3: Action Planning
        action_input = {
            "location": location,
            "risk_level": risk_result.get("risk_level", "UNKNOWN"),
            "category_risks": risk_result.get("category_risks", {})
        }
        action_result = self.action_agent.execute(action_input)
        
        # Combine results
        return {
            "location": location,
            "analysis_summary": {
                "weather_patterns": weather_result.get("patterns_count", 0),
                "anomalies_detected": weather_result.get("anomalies_count", 0),
                "overall_risk": risk_result.get("overall_risk", 0),
                "risk_level": risk_result.get("risk_level", "UNKNOWN"),
                "plan_priority": action_result.get("plan_priority", 5)
            },
            "detailed_results": {
                "weather_analysis": weather_result,
                "risk_assessment": risk_result,
                "action_plan": action_result
            },
            "execution_summary": {
                "agents_executed": 3,
                "all_successful": all(
                    result.get("status") == "success" 
                    for result in [weather_result, risk_result, action_result]
                )
            }
        }

if __name__ == "__main__":
    # Test the agent coordinator
    coordinator = AgentCoordinator()
    
    result = coordinator.run_full_analysis("Manila,PH")
    
    print(f"Location: {result['location']}")
    print(f"Risk Level: {result['analysis_summary']['risk_level']}")
    print(f"Agents Executed: {result['execution_summary']['agents_executed']}")
    print(f"All Successful: {result['execution_summary']['all_successful']}")