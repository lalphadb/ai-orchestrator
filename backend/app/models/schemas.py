"""
Pydantic schemas for request/response validation
"""

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import (BaseModel, BeforeValidator, ConfigDict, EmailStr, Field,
                      ValidationError, field_validator)
from typing_extensions import Annotated

# UUID fields from PostgreSQL need coercion to str for Pydantic v2
StrUUID = Annotated[str, BeforeValidator(lambda v: str(v) if v is not None else v)]

# ===== AUTH SCHEMAS =====


class UserCreate(BaseModel):
    """Création d'utilisateur"""

    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=6)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        """SECURITY: Validate username contains only safe characters"""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username can only contain letters, numbers, hyphens and underscores")
        # Check for path traversal attempts
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("Invalid characters in username")
        return v


class UserLogin(BaseModel):
    """Login utilisateur"""

    username: str
    password: str


class UserResponse(BaseModel):
    """Réponse utilisateur"""

    id: StrUUID
    username: str
    email: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Token JWT avec refresh token"""

    access_token: str
    refresh_token: Optional[str] = None  # Nouveau: pour refresh sans re-login
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


# ===== CONVERSATION SCHEMAS =====


class ConversationCreate(BaseModel):
    """Création de conversation"""

    title: Optional[str] = Field(default="Nouvelle conversation", max_length=200)
    model: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        """SECURITY: Sanitize conversation title"""
        if v is None:
            return v
        # Remove dangerous HTML/JS patterns
        dangerous_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"<iframe",
            r"onerror\s*=",
            r"onload\s*=",
        ]
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, v_lower, re.IGNORECASE):
                raise ValueError("Title contains potentially malicious content")
        return v


class MessageResponse(BaseModel):
    """Message dans une conversation"""

    id: int
    role: str
    content: str
    model: Optional[str] = None
    tools_used: Optional[List[str]] = None
    thinking: Optional[str] = None
    created_at: datetime

    @field_validator("tools_used", mode="before")
    @classmethod
    def parse_tools_used(cls, v):
        """Deserialize tools_used if it's a JSON string"""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if parsed else None
            except (json.JSONDecodeError, ValueError):
                return None
        return v

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    """Réponse conversation"""

    id: StrUUID
    title: str
    model: Optional[str] = None
    messages: List[MessageResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    """Création de message"""

    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


# ===== CHAT SCHEMAS =====


class ChatRequest(BaseModel):
    """Requête de chat"""

    message: str = Field(..., min_length=1, max_length=50000)
    conversation_id: Optional[str] = None
    model: Optional[str] = None
    stream: bool = False
    use_tools: bool = True

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        """SECURITY: Basic XSS prevention - reject obvious script injection"""
        dangerous_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"onerror\s*=",
            r"onload\s*=",
            r"onclick\s*=",
            r"<iframe",
        ]
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, v_lower, re.IGNORECASE):
                raise ValueError("Message contains potentially malicious content")
        return v

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, v):
        """SECURITY: Validate conversation ID format"""
        if v is None:
            return v
        # Check for path traversal
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("Invalid conversation ID format")
        # Validate UUID-like format (alphanumeric and hyphens only)
        if not re.match(r"^[a-zA-Z0-9-]+$", v):
            raise ValueError("Invalid conversation ID format")
        return v


class ToolExecution(BaseModel):
    """Exécution d'un outil"""

    tool: str
    input: Dict[str, Any]
    output: Any
    duration_ms: int


class ChatResponse(BaseModel):
    """Réponse de chat"""

    response: str
    conversation_id: StrUUID
    model_used: str
    tools_used: List[ToolExecution] = []
    iterations: int = 0
    thinking: Optional[str] = None
    duration_ms: int


# ===== TOOL SCHEMAS =====


class ToolInfo(BaseModel):
    """Information sur un outil"""

    id: str
    name: str
    description: Optional[str] = None
    category: str
    enabled: bool
    usage_count: int = 0
    parameters: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class ToolListResponse(BaseModel):
    """Liste des outils"""

    tools: List[ToolInfo]
    total: int
    categories: List[str]


# ===== SYSTEM SCHEMAS =====


class SystemStats(BaseModel):
    """Statistiques système"""

    version: str
    uptime_seconds: float
    total_conversations: int
    total_messages: int
    total_tools: int
    active_model: str
    ollama_status: str
    memory_usage_mb: float
    cpu_percent: float


class ModelInfo(BaseModel):
    """Information sur un modèle"""

    name: str
    size: Optional[int] = None
    modified_at: Optional[datetime] = None
    available: bool = True


class ModelsResponse(BaseModel):
    """Liste des modèles"""

    models: List[ModelInfo]
    default_model: str


# ===== WEBSOCKET SCHEMAS =====


class WSMessage(BaseModel):
    """Message WebSocket"""

    type: str  # thinking, tool, chunk, complete, error
    data: Any
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
