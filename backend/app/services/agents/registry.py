"""
AI Orchestrator v8 - Agent Registry
Central registry for all agents with tool restrictions
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Callable, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AgentCapability(Enum):
    """Agent capability categories"""
    SYSTEM = "system"           # System health, monitoring
    DOCKER = "docker"           # Container management
    NETWORK = "network"         # Network/UniFi monitoring
    WEB = "web"                 # Web research, scraping
    SELF_IMPROVE = "self_improve"  # Auto-improvement
    QA = "qa"                   # Quality assurance
    MEMORY = "memory"           # ChromaDB memory
    FILESYSTEM = "filesystem"   # File operations


@dataclass
class Agent:
    """Agent definition with restricted tool access"""
    id: str
    name: str
    description: str
    capabilities: List[AgentCapability]
    allowed_tools: Set[str]
    system_prompt: str = ""
    model: str = "qwen2.5-coder:7b"
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def can_use_tool(self, tool_name: str) -> bool:
        """Check if agent is allowed to use a specific tool"""
        return tool_name in self.allowed_tools
    
    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has a specific capability"""
        return capability in self.capabilities
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize agent to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "capabilities": [c.value for c in self.capabilities],
            "allowed_tools": list(self.allowed_tools),
            "system_prompt": self.system_prompt,
            "model": self.model,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


class AgentRegistry:
    """
    Central registry for managing agents
    Thread-safe singleton pattern
    """
    _instance = None
    _agents: Dict[str, Agent] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents = {}
            cls._instance._initialize_default_agents()
        return cls._instance
    
    def _initialize_default_agents(self):
        """Initialize built-in agents"""
        
        # System Health Agent
        self.register(Agent(
            id="system.health",
            name="System Health Monitor",
            description="Monitors system resources, services, and infrastructure health",
            capabilities=[AgentCapability.SYSTEM],
            allowed_tools={
                "read_file",
                "list_directory",
                "bash"  # Restricted to safe commands
            },
            system_prompt="""You are a system health monitoring agent.
Your role is to check system resources, service status, and report issues.
Only use safe, read-only commands. Never modify system state.""",
            model="qwen2.5-coder:7b"
        ))
        
        # Docker Monitor Agent
        self.register(Agent(
            id="docker.monitor",
            name="Docker Container Monitor",
            description="Monitors Docker containers, images, and networks",
            capabilities=[AgentCapability.DOCKER, AgentCapability.SYSTEM],
            allowed_tools={
                "read_file",
                "list_directory",
                "bash"  # docker ps, docker stats, etc.
            },
            system_prompt="""You are a Docker monitoring agent.
Your role is to check container status, resource usage, and logs.
Use docker commands for inspection only. Never start/stop/remove containers.""",
            model="qwen2.5-coder:7b"
        ))
        
        # UniFi Network Monitor Agent
        self.register(Agent(
            id="unifi.monitor",
            name="UniFi Network Monitor",
            description="Monitors UniFi network devices and clients",
            capabilities=[AgentCapability.NETWORK],
            allowed_tools={
                "read_file",
                "http_request"  # For UniFi API
            },
            system_prompt="""You are a UniFi network monitoring agent.
Your role is to check network device status, client connections, and alerts.
Only perform read operations. Never modify network configuration.""",
            model="qwen2.5-coder:7b"
        ))
        
        # Web Researcher Agent
        self.register(Agent(
            id="web.researcher",
            name="Web Researcher",
            description="Searches and reads web content for research tasks",
            capabilities=[AgentCapability.WEB],
            allowed_tools={
                "web_search",
                "web_read"
            },
            system_prompt="""You are a web research agent.
Your role is to search the web and extract relevant information.
Summarize findings clearly and cite sources.""",
            model="qwen2.5-coder:7b"
        ))
        
        # Self-Improve Agent
        self.register(Agent(
            id="self_improve",
            name="Self-Improvement Agent",
            description="Analyzes system performance and suggests improvements",
            capabilities=[AgentCapability.SELF_IMPROVE, AgentCapability.QA],
            allowed_tools={
                "read_file",
                "write_file",
                "patch_file",
                "list_directory",
                "search_directory",
                "run_tests",
                "run_lint",
                "git_status",
                "git_diff",
                "git_log",
                "memory_store",
                "memory_search"
            },
            system_prompt="""You are a self-improvement agent.
Your role is to analyze code, logs, and metrics to suggest improvements.
All changes must pass QA tests. Create backups before modifications.
Follow the improvement pipeline: analyze → patch → verify → rollback if fail.""",
            model="qwen2.5-coder:14b"
        ))
        
        # QA Runner Agent
        self.register(Agent(
            id="qa.runner",
            name="QA Test Runner",
            description="Runs tests, linting, and quality checks",
            capabilities=[AgentCapability.QA],
            allowed_tools={
                "read_file",
                "list_directory",
                "run_tests",
                "run_lint",
                "bash"  # For test commands
            },
            system_prompt="""You are a QA testing agent.
Your role is to run tests, check code quality, and report results.
Execute test suites and report failures clearly.""",
            model="qwen2.5-coder:7b"
        ))
        
        logger.info(f"Initialized {len(self._agents)} default agents")
    
    def register(self, agent: Agent) -> None:
        """Register a new agent"""
        if agent.id in self._agents:
            logger.warning(f"Overwriting existing agent: {agent.id}")
        self._agents[agent.id] = agent
        logger.info(f"Registered agent: {agent.id}")
    
    def unregister(self, agent_id: str) -> bool:
        """Unregister an agent"""
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
            return True
        return False
    
    def get(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self._agents.get(agent_id)
    
    def get_all(self) -> List[Agent]:
        """Get all registered agents"""
        return list(self._agents.values())
    
    def get_active(self) -> List[Agent]:
        """Get all active agents"""
        return [a for a in self._agents.values() if a.active]
    
    def get_by_capability(self, capability: AgentCapability) -> List[Agent]:
        """Get agents with a specific capability"""
        return [a for a in self._agents.values() if a.has_capability(capability)]
    
    def validate_tool_access(self, agent_id: str, tool_name: str) -> bool:
        """Validate if an agent can use a specific tool"""
        agent = self.get(agent_id)
        if not agent:
            logger.warning(f"Unknown agent: {agent_id}")
            return False
        
        if not agent.active:
            logger.warning(f"Agent {agent_id} is not active")
            return False
        
        allowed = agent.can_use_tool(tool_name)
        if not allowed:
            logger.warning(f"Agent {agent_id} denied access to tool: {tool_name}")
        
        return allowed
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize registry to dictionary"""
        return {
            "agents": [a.to_dict() for a in self._agents.values()],
            "total": len(self._agents),
            "active": len(self.get_active())
        }


# Global registry instance
agent_registry = AgentRegistry()
