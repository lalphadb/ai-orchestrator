"""
AI Orchestrator v8 - Base Agent
Abstract base class for agent implementations
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .registry import Agent, AgentCapability, agent_registry

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Result from agent execution"""

    agent_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    duration_ms: int = 0
    tools_used: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.tools_used is None:
            self.tools_used = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "tools_used": self.tools_used,
            "metadata": self.metadata,
        }


class BaseAgent(ABC):
    """
    Abstract base class for all agents
    Provides common functionality and enforces tool restrictions
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self._agent = agent_registry.get(agent_id)
        if not self._agent:
            raise ValueError(f"Agent not found in registry: {agent_id}")

        self._tools_used: List[str] = []
        self._start_time: Optional[datetime] = None

    @property
    def agent(self) -> Agent:
        """Get agent definition"""
        return self._agent

    @property
    def allowed_tools(self) -> List[str]:
        """Get list of allowed tools"""
        return list(self._agent.allowed_tools)

    def can_use_tool(self, tool_name: str) -> bool:
        """Check if tool is allowed"""
        return self._agent.can_use_tool(tool_name)

    def validate_tool(self, tool_name: str) -> None:
        """Validate tool access, raise if denied"""
        if not self.can_use_tool(tool_name):
            raise PermissionError(f"Agent {self.agent_id} is not allowed to use tool: {tool_name}")

    def record_tool_use(self, tool_name: str) -> None:
        """Record tool usage for audit"""
        self.validate_tool(tool_name)
        self._tools_used.append(tool_name)
        logger.debug(f"Agent {self.agent_id} used tool: {tool_name}")

    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        """
        Execute the agent's task
        Must be implemented by subclasses
        """
        pass

    async def run(self, task: Dict[str, Any]) -> AgentResult:
        """
        Run the agent with proper setup and teardown
        Wraps execute() with timing and error handling
        """
        self._start_time = datetime.now(timezone.utc)
        self._tools_used = []

        try:
            if not self._agent.active:
                return AgentResult(
                    agent_id=self.agent_id,
                    success=False,
                    result=None,
                    error=f"Agent {self.agent_id} is not active",
                )

            result = await self.execute(task)

            # Calculate duration
            duration = datetime.now(timezone.utc) - self._start_time
            result.duration_ms = int(duration.total_seconds() * 1000)
            result.tools_used = self._tools_used

            return result

        except PermissionError as e:
            duration = datetime.now(timezone.utc) - self._start_time
            return AgentResult(
                agent_id=self.agent_id,
                success=False,
                result=None,
                error=str(e),
                duration_ms=int(duration.total_seconds() * 1000),
                tools_used=self._tools_used,
            )

        except Exception as e:
            logger.exception(f"Agent {self.agent_id} execution failed")
            duration = datetime.now(timezone.utc) - self._start_time
            return AgentResult(
                agent_id=self.agent_id,
                success=False,
                result=None,
                error=str(e),
                duration_ms=int(duration.total_seconds() * 1000),
                tools_used=self._tools_used,
            )

    def get_system_prompt(self) -> str:
        """Get agent's system prompt"""
        return self._agent.system_prompt

    def get_model(self) -> str:
        """Get agent's preferred model"""
        return self._agent.model
