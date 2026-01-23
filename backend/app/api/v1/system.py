"""
System routes - Status, stats, models
"""

import time

import psutil
from app.core.config import settings
from app.core.database import Conversation, Message, get_db
from app.models import ModelInfo, ModelsResponse, SystemStats
from app.services.ollama.client import ollama_client
from app.services.react_engine.tools import BUILTIN_TOOLS
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/system")

# Startup time
_start_time = time.time()


@router.get("/health")
async def health():
    """Health check rapide (sans dépendances)"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
    }


@router.get("/health/deep")
async def health_deep(db: Session = Depends(get_db)):
    """
    Deep health check - Vérifie toutes les dépendances critiques.
    Utilisé pour les alertes et monitoring.

    Retourne 200 si tout est OK, 503 si un composant est down.
    """
    import shutil

    from fastapi import HTTPException

    checks = {
        "api": {"status": "ok", "message": "API responding"},
        "database": {"status": "unknown", "message": ""},
        "ollama": {"status": "unknown", "message": ""},
        "disk_space": {"status": "unknown", "message": ""},
        "workspace": {"status": "unknown", "message": ""},
    }

    all_ok = True

    # 1. Database check
    try:
        from sqlalchemy import text

        db.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok", "message": "Database accessible"}
    except Exception as e:
        checks["database"] = {"status": "error", "message": f"Database error: {str(e)[:100]}"}
        all_ok = False

    # 2. Ollama check
    ollama_ok = await ollama_client.health_check()
    if ollama_ok:
        checks["ollama"] = {"status": "ok", "message": "Ollama accessible"}
    else:
        checks["ollama"] = {
            "status": "error",
            "message": f"Ollama unreachable at {settings.OLLAMA_URL}",
        }
        all_ok = False

    # 3. Disk space check (workspace)
    try:
        workspace_dir = settings.WORKSPACE_DIR
        disk_usage = shutil.disk_usage(workspace_dir)
        percent_used = (disk_usage.used / disk_usage.total) * 100

        if percent_used < 90:
            checks["disk_space"] = {
                "status": "ok",
                "message": f"{percent_used:.1f}% used",
                "percent": round(percent_used, 1),
            }
        else:
            checks["disk_space"] = {
                "status": "warning",
                "message": f"{percent_used:.1f}% used - CRITICAL",
                "percent": round(percent_used, 1),
            }
            all_ok = False
    except Exception as e:
        checks["disk_space"] = {"status": "error", "message": f"Cannot check disk: {str(e)[:100]}"}

    # 4. Workspace directory check
    import os

    if os.path.exists(settings.WORKSPACE_DIR) and os.access(settings.WORKSPACE_DIR, os.W_OK):
        checks["workspace"] = {
            "status": "ok",
            "message": f"Workspace accessible: {settings.WORKSPACE_DIR}",
        }
    else:
        checks["workspace"] = {
            "status": "error",
            "message": f"Workspace not accessible: {settings.WORKSPACE_DIR}",
        }
        all_ok = False

    # Return result
    result = {
        "status": "healthy" if all_ok else "degraded",
        "version": settings.APP_VERSION,
        "checks": checks,
        "timestamp": time.time(),
    }

    if not all_ok:
        raise HTTPException(status_code=503, detail=result)

    return result


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
            available=True,
        )
        for m in models
    ]

    # Ajouter les modèles configurés s'ils ne sont pas dans la liste
    existing_names = {m.name for m in model_list}
    for model_name in settings.AVAILABLE_MODELS:
        if model_name not in existing_names:
            model_list.append(ModelInfo(name=model_name, available=False))

    return ModelsResponse(models=model_list, default_model=settings.DEFAULT_MODEL)
