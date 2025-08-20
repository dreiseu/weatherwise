"""
Agent API Endpoints
Provides access to the complete agent system
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from ..core.database import get_db
from ..agents.agent_coordinator import AgentCoordinator
from ..agents.report_generation_agent import ReportGenerationAgent
from ..mcp.mcp_server import MCPWeatherServer

router = APIRouter()

class AgentAnalysisRequest(BaseModel):
    """Request for agent analysis."""
    location: str
    include_report: bool = True

@router.post("/analyze/comprehensive")
async def comprehensive_agent_analysis(
    request: AgentAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Run comprehensive analysis using all agents."""
    
    try:
        coordinator = AgentCoordinator()
        
        # Run full agent analysis
        analysis_result = coordinator.run_full_analysis(request.location)
        
        # Generate report if requested
        report_data = None
        if request.include_report:
            report_agent = ReportGenerationAgent()
            
            report_input = {
                "location": request.location,
                "weather_analysis": analysis_result["detailed_results"]["weather_analysis"],
                "risk_assessment": analysis_result["detailed_results"]["risk_assessment"],
                "action_plan": analysis_result["detailed_results"]["action_plan"]
            }
            
            report_result = report_agent.execute(report_input)
            report_data = report_result.get("report")
        
        return {
            "status": "success",
            "location": request.location,
            "analysis_summary": analysis_result["analysis_summary"],
            "detailed_results": analysis_result["detailed_results"],
            "execution_summary": analysis_result["execution_summary"],
            "report": report_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent analysis failed: {str(e)}")

@router.get("/mcp/tools")
async def list_mcp_tools():
    """List available MCP tools."""
    
    try:
        server = MCPWeatherServer()
        tools = server.list_tools()
        
        return {
            "status": "success",
            "available_tools": tools,
            "tool_count": len(tools)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP tools listing failed: {str(e)}")

@router.post("/mcp/execute")
async def execute_mcp_tool(
    tool_name: str,
    location: Optional[str] = None,
    query: Optional[str] = None,
    forecast_hours: Optional[int] = 24,
    days: Optional[int] = 3,
    n_results: Optional[int] = 3
):
    """Execute an MCP tool with parameters."""
    
    try:
        server = MCPWeatherServer()
        
        # Build parameters based on tool
        params = {}
        if location:
            params["location"] = location
        if query:
            params["query"] = query
        if forecast_hours and tool_name == "calculate_risk_score":
            params["forecast_hours"] = forecast_hours
        if days and tool_name == "analyze_weather_patterns":
            params["days"] = days
        if n_results and tool_name == "search_drrm_knowledge":
            params["n_results"] = n_results
        
        result = server.execute_tool(tool_name, **params)
        
        return {
            "status": "success",
            "tool_name": tool_name,
            "parameters": params,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP tool execution failed: {str(e)}")