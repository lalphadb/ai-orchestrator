"""
AI Orchestrator v8 - Agents System
Modular agent registry with tool restrictions and capabilities
"""
from .registry import AgentRegistry, Agent, AgentCapability
from .base import BaseAgent

__all__ = ['AgentRegistry', 'Agent', 'AgentCapability', 'BaseAgent']
