"""
AI Orchestrator v8 - Agents API Routes
REST endpoints for agent management
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from app.services.agents.registry import agent_registry, AgentCapability

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.get("/")
async def list_agents() -> Dict[str, Any]:
    """List all registered agents"""
    return agent_registry.to_dict()


@router.get("/{agent_id}")
async def get_agent(agent_id: str) -> Dict[str, Any]:
    """Get agent by ID"""
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return agent.to_dict()


@router.get("/capability/{capability}")
async def get_agents_by_capability(capability: str) -> Dict[str, Any]:
    """Get agents with a specific capability"""
    try:
        cap = AgentCapability(capability)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid capability: {capability}. Valid: {[c.value for c in AgentCapability]}"
        )
    
    agents = agent_registry.get_by_capability(cap)
    return {
        "capability": capability,
        "agents": [a.to_dict() for a in agents],
        "count": len(agents)
    }


@router.get("/{agent_id}/validate/{tool_name}")
async def validate_tool_access(agent_id: str, tool_name: str) -> Dict[str, Any]:
    """Check if an agent can use a specific tool"""
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    
    allowed = agent.can_use_tool(tool_name)
    return {
        "agent_id": agent_id,
        "tool": tool_name,
        "allowed": allowed
    }


@router.get("/active")
async def list_active_agents() -> Dict[str, Any]:
    """List only active agents"""
    agents = agent_registry.get_active()
    return {
        "agents": [a.to_dict() for a in agents],
        "count": len(agents)
    }
