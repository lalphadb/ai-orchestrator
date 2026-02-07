"""
WebSocket Event Models for AI Orchestrator v8
Defines Pydantic models for 8 WebSocket event types with strict validation.

INVARIANTS (from CLAUDE.md):
- Every event MUST include: type, timestamp (ISO 8601), run_id
- Every run MUST terminate with EXACTLY ONE terminal event: complete OR error
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utcnow_iso() -> str:
    """Generate ISO 8601 timestamp in UTC."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ===== BASE EVENT =====


class WSEventBase(BaseModel):
    """
    Base class for all WebSocket events.
    Enforces invariant: Every event has type, timestamp (ISO 8601), run_id.
    CRQ-P1-6: Added correlation_id for distributed tracing.
    """

    type: str = Field(..., description="Event type identifier")
    timestamp: str = Field(default_factory=utcnow_iso, description="ISO 8601 timestamp")
    run_id: str = Field(..., description="Unique identifier for the run")
    correlation_id: Optional[str] = Field(
        None, description="Correlation ID for distributed tracing (CRQ-P1-6)"
    )
    data: Dict[str, Any] = Field(default_factory=dict, description="Event payload")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Validate ISO 8601 format."""
        try:
            # Accept both with and without 'Z' suffix
            if v.endswith("Z"):
                datetime.fromisoformat(v[:-1])
            else:
                datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid ISO 8601 timestamp: {v}")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "thinking",
                "timestamp": "2026-01-28T10:30:00.000Z",
                "run_id": "a1b2c3d4",
                "data": {"message": "Analyzing request..."},
            }
        }
    )


# ===== SPECIFIC EVENT TYPES =====


class WSThinkingEvent(WSEventBase):
    """
    Thinking event: LLM reasoning step.
    Example: {"type": "thinking", "timestamp": "...", "run_id": "...", "data": {"message": "..."}}
    """

    type: Literal["thinking"] = "thinking"
    data: Dict[str, Any] = Field(
        ...,
        description="Thinking data with 'message' key",
        examples=[{"message": "Analyzing the request to determine next steps..."}],
    )

    @field_validator("data")
    @classmethod
    def validate_thinking_data(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure 'message' key exists."""
        if "message" not in v:
            raise ValueError("Thinking event data must contain 'message' key")
        return v


class WSPhaseEvent(WSEventBase):
    """
    Phase event: Workflow phase transition.
    Example: {"type": "phase", "timestamp": "...", "run_id": "...", "data": {"phase": "spec", "status": "starting"}}
    """

    type: Literal["phase"] = "phase"
    data: Dict[str, Any] = Field(
        ...,
        description="Phase data with 'phase' and 'status' keys",
        examples=[
            {"phase": "spec", "status": "starting"},
            {"phase": "execute", "status": "complete", "result": "Success"},
        ],
    )

    @field_validator("data")
    @classmethod
    def validate_phase_data(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure 'phase' and 'status' keys exist."""
        if "phase" not in v:
            raise ValueError("Phase event data must contain 'phase' key")
        if "status" not in v:
            raise ValueError("Phase event data must contain 'status' key")
        # Valid phases: spec, plan, execute, verify, repair, complete
        valid_phases = ["spec", "plan", "execute", "verify", "repair", "complete"]
        if v["phase"] not in valid_phases:
            raise ValueError(f"Invalid phase '{v['phase']}', must be one of: {valid_phases}")
        # Valid statuses: starting, in_progress, complete, failed
        valid_statuses = ["starting", "in_progress", "complete", "failed"]
        if v["status"] not in valid_statuses:
            raise ValueError(f"Invalid status '{v['status']}', must be one of: {valid_statuses}")
        return v


class WSToolEvent(WSEventBase):
    """
    Tool event: Tool execution result.
    Example: {"type": "tool", "timestamp": "...", "run_id": "...", "data": {"tool": "bash", "status": "success"}}
    """

    type: Literal["tool"] = "tool"
    data: Dict[str, Any] = Field(
        ...,
        description="Tool execution data with 'tool' and 'status' keys",
        examples=[
            {"tool": "bash", "status": "success", "output": "Command executed"},
            {"tool": "read_file", "status": "failed", "error": "File not found"},
        ],
    )

    @field_validator("data")
    @classmethod
    def validate_tool_data(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure 'tool' and 'status' keys exist."""
        if "tool" not in v:
            raise ValueError("Tool event data must contain 'tool' key")
        if "status" not in v:
            raise ValueError("Tool event data must contain 'status' key")
        return v


class WSVerificationItemEvent(WSEventBase):
    """
    Verification item event: Individual QA check result.
    Example: {"type": "verification_item", "timestamp": "...", "run_id": "...", "data": {"name": "tests", "passed": true}}
    """

    type: Literal["verification_item"] = "verification_item"
    data: Dict[str, Any] = Field(
        ...,
        description="Verification item data with 'name' and 'passed' keys",
        examples=[
            {"name": "tests", "passed": True, "message": "All tests passed"},
            {"name": "lint", "passed": False, "message": "3 errors found"},
        ],
    )

    @field_validator("data")
    @classmethod
    def validate_verification_item_data(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure 'name' and 'passed' keys exist."""
        if "name" not in v:
            raise ValueError("Verification item event data must contain 'name' key")
        if "passed" not in v:
            raise ValueError("Verification item event data must contain 'passed' key")
        if not isinstance(v["passed"], bool):
            raise ValueError("Verification item 'passed' must be boolean")
        return v


class WSCompleteEvent(WSEventBase):
    """
    Complete event: Terminal event indicating successful run completion.
    INVARIANT: Exactly ONE terminal event per run (complete OR error).
    Example: {"type": "complete", "timestamp": "...", "run_id": "...", "data": {"message": "Task completed"}}
    """

    type: Literal["complete"] = "complete"
    data: Dict[str, Any] = Field(
        default_factory=lambda: {"message": "Run completed successfully"},
        description="Completion data with optional 'message' key",
        examples=[
            {"message": "Task completed successfully", "result": "..."},
            {"message": "All phases passed"},
        ],
    )


class WSErrorEvent(WSEventBase):
    """
    Error event: Terminal event indicating run failure.
    INVARIANT: Exactly ONE terminal event per run (complete OR error).
    Example: {"type": "error", "timestamp": "...", "run_id": "...", "data": {"message": "Execution failed"}}
    """

    type: Literal["error"] = "error"
    data: Dict[str, Any] = Field(
        ...,
        description="Error data with 'message' key",
        examples=[
            {"message": "Execution failed", "error": "ValueError: Invalid input"},
            {"message": "Phase 'verify' failed", "phase": "verify"},
        ],
    )

    @field_validator("data")
    @classmethod
    def validate_error_data(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure 'message' key exists."""
        if "message" not in v:
            raise ValueError("Error event data must contain 'message' key")
        return v


class WSConversationCreatedEvent(WSEventBase):
    """
    Conversation created event: Sent at start of new conversation.
    Example: {"type": "conversation_created", "timestamp": "...", "run_id": "...", "data": {"conversation_id": "..."}}
    """

    type: Literal["conversation_created"] = "conversation_created"
    data: Dict[str, Any] = Field(
        ...,
        description="Conversation data with 'conversation_id' key",
        examples=[{"conversation_id": "conv-12345"}],
    )

    @field_validator("data")
    @classmethod
    def validate_conversation_data(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure 'conversation_id' key exists."""
        if "conversation_id" not in v:
            raise ValueError("Conversation created event data must contain 'conversation_id' key")
        return v


# ===== UNION TYPE FOR ALL EVENTS =====

WSEvent = Union[
    WSThinkingEvent,
    WSPhaseEvent,
    WSToolEvent,
    WSVerificationItemEvent,
    WSCompleteEvent,
    WSErrorEvent,
    WSConversationCreatedEvent,
]


# ===== TERMINAL EVENT TYPES =====

TERMINAL_EVENT_TYPES = {"complete", "error"}


def is_terminal_event(event_type: str) -> bool:
    """Check if event type is terminal (complete or error)."""
    return event_type in TERMINAL_EVENT_TYPES
