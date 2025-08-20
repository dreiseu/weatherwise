"""
MCP Server for WeatherWise
Provides tools for weather data access and DRRM operations
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
import json

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.weather import CurrentWeather
from app.services.weather_analysis import WeatherAnalysisService
from app.services.rag_service import RAGService

class MCPWeatherServer:
    """MCP server providing weather and DRRM tools."""
    
    def __init__(self):
        """Initialize MCP server."""
        self.db = SessionLocal()
        self.analysis_service = WeatherAnalysisService(self.db)
        self.rag_service = RAGService()
        
        # Define available tools
        self.tools = {
            "get_current_weather": self.get_current_weather,
            "calculate_risk_score": self.calculate_risk_score,
            "search_drrm_knowledge": self.search_drrm_knowledge,
            "analyze_weather_patterns": self.analyze_weather_patterns
        }
    
    def get_current_weather(self, location: str) -> Dict[str, Any]:
        """Tool: Get current weather data for location."""
        try:
            weather_data = self.db.query(CurrentWeather).filter(
                CurrentWeather.location == location
            ).order_by(CurrentWeather.timestamp.desc()).first()
            
            if not weather_data:
                return {"error": f"No weather data found for {location}"}
            
            return {
                "location": weather_data.location,
                "temperature": weather_data.temperature,
                "humidity": weather_data.humidity,
                "wind_speed": weather_data.wind_speed,
                "pressure": weather_data.pressure,
                "weather_condition": weather_data.weather_condition,
                "timestamp": weather_data.timestamp.isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def calculate_risk_score(self, location: str, forecast_hours: int = 24) -> Dict[str, Any]:
        """Tool: Calculate disaster risk score for location."""
        try:
            risk_score = self.analysis_service.calculate_risk_scores(location, forecast_hours)
            
            return {
                "location": location,
                "overall_risk": risk_score.overall_risk,
                "risk_level": risk_score.risk_level,
                "confidence": risk_score.confidence,
                "category_risks": risk_score.category_risks,
                "recommendations": risk_score.recommendations[:3]  # Top 3
            }
        except Exception as e:
            return {"error": str(e)}
    
    def search_drrm_knowledge(self, query: str, n_results: int = 3) -> Dict[str, Any]:
        """Tool: Search DRRM knowledge base."""
        try:
            results = self.rag_service.vector_service.search(query, n_results)
            
            if results and results['documents'][0]:
                return {
                    "query": query,
                    "results_found": len(results['documents'][0]),
                    "knowledge": results['documents'][0],
                    "metadata": results.get('metadatas', [[]])[0]
                }
            else:
                return {"query": query, "results_found": 0, "knowledge": []}
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_weather_patterns(self, location: str, days: int = 3) -> Dict[str, Any]:
        """Tool: Analyze weather patterns for location."""
        try:
            patterns = self.analysis_service.analyze_weather_patterns(location, days)
            
            return {
                "location": location,
                "analysis_period_days": days,
                "patterns_found": len(patterns),
                "patterns": [
                    {
                        "type": p.pattern_type,
                        "confidence": p.confidence,
                        "risk_level": p.risk_level,
                        "description": p.description
                    } for p in patterns
                ]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name with parameters."""
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            return self.tools[tool_name](**kwargs)
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
    
    def list_tools(self) -> List[str]:
        """List available tools."""
        return list(self.tools.keys())
    
    def __del__(self):
        """Cleanup database connection."""
        if hasattr(self, 'db'):
            self.db.close()

if __name__ == "__main__":
    # Test MCP server
    server = MCPWeatherServer()
    
    print("Available tools:", server.list_tools())
    
    # Test weather tool
    weather_result = server.execute_tool("get_current_weather", location="Manila,PH")
    print(f"Weather tool result: {weather_result.get('temperature', 'No data')}°C")
    
    # Test knowledge search tool
    knowledge_result = server.execute_tool("search_drrm_knowledge", query="typhoon preparation")
    print(f"Knowledge search found: {knowledge_result.get('results_found', 0)} results")