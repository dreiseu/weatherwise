"""
Enhanced Agent Communication System
Adds pub/sub messaging and workflow capabilities to your existing agents
"""

import asyncio
import json
import uuid
import logging
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import text

# Configure logging
logger = logging.getLogger(__name__)

class MessageType(Enum):
    WEATHER_UPDATE = "weather_update"
    RISK_ASSESSMENT = "risk_assessment"
    ACTION_REQUIRED = "action_required"
    REPORT_GENERATED = "report_generated"
    SYSTEM_ALERT = "system_alert"
    WORKFLOW_START = "workflow_start"
    WORKFLOW_COMPLETE = "workflow_complete"

@dataclass
class AgentMessage:
    message_id: str
    message_type: MessageType
    sender_agent: str
    recipient_agent: str
    payload: Dict[str, Any]
    priority: int  # 1=highest, 5=lowest
    timestamp: datetime
    correlation_id: str = None
    workflow_id: str = None

class AgentEventBus:
    """Event bus for agent-to-agent communication."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.subscribers: Dict[MessageType, List[Callable]] = {}
        self.message_history: List[AgentMessage] = []
        self.active_workflows: Dict[str, Dict] = {}
    
    def subscribe(self, message_type: MessageType, handler: Callable):
        """Subscribe to specific message types."""
        if message_type not in self.subscribers:
            self.subscribers[message_type] = []
        self.subscribers[message_type].append(handler)
        logger.info(f"Handler subscribed to {message_type.value}")
    
    async def publish(self, message: AgentMessage):
        """Publish message to all subscribers and store in database."""
        self.message_history.append(message)
        
        # Store message in database
        await self._store_message_in_db(message)
        
        # Notify subscribers
        if message.message_type in self.subscribers:
            for handler in self.subscribers[message.message_type]:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Error in message handler: {e}")
    
    async def _store_message_in_db(self, message: AgentMessage):
        """Store message in database for persistence."""
        try:
            insert_sql = text("""
                INSERT INTO agent_messages (
                    id, message_type, sender_agent, recipient_agent, 
                    workflow_id, correlation_id, payload, priority, status
                ) VALUES (
                    :message_id, :message_type, :sender_agent, :recipient_agent,
                    :workflow_id, :correlation_id, :payload, :priority, 'sent'
                )
            """)
            
            self.db.execute(insert_sql, {
                "message_id": message.message_id,
                "message_type": message.message_type.value,
                "sender_agent": message.sender_agent,
                "recipient_agent": message.recipient_agent,
                "workflow_id": message.workflow_id,
                "correlation_id": message.correlation_id,
                "payload": json.dumps(message.payload),
                "priority": message.priority
            })
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to store message in database: {e}")
            self.db.rollback()
    
    def start_workflow(self, workflow_type: str, initiator: str, context: Dict, location: str = None) -> str:
        """Start a new multi-agent workflow."""
        workflow_id = str(uuid.uuid4())
        
        try:
            # Use the database function we created
            result = self.db.execute(text("""
                SELECT start_agent_workflow(:workflow_type, :initiator, :context, :location, 3)
            """), {
                "workflow_type": workflow_type,
                "initiator": initiator,
                "context": json.dumps(context),
                "location": location
            })
            
            db_workflow_id = result.scalar()
            self.db.commit()
            
            # Store in memory for quick access
            self.active_workflows[workflow_id] = {
                "id": workflow_id,
                "db_id": str(db_workflow_id),
                "workflow_type": workflow_type,
                "initiator": initiator,
                "context": context,
                "location": location,
                "started_at": datetime.now(timezone.utc),
                "status": "running",
                "agents_involved": [initiator],
                "messages": []
            }
            
            logger.info(f"Started workflow {workflow_type} with ID: {workflow_id}")
            return workflow_id
            
        except Exception as e:
            logger.error(f"Failed to start workflow: {e}")
            self.db.rollback()
            return None
    
    def complete_workflow(self, workflow_id: str, status: str = "completed"):
        """Complete a workflow."""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            
            try:
                # Update database
                self.db.execute(text("""
                    SELECT complete_agent_workflow(:workflow_id, :status)
                """), {
                    "workflow_id": workflow["db_id"],
                    "status": status
                })
                self.db.commit()
                
                # Update in-memory status
                workflow["status"] = status
                workflow["completed_at"] = datetime.now(timezone.utc)
                
                logger.info(f"Completed workflow {workflow_id} with status: {status}")
                
            except Exception as e:
                logger.error(f"Failed to complete workflow: {e}")
                self.db.rollback()

class EnhancedBaseAgent:
    """Enhanced base agent with communication capabilities."""
    
    def __init__(self, agent_name: str, event_bus: AgentEventBus):
        self.agent_name = agent_name
        self.event_bus = event_bus
        self.state = {}
        self.workflow_context = {}
        self.execution_count = 0
        
        # Subscribe to relevant message types
        self.setup_subscriptions()
        
        logger.info(f"Enhanced agent {agent_name} initialized")
    
    def setup_subscriptions(self):
        """Setup message subscriptions for this agent. Override in subclasses."""
        pass
    
    async def send_message(self, 
                          recipient: str, 
                          message_type: MessageType, 
                          payload: Dict[str, Any],
                          priority: int = 3,
                          correlation_id: str = None,
                          workflow_id: str = None):
        """Send message to another agent."""
        
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            sender_agent=self.agent_name,
            recipient_agent=recipient,
            payload=payload,
            priority=priority,
            timestamp=datetime.now(timezone.utc),
            correlation_id=correlation_id,
            workflow_id=workflow_id
        )
        
        await self.event_bus.publish(message)
        logger.info(f"{self.agent_name} sent {message_type.value} to {recipient}")
        return message.message_id
    
    async def handle_message(self, message: AgentMessage):
        """Handle incoming messages. Override in subclasses."""
        if message.recipient_agent != self.agent_name:
            return
        
        logger.info(f"{self.agent_name} received {message.message_type.value} from {message.sender_agent}")
        
        # Process message based on type
        handler_name = f"handle_{message.message_type.value}"
        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            await handler(message)
    
    async def log_execution(self, 
                          execution_type: str,
                          input_data: Dict,
                          output_data: Dict = None,
                          execution_time_ms: int = None,
                          workflow_id: str = None,
                          status: str = "completed",
                          error_message: str = None):
        """Log agent execution to database."""
        
        try:
            result = self.event_bus.db.execute(text("""
                SELECT log_agent_execution(
                    :agent_name, :execution_type, :workflow_id, :input_data,
                    :output_data, :status, :execution_time_ms, :error_message
                )
            """), {
                "agent_name": self.agent_name,
                "execution_type": execution_type,
                "workflow_id": workflow_id,
                "input_data": json.dumps(input_data),
                "output_data": json.dumps(output_data) if output_data else None,
                "status": status,
                "execution_time_ms": execution_time_ms,
                "error_message": error_message
            })
            
            execution_id = result.scalar()
            self.event_bus.db.commit()
            
            self.execution_count += 1
            logger.info(f"{self.agent_name} execution logged: {execution_id}")
            
            return str(execution_id)
            
        except Exception as e:
            logger.error(f"Failed to log execution for {self.agent_name}: {e}")
            self.event_bus.db.rollback()
            return None

# Enhanced versions of your existing agents
class EnhancedWeatherAnalysisAgent(EnhancedBaseAgent):
    """Enhanced weather analysis agent with collaboration capabilities."""
    
    def __init__(self, event_bus: AgentEventBus):
        super().__init__("WeatherAnalysisAgent", event_bus)
        
        # Import your existing agent
        from .weather_analysis_agent import WeatherAnalysisAgent
        self.core_agent = WeatherAnalysisAgent()
    
    def setup_subscriptions(self):
        """Subscribe to relevant message types."""
        self.event_bus.subscribe(MessageType.WEATHER_UPDATE, self.handle_message)
        self.event_bus.subscribe(MessageType.SYSTEM_ALERT, self.handle_message)
        self.event_bus.subscribe(MessageType.WORKFLOW_START, self.handle_message)
    
    async def analyze_with_collaboration(self, location: str, workflow_id: str = None):
        """Perform analysis and notify other agents."""
        import time
        start_time = time.time()
        
        try:
            # Perform standard analysis using your existing agent
            input_data = {"location": location, "analysis_type": "comprehensive"}
            analysis_result = self.core_agent.execute(input_data)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Log execution
            await self.log_execution(
                execution_type="collaborative_analysis",
                input_data=input_data,
                output_data=analysis_result,
                execution_time_ms=execution_time_ms,
                workflow_id=workflow_id
            )
            
            # Notify risk assessment agent if significant patterns found
            if analysis_result.get('patterns_count', 0) > 0 or analysis_result.get('anomalies_count', 0) > 0:
                await self.send_message(
                    recipient="RiskAssessmentAgent",
                    message_type=MessageType.WEATHER_UPDATE,
                    payload={
                        "location": location,
                        "analysis_result": analysis_result,
                        "requires_risk_assessment": True,
                        "priority": "high" if analysis_result.get('anomalies_count', 0) > 0 else "normal"
                    },
                    priority=2 if analysis_result.get('anomalies_count', 0) > 0 else 3,
                    workflow_id=workflow_id
                )
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Analysis failed for {location}: {e}")
            
            # Log failed execution
            await self.log_execution(
                execution_type="collaborative_analysis",
                input_data={"location": location},
                status="failed",
                error_message=str(e),
                workflow_id=workflow_id
            )
            
            return {"status": "error", "error": str(e)}
    
    async def handle_weather_update(self, message: AgentMessage):
        """Handle weather update messages."""
        payload = message.payload
        location = payload.get('location')
        
        if payload.get('trigger_analysis'):
            await self.analyze_with_collaboration(location, message.workflow_id)
    
    async def handle_workflow_start(self, message: AgentMessage):
        """Handle workflow start messages."""
        payload = message.payload
        workflow_type = payload.get('workflow_type')
        location = payload.get('location')
        
        if workflow_type in ['emergency', 'monitoring', 'investigation']:
            await self.analyze_with_collaboration(location, message.workflow_id)

class EnhancedRiskAssessmentAgent(EnhancedBaseAgent):
    """Enhanced risk assessment agent with collaboration capabilities."""
    
    def __init__(self, event_bus: AgentEventBus):
        super().__init__("RiskAssessmentAgent", event_bus)
        
        # Import your existing agent
        from .risk_assessment_agent import RiskAssessmentAgent
        self.core_agent = RiskAssessmentAgent()
    
    def setup_subscriptions(self):
        """Subscribe to relevant message types."""
        self.event_bus.subscribe(MessageType.WEATHER_UPDATE, self.handle_message)
        self.event_bus.subscribe(MessageType.RISK_ASSESSMENT, self.handle_message)
    
    async def assess_risk_with_collaboration(self, location: str, weather_context: Dict = None, workflow_id: str = None):
        """Assess risk and coordinate with action planning."""
        import time
        start_time = time.time()
        
        try:
            # Perform risk assessment using your existing agent
            input_data = {"location": location, "forecast_hours": 24}
            if weather_context:
                input_data["weather_context"] = weather_context
            
            risk_result = self.core_agent.execute(input_data)
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Log execution
            await self.log_execution(
                execution_type="collaborative_risk_assessment",
                input_data=input_data,
                output_data=risk_result,
                execution_time_ms=execution_time_ms,
                workflow_id=workflow_id
            )
            
            # If high risk, immediately notify action planning agent
            risk_level = risk_result.get('risk_level', 'LOW')
            if risk_level in ['HIGH', 'CRITICAL']:
                await self.send_message(
                    recipient="ActionPlanningAgent",
                    message_type=MessageType.ACTION_REQUIRED,
                    payload={
                        "location": location,
                        "risk_assessment": risk_result,
                        "urgency": "immediate" if risk_level == 'CRITICAL' else "high",
                        "weather_context": weather_context
                    },
                    priority=1 if risk_level == 'CRITICAL' else 2,
                    workflow_id=workflow_id
                )
            
            return risk_result
            
        except Exception as e:
            logger.error(f"Risk assessment failed for {location}: {e}")
            
            await self.log_execution(
                execution_type="collaborative_risk_assessment",
                input_data={"location": location},
                status="failed",
                error_message=str(e),
                workflow_id=workflow_id
            )
            
            return {"status": "error", "error": str(e)}
    
    async def handle_weather_update(self, message: AgentMessage):
        """Handle weather updates from weather analysis agent."""
        payload = message.payload
        
        if payload.get('requires_risk_assessment'):
            await self.assess_risk_with_collaboration(
                payload['location'], 
                payload.get('analysis_result'),
                message.workflow_id
            )

class EnhancedActionPlanningAgent(EnhancedBaseAgent):
    """Enhanced action planning agent with collaboration capabilities."""
    
    def __init__(self, event_bus: AgentEventBus):
        super().__init__("ActionPlanningAgent", event_bus)
        
        # Import your existing agent
        from .action_planning_agent import ActionPlanningAgent
        self.core_agent = ActionPlanningAgent()
    
    def setup_subscriptions(self):
        """Subscribe to relevant message types."""
        self.event_bus.subscribe(MessageType.ACTION_REQUIRED, self.handle_message)
    
    async def plan_actions_with_collaboration(self, location: str, risk_data: Dict, workflow_id: str = None):
        """Generate action plan and coordinate with report generation."""
        import time
        start_time = time.time()
        
        try:
            # Generate action plan using your existing agent
            input_data = {
                "location": location,
                "risk_level": risk_data.get('risk_level', 'UNKNOWN'),
                "category_risks": risk_data.get('category_risks', {})
            }
            
            action_result = self.core_agent.execute(input_data)
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Log execution
            await self.log_execution(
                execution_type="collaborative_action_planning",
                input_data=input_data,
                output_data=action_result,
                execution_time_ms=execution_time_ms,
                workflow_id=workflow_id
            )
            
            # Notify report generation agent for high-priority plans
            if action_result.get('plan_priority', 5) <= 2:
                await self.send_message(
                    recipient="ReportGenerationAgent",
                    message_type=MessageType.REPORT_GENERATED,
                    payload={
                        "location": location,
                        "action_plan": action_result,
                        "risk_data": risk_data,
                        "generate_immediate_report": True
                    },
                    priority=1,
                    workflow_id=workflow_id
                )
            
            return action_result
            
        except Exception as e:
            logger.error(f"Action planning failed for {location}: {e}")
            
            await self.log_execution(
                execution_type="collaborative_action_planning",
                input_data={"location": location},
                status="failed",
                error_message=str(e),
                workflow_id=workflow_id
            )
            
            return {"status": "error", "error": str(e)}
    
    async def handle_action_required(self, message: AgentMessage):
        """Handle action required messages."""
        payload = message.payload
        
        await self.plan_actions_with_collaboration(
            payload['location'],
            payload['risk_assessment'],
            message.workflow_id
        )

class WorkflowOrchestrator:
    """Orchestrates complex multi-agent workflows."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.event_bus = AgentEventBus(db_session)
        self.agents = {}
        self.setup_agents()
    
    def setup_agents(self):
        """Initialize and register all enhanced agents."""
        try:
            self.agents["WeatherAnalysisAgent"] = EnhancedWeatherAnalysisAgent(self.event_bus)
            self.agents["RiskAssessmentAgent"] = EnhancedRiskAssessmentAgent(self.event_bus)
            self.agents["ActionPlanningAgent"] = EnhancedActionPlanningAgent(self.event_bus)
            
            logger.info(f"Initialized {len(self.agents)} enhanced agents")
            
        except ImportError as e:
            logger.error(f"Failed to import agent: {e}")
            logger.info("Make sure your existing agent files are in the same directory")
    
    async def execute_emergency_workflow(self, location: str, trigger_event: str):
        """Execute emergency response workflow."""
        
        workflow_id = self.event_bus.start_workflow(
            workflow_type="emergency",
            initiator="WorkflowOrchestrator",
            context={
                "location": location,
                "trigger_event": trigger_event,
                "workflow_type": "emergency_response"
            },
            location=location
        )
        
        if not workflow_id:
            return {"status": "error", "message": "Failed to start workflow"}
        
        try:
            # Step 1: Trigger weather analysis
            if "WeatherAnalysisAgent" in self.agents:
                result = await self.agents["WeatherAnalysisAgent"].analyze_with_collaboration(
                    location, workflow_id
                )
                
                # The workflow continues through agent messaging...
                # Other agents will be automatically triggered based on the results
            
            return {
                "status": "success",
                "workflow_id": workflow_id,
                "message": f"Emergency workflow started for {location}",
                "trigger_event": trigger_event
            }
            
        except Exception as e:
            logger.error(f"Emergency workflow failed: {e}")
            self.event_bus.complete_workflow(workflow_id, "failed")
            return {"status": "error", "message": str(e)}
    
    async def execute_routine_monitoring_workflow(self, locations: List[str]):
        """Execute routine monitoring across multiple locations."""
        
        workflow_id = self.event_bus.start_workflow(
            workflow_type="routine_monitoring",
            initiator="WorkflowOrchestrator",
            context={
                "locations": locations,
                "workflow_type": "routine_monitoring"
            }
        )
        
        if not workflow_id:
            return {"status": "error", "message": "Failed to start workflow"}
        
        try:
            # Process multiple locations in parallel
            tasks = []
            for location in locations:
                if "WeatherAnalysisAgent" in self.agents:
                    task = self.agents["WeatherAnalysisAgent"].analyze_with_collaboration(
                        location, workflow_id
                    )
                    tasks.append(task)
            
            # Wait for all analyses to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Complete workflow
            self.event_bus.complete_workflow(workflow_id, "completed")
            
            return {
                "status": "success",
                "workflow_id": workflow_id,
                "locations_processed": len(locations),
                "results": len([r for r in results if not isinstance(r, Exception)]),
                "errors": len([r for r in results if isinstance(r, Exception)])
            }
            
        except Exception as e:
            logger.error(f"Routine monitoring workflow failed: {e}")
            self.event_bus.complete_workflow(workflow_id, "failed")
            return {"status": "error", "message": str(e)}

# Test function
async def test_enhanced_system(db_session: Session):
    """Test the enhanced agent communication system."""
    
    print("🧪 Testing Enhanced Agent Communication System...")
    
    # Create orchestrator
    orchestrator = WorkflowOrchestrator(db_session)
    
    # Test emergency workflow
    print("\n1. Testing Emergency Workflow...")
    result = await orchestrator.execute_emergency_workflow(
        location="Manila,PH",
        trigger_event="severe_weather_warning"
    )
    print(f"   Result: {result['status']} - {result.get('message', '')}")
    
    # Test routine monitoring
    print("\n2. Testing Routine Monitoring Workflow...")
    result = await orchestrator.execute_routine_monitoring_workflow(
        locations=["Manila,PH", "Cebu,PH"]
    )
    print(f"   Result: {result['status']} - Processed {result.get('results', 0)} locations")
    
    print("\n✅ Enhanced system test completed!")
    return orchestrator

if __name__ == "__main__":
    # This would be used for testing
    print("Enhanced Agent Communication System loaded successfully!")
    print("Import this module in your main application to use the enhanced agents.")