"""
Report Generation Agent
Creates comprehensive DRRM reports from agent analysis results
"""

import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.append(str(backend_dir.parent))

from app.agents.base_agent import BaseAgent
from app.services.rag_service import RAGService

class ReportGenerationAgent(BaseAgent):
    """Agent specialized in generating comprehensive DRRM reports."""
    
    def __init__(self):
        """Initialize report generation agent."""
        super().__init__("ReportGenerationAgent")
        self.rag_service = RAGService()
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive report from analysis results."""
        
        location = input_data.get("location", "Unknown")
        weather_analysis = input_data.get("weather_analysis", {})
        risk_assessment = input_data.get("risk_assessment", {})
        action_plan = input_data.get("action_plan", {})
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            location, risk_assessment, action_plan
        )
        
        # Generate detailed sections
        risk_analysis_section = self._generate_risk_analysis_section(risk_assessment)
        recommendations_section = self._generate_recommendations_section(action_plan)
        weather_summary = self._generate_weather_summary(weather_analysis)
        
        # Create full report
        full_report = {
            "report_header": {
                "title": f"DRRM Analysis Report - {location}",
                "generated_at": datetime.now().isoformat(),
                "report_type": "Comprehensive Weather Risk Assessment",
                "location": location
            },
            "executive_summary": executive_summary,
            "sections": {
                "weather_analysis": weather_summary,
                "risk_assessment": risk_analysis_section,
                "action_recommendations": recommendations_section
            },
            "metadata": {
                "data_sources": ["Weather monitoring", "Historical patterns", "DRRM protocols"],
                "confidence_level": risk_assessment.get("confidence", 0.5),
                "next_review": "24 hours"
            }
        }
        
        return {
            "location": location,
            "report": full_report,
            "report_length": len(str(full_report)),
            "sections_count": len(full_report["sections"])
        }
    
    def _generate_executive_summary(self, location: str, risk_assessment: Dict, action_plan: Dict) -> str:
        """Generate executive summary."""
        
        risk_level = risk_assessment.get("risk_level", "UNKNOWN")
        overall_risk = risk_assessment.get("overall_risk", 0)
        priority = action_plan.get("plan_priority", 5)
        
        summary = f"""
EXECUTIVE SUMMARY

Location: {location}
Assessment Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Current Risk Level: {risk_level}
Overall Risk Score: {overall_risk:.2f}
Response Priority: {priority}/5

Key Findings:
- Weather conditions assessed for disaster risk potential
- Risk evaluation completed across multiple hazard categories
- Action plan developed with specific timeline requirements

Immediate Actions Required: {priority <= 2}
Coordination Needed: {risk_level in ['CRITICAL', 'HIGH']}

This report provides comprehensive analysis and actionable recommendations for disaster risk management in {location}.
        """.strip()
        
        return summary
    
    def _generate_risk_analysis_section(self, risk_assessment: Dict) -> str:
        """Generate detailed risk analysis section."""
        
        category_risks = risk_assessment.get("category_risks", {})
        contributing_factors = risk_assessment.get("contributing_factors", [])
        
        section = "RISK ANALYSIS\n\nCategory-Specific Risk Scores:\n"
        
        for category, score in category_risks.items():
            risk_descriptor = "High" if score > 0.6 else "Moderate" if score > 0.3 else "Low"
            section += f"- {category.replace('_', ' ').title()}: {score:.2f} ({risk_descriptor})\n"
        
        if contributing_factors:
            section += "\nContributing Risk Factors:\n"
            for factor in contributing_factors:
                section += f"- {factor}\n"
        
        return section
    
    def _generate_recommendations_section(self, action_plan: Dict) -> str:
        """Generate recommendations section."""
        
        if "action_plan" not in action_plan:
            return "RECOMMENDATIONS\n\nNo specific action plan available."
        
        plan_data = action_plan["action_plan"]
        
        section = "ACTION RECOMMENDATIONS\n\n"
        section += f"Timeline: {plan_data.get('timeline', 'Not specified')}\n\n"
        
        immediate_actions = plan_data.get("immediate_actions", [])
        if immediate_actions:
            section += "Immediate Actions (0-6 hours):\n"
            for action in immediate_actions:
                section += f"- {action}\n"
            section += "\n"
        
        short_term_actions = plan_data.get("short_term_actions", [])
        if short_term_actions:
            section += "Short-term Actions (24-72 hours):\n"
            for action in short_term_actions:
                section += f"- {action}\n"
            section += "\n"
        
        resources = plan_data.get("resources_needed", [])
        if resources:
            section += "Required Resources:\n"
            for resource in resources:
                section += f"- {resource}\n"
        
        return section
    
    def _generate_weather_summary(self, weather_analysis: Dict) -> str:
        """Generate weather analysis summary."""
        
        patterns_count = weather_analysis.get("patterns_count", 0)
        anomalies_count = weather_analysis.get("anomalies_count", 0)
        
        summary = f"""WEATHER ANALYSIS SUMMARY

Patterns Detected: {patterns_count}
Anomalies Found: {anomalies_count}

Analysis Status: {'Complete' if patterns_count > 0 or anomalies_count > 0 else 'Normal conditions detected'}

Weather conditions have been analyzed for disaster risk indicators. Current conditions show {"elevated risk patterns" if patterns_count > 0 else "normal atmospheric conditions"}.
        """.strip()
        
        return summary

if __name__ == "__main__":
    # Test the report generation agent
    agent = ReportGenerationAgent()
    
    test_input = {
        "location": "Manila,PH",
        "weather_analysis": {"patterns_count": 0, "anomalies_count": 0},
        "risk_assessment": {
            "risk_level": "MODERATE",
            "overall_risk": 0.45,
            "confidence": 0.8,
            "category_risks": {"typhoon": 0.2, "flooding": 0.6, "heat_stress": 0.3},
            "contributing_factors": ["High humidity levels", "Urban heat island effect"]
        },
        "action_plan": {
            "plan_priority": 3,
            "action_plan": {
                "timeline": "Priority (24-48 hours)",
                "immediate_actions": ["Monitor drainage systems", "Check flood barriers"],
                "short_term_actions": ["Review evacuation routes", "Update emergency contacts"],
                "resources_needed": ["Emergency communications", "Water pumps"]
            }
        }
    }
    
    result = agent.execute(test_input)
    print(f"Agent: {result['agent_name']}")
    print(f"Status: {result['status']}")
    print(f"Report Length: {result.get('report_length', 0)} characters")
    print(f"Sections: {result.get('sections_count', 0)}")