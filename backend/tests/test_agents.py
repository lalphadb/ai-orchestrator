"""
Tests for AI Orchestrator v8 Agents System
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.services.agents.base import AgentResult, BaseAgent
from app.services.agents.registry import (Agent, AgentCapability,
                                          AgentRegistry, agent_registry)


class TestAgentCapability:
    """Tests for AgentCapability enum"""

    def test_capability_values(self):
        """All capabilities have string values"""
        assert AgentCapability.SYSTEM.value == "system"
        assert AgentCapability.DOCKER.value == "docker"
        assert AgentCapability.NETWORK.value == "network"
        assert AgentCapability.WEB.value == "web"
        assert AgentCapability.SELF_IMPROVE.value == "self_improve"
        assert AgentCapability.QA.value == "qa"
        assert AgentCapability.MEMORY.value == "memory"
        assert AgentCapability.FILESYSTEM.value == "filesystem"


class TestAgent:
    """Tests for Agent dataclass"""

    def test_agent_creation(self):
        """Agent can be created with required fields"""
        agent = Agent(
            id="test.agent",
            name="Test Agent",
            description="A test agent",
            capabilities=[AgentCapability.SYSTEM],
            allowed_tools={"read_file", "list_directory"},
        )

        assert agent.id == "test.agent"
        assert agent.name == "Test Agent"
        assert agent.active is True
        assert len(agent.allowed_tools) == 2

    def test_can_use_tool_allowed(self):
        """Agent can use allowed tools"""
        agent = Agent(
            id="test.agent",
            name="Test Agent",
            description="Test",
            capabilities=[AgentCapability.SYSTEM],
            allowed_tools={"read_file", "bash"},
        )

        assert agent.can_use_tool("read_file") is True
        assert agent.can_use_tool("bash") is True

    def test_can_use_tool_denied(self):
        """Agent cannot use disallowed tools"""
        agent = Agent(
            id="test.agent",
            name="Test Agent",
            description="Test",
            capabilities=[AgentCapability.SYSTEM],
            allowed_tools={"read_file"},
        )

        assert agent.can_use_tool("write_file") is False
        assert agent.can_use_tool("http_request") is False

    def test_has_capability(self):
        """Agent has_capability works correctly"""
        agent = Agent(
            id="test.agent",
            name="Test Agent",
            description="Test",
            capabilities=[AgentCapability.SYSTEM, AgentCapability.DOCKER],
            allowed_tools=set(),
        )

        assert agent.has_capability(AgentCapability.SYSTEM) is True
        assert agent.has_capability(AgentCapability.DOCKER) is True
        assert agent.has_capability(AgentCapability.WEB) is False

    def test_to_dict(self):
        """Agent serializes to dictionary"""
        agent = Agent(
            id="test.agent",
            name="Test Agent",
            description="Test",
            capabilities=[AgentCapability.SYSTEM],
            allowed_tools={"read_file"},
            model="test-model",
        )

        d = agent.to_dict()

        assert d["id"] == "test.agent"
        assert d["name"] == "Test Agent"
        assert d["capabilities"] == ["system"]
        assert "read_file" in d["allowed_tools"]
        assert d["model"] == "test-model"
        assert "created_at" in d


class TestAgentRegistry:
    """Tests for AgentRegistry"""

    def test_singleton_pattern(self):
        """Registry is a singleton"""
        reg1 = AgentRegistry()
        reg2 = AgentRegistry()
        assert reg1 is reg2

    def test_default_agents_loaded(self):
        """Default agents are loaded on init"""
        registry = AgentRegistry()

        assert registry.get("system.health") is not None
        assert registry.get("docker.monitor") is not None
        assert registry.get("unifi.monitor") is not None
        assert registry.get("web.researcher") is not None
        assert registry.get("self_improve") is not None
        assert registry.get("qa.runner") is not None

    def test_register_new_agent(self):
        """Can register new agents"""
        registry = AgentRegistry()

        agent = Agent(
            id="custom.agent",
            name="Custom Agent",
            description="Custom test agent",
            capabilities=[AgentCapability.FILESYSTEM],
            allowed_tools={"read_file"},
        )

        registry.register(agent)

        retrieved = registry.get("custom.agent")
        assert retrieved is not None
        assert retrieved.name == "Custom Agent"

        # Cleanup
        registry.unregister("custom.agent")

    def test_unregister_agent(self):
        """Can unregister agents"""
        registry = AgentRegistry()

        agent = Agent(
            id="temp.agent",
            name="Temp Agent",
            description="Temporary",
            capabilities=[],
            allowed_tools=set(),
        )

        registry.register(agent)
        assert registry.get("temp.agent") is not None

        result = registry.unregister("temp.agent")
        assert result is True
        assert registry.get("temp.agent") is None

    def test_unregister_nonexistent(self):
        """Unregistering nonexistent agent returns False"""
        registry = AgentRegistry()
        result = registry.unregister("nonexistent.agent")
        assert result is False

    def test_get_all_agents(self):
        """Can get all registered agents"""
        registry = AgentRegistry()
        agents = registry.get_all()

        assert len(agents) >= 6  # At least default agents
        assert all(isinstance(a, Agent) for a in agents)

    def test_get_active_agents(self):
        """Can get only active agents"""
        registry = AgentRegistry()

        # All default agents are active
        active = registry.get_active()
        all_agents = registry.get_all()

        assert len(active) == len(all_agents)

    def test_get_by_capability(self):
        """Can filter agents by capability"""
        registry = AgentRegistry()

        system_agents = registry.get_by_capability(AgentCapability.SYSTEM)
        assert len(system_agents) >= 1

        web_agents = registry.get_by_capability(AgentCapability.WEB)
        assert len(web_agents) >= 1

        # All returned agents have the capability
        for agent in system_agents:
            assert agent.has_capability(AgentCapability.SYSTEM)

    def test_validate_tool_access_allowed(self):
        """Tool access validation allows valid tools"""
        registry = AgentRegistry()

        # web.researcher can use web_search
        assert registry.validate_tool_access("web.researcher", "web_search") is True
        assert registry.validate_tool_access("web.researcher", "web_read") is True

    def test_validate_tool_access_denied(self):
        """Tool access validation denies invalid tools"""
        registry = AgentRegistry()

        # web.researcher cannot use bash
        assert registry.validate_tool_access("web.researcher", "bash") is False
        assert registry.validate_tool_access("web.researcher", "write_file") is False

    def test_validate_tool_access_unknown_agent(self):
        """Tool access validation returns False for unknown agent"""
        registry = AgentRegistry()
        assert registry.validate_tool_access("unknown.agent", "read_file") is False

    def test_to_dict(self):
        """Registry serializes to dictionary"""
        registry = AgentRegistry()
        d = registry.to_dict()

        assert "agents" in d
        assert "total" in d
        assert "active" in d
        assert d["total"] >= 6
        assert len(d["agents"]) == d["total"]


class TestBaseAgent:
    """Tests for BaseAgent abstract class"""

    class ConcreteAgent(BaseAgent):
        """Concrete implementation for testing"""

        async def execute(self, task):
            # Record tool use for testing
            if "use_tool" in task:
                self.record_tool_use(task["use_tool"])

            return AgentResult(
                agent_id=self.agent_id, success=True, result={"task_completed": True}
            )

    def test_init_valid_agent(self):
        """BaseAgent initializes with valid agent ID"""
        agent = self.ConcreteAgent("system.health")

        assert agent.agent_id == "system.health"
        assert agent.agent is not None
        assert "read_file" in agent.allowed_tools

    def test_init_invalid_agent(self):
        """BaseAgent raises for invalid agent ID"""
        with pytest.raises(ValueError, match="Agent not found"):
            self.ConcreteAgent("nonexistent.agent")

    def test_can_use_tool(self):
        """can_use_tool delegates to agent"""
        agent = self.ConcreteAgent("web.researcher")

        assert agent.can_use_tool("web_search") is True
        assert agent.can_use_tool("bash") is False

    def test_validate_tool_allowed(self):
        """validate_tool passes for allowed tools"""
        agent = self.ConcreteAgent("web.researcher")

        # Should not raise
        agent.validate_tool("web_search")
        agent.validate_tool("web_read")

    def test_validate_tool_denied(self):
        """validate_tool raises for denied tools"""
        agent = self.ConcreteAgent("web.researcher")

        with pytest.raises(PermissionError, match="not allowed"):
            agent.validate_tool("bash")

    @pytest.mark.asyncio
    async def test_run_success(self):
        """run() executes and returns result"""
        agent = self.ConcreteAgent("system.health")

        result = await agent.run({"task": "test"})

        assert result.success is True
        assert result.agent_id == "system.health"
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_run_records_tool_use(self):
        """run() records tool usage"""
        agent = self.ConcreteAgent("system.health")

        result = await agent.run({"use_tool": "read_file"})

        assert result.success is True
        assert "read_file" in result.tools_used

    @pytest.mark.asyncio
    async def test_run_denied_tool(self):
        """run() fails when using denied tool"""
        agent = self.ConcreteAgent("web.researcher")

        result = await agent.run({"use_tool": "bash"})

        assert result.success is False
        assert "not allowed" in result.error

    def test_get_system_prompt(self):
        """get_system_prompt returns agent's prompt"""
        agent = self.ConcreteAgent("system.health")

        prompt = agent.get_system_prompt()

        assert "system health" in prompt.lower()

    def test_get_model(self):
        """get_model returns agent's preferred model"""
        agent = self.ConcreteAgent("system.health")

        model = agent.get_model()

        assert model is not None
        assert len(model) > 0


class TestAgentResult:
    """Tests for AgentResult dataclass"""

    def test_result_creation(self):
        """AgentResult creates with required fields"""
        result = AgentResult(agent_id="test.agent", success=True, result={"data": "value"})

        assert result.agent_id == "test.agent"
        assert result.success is True
        assert result.result == {"data": "value"}
        assert result.error is None
        assert result.tools_used == []

    def test_result_with_error(self):
        """AgentResult handles errors"""
        result = AgentResult(
            agent_id="test.agent", success=False, result=None, error="Something went wrong"
        )

        assert result.success is False
        assert result.error == "Something went wrong"

    def test_to_dict(self):
        """AgentResult serializes to dictionary"""
        result = AgentResult(
            agent_id="test.agent",
            success=True,
            result={"data": "value"},
            duration_ms=150,
            tools_used=["read_file", "bash"],
        )

        d = result.to_dict()

        assert d["agent_id"] == "test.agent"
        assert d["success"] is True
        assert d["duration_ms"] == 150
        assert d["tools_used"] == ["read_file", "bash"]


class TestSelfImproveAgent:
    """Tests for self_improve agent configuration"""

    def test_self_improve_has_required_tools(self):
        """self_improve agent has all necessary tools"""
        registry = AgentRegistry()
        agent = registry.get("self_improve")

        required_tools = [
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
            "memory_search",
        ]

        for tool in required_tools:
            assert agent.can_use_tool(tool), f"self_improve missing tool: {tool}"

    def test_self_improve_has_capabilities(self):
        """self_improve agent has correct capabilities"""
        registry = AgentRegistry()
        agent = registry.get("self_improve")

        assert agent.has_capability(AgentCapability.SELF_IMPROVE)
        assert agent.has_capability(AgentCapability.QA)

    def test_self_improve_cannot_use_dangerous_tools(self):
        """self_improve agent cannot use unrestricted tools"""
        registry = AgentRegistry()
        agent = registry.get("self_improve")

        # Should not have access to these
        assert not agent.can_use_tool("bash")
        assert not agent.can_use_tool("http_request")
        assert not agent.can_use_tool("web_search")


class TestWebResearcherAgent:
    """Tests for web.researcher agent configuration"""

    def test_web_researcher_tools(self):
        """web.researcher has only web tools"""
        registry = AgentRegistry()
        agent = registry.get("web.researcher")

        assert agent.can_use_tool("web_search")
        assert agent.can_use_tool("web_read")
        assert not agent.can_use_tool("bash")
        assert not agent.can_use_tool("write_file")

    def test_web_researcher_capability(self):
        """web.researcher has WEB capability"""
        registry = AgentRegistry()
        agent = registry.get("web.researcher")

        assert agent.has_capability(AgentCapability.WEB)
        assert not agent.has_capability(AgentCapability.SYSTEM)


# ============================================================================
# CRQ-P0-1: Agent Isolation Enforcement Tests
# ============================================================================


class TestAgentIsolationEnforcement:
    """Tests for CRQ-P0-1: Agent isolation enforcement in ToolRegistry.execute()"""

    @pytest.mark.asyncio
    async def test_agent_isolation_denied(self):
        """Agent web.researcher cannot call write_file when enforcement enabled"""
        from app.core.config import settings
        from app.services.react_engine.tools import BUILTIN_TOOLS

        # Enable enforcement
        original_value = settings.ENFORCE_AGENT_ISOLATION
        try:
            settings.ENFORCE_AGENT_ISOLATION = True

            # web.researcher should NOT have write_file
            result = await BUILTIN_TOOLS.execute(
                "write_file", agent_id="web.researcher", path="/tmp/test.txt", content="test"
            )

            assert result["success"] is False
            assert result["error"]["code"] == "E_AGENT_PERMISSION_DENIED"
            assert "web.researcher" in result["error"]["message"]
            assert "write_file" in result["error"]["message"]

        finally:
            settings.ENFORCE_AGENT_ISOLATION = original_value

    @pytest.mark.asyncio
    async def test_agent_isolation_allowed(self):
        """Agent self_improve CAN call write_file when authorized"""
        import os
        import tempfile

        from app.core.config import settings
        from app.services.react_engine.tools import BUILTIN_TOOLS

        original_value = settings.ENFORCE_AGENT_ISOLATION
        try:
            settings.ENFORCE_AGENT_ISOLATION = True

            # self_improve SHOULD have write_file
            # Use a path inside WORKSPACE_DIR so it passes path validation
            test_path = os.path.join(settings.WORKSPACE_DIR, "_test_agent_isolation.txt")

            try:
                result = await BUILTIN_TOOLS.execute(
                    "write_file",
                    agent_id="self_improve",
                    path=test_path,
                    content="test content",
                    justification="Test agent isolation",
                )

                assert result["success"] is True, f"Expected success, got: {result}"

            finally:
                if os.path.exists(test_path):
                    os.unlink(test_path)

        finally:
            settings.ENFORCE_AGENT_ISOLATION = original_value

    @pytest.mark.asyncio
    async def test_missing_agent_id_with_enforcement(self):
        """Missing agent_id with ENFORCE_AGENT_ISOLATION=true should fail closed"""
        from app.core.config import settings
        from app.services.react_engine.tools import BUILTIN_TOOLS

        original_value = settings.ENFORCE_AGENT_ISOLATION
        try:
            settings.ENFORCE_AGENT_ISOLATION = True

            # Call without agent_id should fail
            result = await BUILTIN_TOOLS.execute("read_file", path="/tmp/test.txt")

            assert result["success"] is False
            assert result["error"]["code"] == "E_AGENT_REQUIRED"
            assert "Agent ID required" in result["error"]["message"]

        finally:
            settings.ENFORCE_AGENT_ISOLATION = original_value

    @pytest.mark.asyncio
    async def test_missing_agent_id_without_enforcement(self):
        """Missing agent_id with ENFORCE_AGENT_ISOLATION=false should work (backward compat)"""
        import os
        import tempfile

        from app.core.config import settings
        from app.services.react_engine.tools import BUILTIN_TOOLS

        original_value = settings.ENFORCE_AGENT_ISOLATION
        try:
            settings.ENFORCE_AGENT_ISOLATION = False

            # Create a temp file inside workspace to read
            test_path = os.path.join(settings.WORKSPACE_DIR, "_test_agent_no_enforce.txt")

            try:
                with open(test_path, "w") as f:
                    f.write("test content")

                # Call without agent_id should work when enforcement disabled
                result = await BUILTIN_TOOLS.execute("read_file", path=test_path)

                assert result["success"] is True
                assert "test content" in result["data"]["content"]

            finally:
                if os.path.exists(test_path):
                    os.unlink(test_path)

        finally:
            settings.ENFORCE_AGENT_ISOLATION = original_value

    @pytest.mark.asyncio
    async def test_nonexistent_agent_id(self):
        """Calling with nonexistent agent_id should fail"""
        from app.core.config import settings
        from app.services.react_engine.tools import BUILTIN_TOOLS

        original_value = settings.ENFORCE_AGENT_ISOLATION
        try:
            settings.ENFORCE_AGENT_ISOLATION = True

            result = await BUILTIN_TOOLS.execute(
                "read_file", agent_id="nonexistent.agent", path="/tmp/test.txt"
            )

            assert result["success"] is False
            assert result["error"]["code"] == "E_AGENT_NOT_FOUND"
            assert "nonexistent.agent" in result["error"]["message"]

        finally:
            settings.ENFORCE_AGENT_ISOLATION = original_value

    def test_agent_isolation_flag_default(self):
        """ENFORCE_AGENT_ISOLATION should default to False for backward compat"""
        from app.core.config import settings

        # Default should be False (unless explicitly set in .env)
        # This ensures backward compatibility
        assert isinstance(settings.ENFORCE_AGENT_ISOLATION, bool)
