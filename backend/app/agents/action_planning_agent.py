"""
Action Planning Agent
Generates specific action plans based on risk assessments
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.agents.base_agent import BaseAgent

class ActionPlanningAgent(BaseAgent):
    """Agent specialized in generating actionable response plans."""
    
    def __init__(self):
        """Initialize action planning agent."""
        super().__init__("ActionPlanningAgent")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate action plan based on risk assessment."""
        
        risk_level = input_data.get("risk_level", "UNKNOWN")
        location = input_data.get("location", "Unknown")
        category_risks = input_data.get("category_risks", {})
        
        # Generate immediate actions
        immediate_actions = self._generate_immediate_actions(risk_level, category_risks)
        
        # Generate short-term actions
        short_term_actions = self._generate_short_term_actions(risk_level, category_risks)
        
        # Determine resource requirements
        resources_needed = self._determine_resources(risk_level, category_risks)
        
        # Set timeline
        timeline = self._set_timeline(risk_level)
        
        return {
            "location": location,
            "risk_level": risk_level,
            "action_plan": {
                "immediate_actions": immediate_actions,
                "short_term_actions": short_term_actions,
                "timeline": timeline,
                "resources_needed": resources_needed,
                "coordination_required": self._requires_coordination(risk_level)
            },
            "plan_priority": self._get_plan_priority(risk_level)
        }
    
    def _generate_immediate_actions(self, risk_level: str, category_risks: Dict) -> List[str]:
        """Generate immediate actions based on risk level."""
        actions = []
        
        if risk_level in ["CRITICAL", "HIGH"]:
            actions.extend([
                "Activate emergency operations center",
                "Alert emergency response teams",
                "Issue public warnings"
            ])
        
        # Specific category actions
        if category_risks.get('typhoon', 0) > 0.6:
            actions.extend([
                "Issue typhoon warnings",
                "Prepare evacuation orders",
                "Secure critical infrastructure"
            ])
        
        if category_risks.get('flooding', 0) > 0.6:
            actions.extend([
                "Deploy flood monitoring equipment",
                "Check drainage systems",
                "Prepare sandbags and barriers"
            ])
        
        if not actions:
            actions.append("Continue monitoring weather conditions")
        
        return actions
    
    def _generate_short_term_actions(self, risk_level: str, category_risks: Dict) -> List[str]:
        """Generate short-term actions (24-72 hours)."""
        actions = []
        
        if risk_level in ["CRITICAL", "HIGH"]:
            actions.extend([
                "Conduct community briefings",
                "Coordinate with neighboring LGUs",
                "Prepare relief supplies"
            ])
        
        if risk_level in ["MODERATE"]:
            actions.extend([
                "Review evacuation plans",
                "Test communication systems",
                "Update emergency contacts"
            ])
        
        actions.append("Monitor weather updates continuously")
        return actions
    
    def _determine_resources(self, risk_level: str, category_risks: Dict) -> List[str]:
        """Determine required resources."""
        resources = ["Emergency communications", "Weather monitoring equipment"]
        
        if risk_level in ["CRITICAL", "HIGH"]:
            resources.extend([
                "Emergency response vehicles",
                "Medical supplies",
                "Evacuation transportation",
                "Emergency shelters"
            ])
        
        if category_risks.get('flooding', 0) > 0.5:
            resources.extend(["Rescue boats", "Water pumps", "Sandbags"])
        
        return resources
    
    def _set_timeline(self, risk_level: str) -> str:
        """Set timeline based on risk level."""
        timelines = {
            "CRITICAL": "Immediate (0-6 hours)",
            "HIGH": "Urgent (6-24 hours)",
            "MODERATE": "Priority (24-48 hours)",
            "LOW": "Routine (48+ hours)",
            "UNKNOWN": "Monitor (ongoing)"
        }
        return timelines.get(risk_level, "Ongoing")
    
    def _requires_coordination(self, risk_level: str) -> bool:
        """Determine if inter-agency coordination is required."""
        return risk_level in ["CRITICAL", "HIGH"]
    
    def _get_plan_priority(self, risk_level: str) -> int:
        """Get numerical priority (1=highest, 5=lowest)."""
        priorities = {
            "CRITICAL": 1,
            "HIGH": 2,
            "MODERATE": 3,
            "LOW": 4,
            "UNKNOWN": 5
        }
        return priorities.get(risk_level, 5)

if __name__ == "__main__":
    # Test the action planning agent
    agent = ActionPlanningAgent()
    
    test_input = {
        "location": "Manila,PH",
        "risk_level": "MODERATE",
        "category_risks": {
            "typhoon": 0.3,
            "flooding": 0.7,
            "heat_stress": 0.2
        }
    }
    
    result = agent.execute(test_input)
    print(f"Agent: {result['agent_name']}")
    print(f"Status: {result['status']}")
    print(f"Plan Priority: {result.get('plan_priority', 'N/A')}")
    print(f"Timeline: {result['action_plan']['timeline']}")
    print(f"Immediate Actions: {len(result['action_plan']['immediate_actions'])}")