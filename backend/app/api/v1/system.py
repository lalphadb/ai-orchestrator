"""
System routes - Status, stats, models
"""

import time

import psutil
from app.core.config import settings
from app.core.database import Conversation, Message, get_db
from app.core.security import get_current_user, get_current_user_optional
from app.models import ModelInfo, ModelsResponse, SystemStats
from app.services.ollama.categorizer import CATEGORY_INFO, categorize_models
from app.services.ollama.client import ollama_client
from app.services.react_engine.tools import BUILTIN_TOOLS
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/system")

# Startup time
_start_time = time.time()


@router.get("/health")
async def health(
    detailed: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional),
):
    """
    Health check endpoint.

    Args:
        detailed: Si False (défaut), retourne check rapide sans dépendances.
                  Si True, vérifie toutes les dépendances (requiert authentification).

    Returns:
        200 si healthy, 503 si degraded (mode detailed seulement)
    """
    # Mode rapide (défaut) — pas d'auth requise
    if not detailed:
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
        }

    # Mode détaillé requiert authentification
    if not current_user:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for detailed health check",
        )

    # Mode détaillé - Vérifie toutes les dépendances
    import os
    import shutil
    from datetime import datetime, timezone

    from fastapi import HTTPException

    checks = {
        "api": {"status": "ok", "message": "API responding"},
        "database": {"status": "unknown", "details": {}},
        "ollama": {"status": "unknown", "details": {}},
        "chromadb": {"status": "unknown", "details": {}},
        "workspace": {"status": "unknown", "details": {}},
    }

    all_ok = True

    # 1. Database check (SQLite)
    try:
        from sqlalchemy import text

        # Test connexion
        db.execute(text("SELECT 1"))

        # Compter entités
        from app.core.database import User

        user_count = db.query(User).count()
        conv_count = db.query(Conversation).count()
        msg_count = db.query(Message).count()

        checks["database"] = {
            "status": "ok",
            "message": "Database accessible",
            "details": {
                "users": user_count,
                "conversations": conv_count,
                "messages": msg_count,
                "type": "SQLite",
            },
        }
    except Exception as e:
        checks["database"] = {
            "status": "error",
            "message": "Database check failed",
            "details": {},
        }
        all_ok = False

    # 2. Ollama check (avec détails modèles)
    try:
        ollama_ok = await ollama_client.health_check()
        if ollama_ok:
            # Récupérer modèles
            models = await ollama_client.list_models()
            model_names = [m.get("name") for m in models]

            # Vérifier si executor/verifier sont présents
            has_executor = any(settings.EXECUTOR_MODEL in name for name in model_names)
            has_verifier = any(settings.VERIFIER_MODEL in name for name in model_names)

            checks["ollama"] = {
                "status": "ok",
                "message": "Ollama accessible",
                "details": {
                    "url": settings.OLLAMA_URL,
                    "models_count": len(models),
                    "has_executor": has_executor,
                    "has_verifier": has_verifier,
                    "executor_model": settings.EXECUTOR_MODEL,
                    "verifier_model": settings.VERIFIER_MODEL,
                },
            }

            # Warning si modèles manquants (mais pas critique si Groq utilisé)
            if not has_executor or not has_verifier:
                checks["ollama"]["status"] = "warning"
                checks["ollama"]["message"] = "Ollama OK but some models unavailable locally"
                # Ne pas mettre all_ok=False car c'est peut-être intentionnel (Groq)
        else:
            checks["ollama"] = {
                "status": "error",
                "message": "Ollama unreachable",
                "details": {},
            }
            all_ok = False
    except Exception as e:
        checks["ollama"] = {
            "status": "error",
            "message": "Ollama check failed",
            "details": {},
        }
        all_ok = False

    # 3. ChromaDB check
    try:
        from app.services.learning.memory import LearningMemory

        memory = LearningMemory()

        # Vérifier connexion et compter feedbacks
        if memory.client and memory.experiences:
            feedback_count = memory.experiences.count()

            checks["chromadb"] = {
                "status": "ok",
                "message": "ChromaDB accessible",
                "details": {
                    "feedback_count": feedback_count,
                    "host": memory.chroma_host,
                    "port": memory.chroma_port,
                },
            }
        else:
            checks["chromadb"] = {
                "status": "warning",
                "message": "ChromaDB not initialized",
                "details": {},
            }
    except Exception as e:
        checks["chromadb"] = {
            "status": "error",
            "message": "ChromaDB check failed",
            "details": {},
        }
        # ChromaDB non-critique, ne met pas all_ok à False
        # all_ok = False

    # 4. Workspace check (permissions + espace disque)
    try:
        workspace_dir = settings.WORKSPACE_DIR

        # Vérifier existence et permissions
        exists = os.path.exists(workspace_dir)
        readable = os.access(workspace_dir, os.R_OK) if exists else False
        writable = os.access(workspace_dir, os.W_OK) if exists else False

        # Espace disque
        if exists:
            disk_usage = shutil.disk_usage(workspace_dir)
            free_gb = disk_usage.free / (1024**3)
            percent_used = (disk_usage.used / disk_usage.total) * 100

            workspace_status = "ok"
            workspace_message = "Workspace accessible"

            if percent_used > 90:
                workspace_status = "warning"
                workspace_message = f"Disk usage critical: {percent_used:.1f}%"
                all_ok = False
            elif not writable:
                workspace_status = "error"
                workspace_message = "Workspace not writable"
                all_ok = False

            checks["workspace"] = {
                "status": workspace_status,
                "message": workspace_message,
                "details": {
                    "path": workspace_dir,
                    "exists": exists,
                    "readable": readable,
                    "writable": writable,
                    "free_gb": round(free_gb, 2),
                    "used_percent": round(percent_used, 1),
                },
            }
        else:
            checks["workspace"] = {
                "status": "error",
                "message": "Workspace directory does not exist",
                "details": {"path": workspace_dir, "exists": False},
            }
            all_ok = False
    except Exception as e:
        checks["workspace"] = {
            "status": "error",
            "message": "Workspace check failed",
            "details": {},
        }
        all_ok = False

    # Return result
    result = {
        "status": "healthy" if all_ok else "degraded",
        "version": settings.APP_VERSION,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if not all_ok:
        raise HTTPException(status_code=503, detail=result)

    return result


# Backward compatibility
@router.get("/health/deep")
async def health_deep(db: Session = Depends(get_db)):
    """
    Alias pour /health?detailed=true (backward compatibility).
    Deprecated: Utiliser /health?detailed=true à la place.
    """
    return await health(detailed=True, db=db)


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


@router.get("/metrics")
async def get_metrics(db: Session = Depends(get_db)):
    """
    Alias pour /stats - Metrics système pour le monitoring.
    """
    return await get_stats(db=db)


@router.get("/models")
async def get_models():
    """Liste des modèles disponibles avec catégorisation"""

    models = await ollama_client.list_models()

    # Catégoriser les modèles
    categorized = categorize_models(models)

    # Flatten pour liste
    all_models = []
    for category, category_models in categorized.items():
        all_models.extend(category_models)

    model_list = [
        {
            "name": m.get("name", "unknown"),
            "size": m.get("size"),
            "modified_at": m.get("modified_at"),
            "available": True,
            "category": m.get("category"),
            "category_info": m.get("category_info"),
            "details": m.get("details"),
        }
        for m in all_models
    ]

    # Ajouter les modèles configurés s'ils ne sont pas dans la liste
    existing_names = {m["name"] for m in model_list}
    for model_name in settings.AVAILABLE_MODELS:
        if model_name not in existing_names:
            model_list.append(
                {
                    "name": model_name,
                    "available": False,
                    "category": "other",
                }
            )

    return {
        "models": model_list,
        "default_model": settings.DEFAULT_MODEL,
        "categories": categorized,
        "category_info": CATEGORY_INFO,
    }
