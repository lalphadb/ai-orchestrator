"""Models module - Export all schemas"""

from .schemas import (ChatRequest,  # Auth; Conversations; Chat; Tools; System
                      ChatResponse, ConversationCreate, ConversationResponse,
                      MessageCreate, MessageResponse, ModelInfo,
                      ModelsResponse, SystemStats, Token, ToolExecution,
                      ToolInfo, ToolListResponse, UserCreate, UserLogin,
                      UserResponse, WSMessage)
from .ws_events import (WSCompleteEvent,  # WebSocket v8 Events
                        WSConversationCreatedEvent, WSErrorEvent, WSEvent,
                        WSEventBase, WSPhaseEvent, WSThinkingEvent,
                        WSToolEvent, WSVerificationItemEvent,
                        is_terminal_event)

__all__ = [
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    "ConversationCreate",
    "ConversationResponse",
    "MessageCreate",
    "MessageResponse",
    "ChatRequest",
    "ChatResponse",
    "ToolExecution",
    "ToolInfo",
    "ToolListResponse",
    "SystemStats",
    "ModelInfo",
    "ModelsResponse",
    "WSMessage",
    # WebSocket v8 Events
    "WSEventBase",
    "WSThinkingEvent",
    "WSPhaseEvent",
    "WSToolEvent",
    "WSVerificationItemEvent",
    "WSCompleteEvent",
    "WSErrorEvent",
    "WSConversationCreatedEvent",
    "WSEvent",
    "is_terminal_event",
]
