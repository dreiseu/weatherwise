"""
Base Agent Class for WeatherWise
Foundation for all specialized agents
"""

import logging 
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all WeatherWise agents."""

    def __init__(self, agent_name: str):
        """Initialize base agent."""
        self.agent_name = agent_name
        self.created_at = datetime.now()
        self.execution_count = 0
        logger.info(f"Agent {self.agent_name} initialized")

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return results."""
        pass

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent with logging and error handling."""
        self.execution_count += 1

        try:
            logger.info(f"Executing {self.agent_name} (run #{self.execution_count})")
            result = self.process(input_data)

            result.update({
                "agent_name": self.agent_name,
                "execution_id": self.execution_count,
                "executed_at": datetime.now().isoformat(),
                "status": "success"
            })

            return result
        
        except Exception as e:
            logger.error(f"Agent {self.agent_name} failed: {e}")
            return {
                "agent_name": self.agent_name,
                "execution_id": self.execution_count,
                "executed_at": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }