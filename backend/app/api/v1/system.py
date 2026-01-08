"""
System routes - Status, stats, models
"""
import time
import psutil
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db, Conversation, Message
from app.core.config import settings
from app.services.ollama.client import ollama_client
from app.services.react_engine.tools import BUILTIN_TOOLS
from app.models import SystemStats, ModelsResponse, ModelInfo

router = APIRouter(prefix="/system")

# Startup time
_start_time = time.time()


@router.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
    }


@router.get("/stats", response_model=SystemStats)
async def get_stats(db: Session = Depends(get_db)):
    """Statistiques système"""
    
    # Database counts
    total_conversations = db.query(Conversation).count()
    total_messages = db.query(Message).count()
    
    # Ollama status
    ollama_ok = await ollama_client.health_check()
    
    # Process info
    process = psutil.Process()
    memory_mb = process.memory_info().rss / (1024 * 1024)
    
    return SystemStats(
        version=settings.APP_VERSION,
        uptime_seconds=time.time() - _start_time,
        total_conversations=total_conversations,
        total_messages=total_messages,
        total_tools=len(BUILTIN_TOOLS.tools),
        active_model=settings.DEFAULT_MODEL,
        ollama_status="connected" if ollama_ok else "disconnected",
        memory_usage_mb=round(memory_mb, 2),
        cpu_percent=psutil.cpu_percent(),
    )


@router.get("/models", response_model=ModelsResponse)
async def get_models():
    """Liste des modèles disponibles"""
    
    models = await ollama_client.list_models()
    
    model_list = [
        ModelInfo(
            name=m.get("name", "unknown"),
            size=m.get("size"),
            modified_at=m.get("modified_at"),
            available=True
        )
        for m in models
    ]
    
    # Ajouter les modèles configurés s'ils ne sont pas dans la liste
    existing_names = {m.name for m in model_list}
    for model_name in settings.AVAILABLE_MODELS:
        if model_name not in existing_names:
            model_list.append(ModelInfo(
                name=model_name,
                available=False
            ))
    
    return ModelsResponse(
        models=model_list,
        default_model=settings.DEFAULT_MODEL
    )
