"""
Pydantic schemas for request/response validation
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr


# ===== AUTH SCHEMAS =====

class UserCreate(BaseModel):
    """Création d'utilisateur"""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """Login utilisateur"""
    username: str
    password: str


class UserResponse(BaseModel):
    """Réponse utilisateur"""
    id: str
    username: str
    email: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token JWT"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


# ===== CONVERSATION SCHEMAS =====

class ConversationCreate(BaseModel):
    """Création de conversation"""
    title: Optional[str] = "Nouvelle conversation"
    model: Optional[str] = None


class MessageResponse(BaseModel):
    """Message dans une conversation"""
    id: int
    role: str
    content: str
    model: Optional[str] = None
    tools_used: Optional[List[str]] = None
    thinking: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Réponse conversation"""
    id: str
    title: str
    model: Optional[str] = None
    messages: List[MessageResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """Création de message"""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


# ===== CHAT SCHEMAS =====

class ChatRequest(BaseModel):
    """Requête de chat"""
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    model: Optional[str] = None
    stream: bool = False
    use_tools: bool = True


class ToolExecution(BaseModel):
    """Exécution d'un outil"""
    tool: str
    input: Dict[str, Any]
    output: Any
    duration_ms: int


class ChatResponse(BaseModel):
    """Réponse de chat"""
    response: str
    conversation_id: str
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

    class Config:
        from_attributes = True


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
    timestamp: datetime = Field(default_factory=datetime.utcnow)
