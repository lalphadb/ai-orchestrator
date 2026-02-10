"""
AI Orchestrator v8 - Main Application
Architecture professionnelle avec FastAPI + Métriques Prometheus
Workflow Engine: Spec → Plan → Execute → Verify → Repair
"""

import logging
from contextlib import asynccontextmanager

from app.api import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.logging_config import setup_logging
from app.core.logging_filter import add_secret_filter_to_all_loggers
from app.core.metrics import OLLAMA_CONNECTED, init_metrics
from app.core.metrics import router as metrics_router
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Configuration logging structuré (v7.1)
setup_logging(level=settings.LOG_LEVEL, format_type=settings.LOG_FORMAT)
logger = logging.getLogger(__name__)

# SECURITY: Ajouter le filtre de secrets à tous les loggers
add_secret_filter_to_all_loggers()
logger.info("🔒 Filtre de secrets activé sur tous les loggers")

# Configuration rate limiting
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    # Startup
    logger.info(f"🚀 Démarrage {settings.APP_NAME} v{settings.APP_VERSION}")

    # Initialiser les métriques
    init_metrics(settings.APP_VERSION)
    logger.info("✅ Métriques Prometheus initialisées")

    # Initialiser la base de données
    init_db()
    logger.info("✅ Base de données initialisée")

    # Vérifier Ollama (skip en mode TESTING)
    if settings.TESTING:
        logger.info("🧪 Mode TESTING: skip vérification Ollama")
        OLLAMA_CONNECTED.set(0)
    else:
        from app.services.ollama.client import ollama_client

        ollama_ok = await ollama_client.health_check()
        if ollama_ok:
            logger.info("✅ Ollama connecté")
            OLLAMA_CONNECTED.set(1)
        else:
            logger.warning("⚠️ Ollama non disponible")
            OLLAMA_CONNECTED.set(0)

    # Afficher les outils disponibles
    from app.services.react_engine.tools import BUILTIN_TOOLS

    logger.info(f"✅ {len(BUILTIN_TOOLS.tools)} outils chargés")

    # Initialiser la mémoire d'apprentissage
    try:
        from app.core.metrics import update_learning_metrics
        from app.services.learning import get_learning_memory

        memory = get_learning_memory()
        stats = memory.get_stats()
        update_learning_metrics(stats)
        logger.info(f"✅ Mémoire d'apprentissage: {stats.get('experiences_count', 0)} expériences")
    except Exception as e:
        logger.warning(f"⚠️ Mémoire d'apprentissage non disponible: {e}")

    # Démarrer le scheduler (CRQ-P0-5)
    try:
        from app.core.scheduler import start_scheduler

        start_scheduler()
    except Exception as e:
        logger.warning(f"⚠️ Scheduler non démarré: {e}")

    logger.info(f"🎯 Serveur prêt sur http://{settings.HOST}:{settings.PORT}")

    yield

    # Shutdown
    logger.info("🛑 Arrêt de l'application")

    # Arrêter le scheduler (CRQ-P0-5)
    try:
        from app.core.scheduler import stop_scheduler

        stop_scheduler()
    except Exception as e:
        logger.warning(f"⚠️ Erreur arrêt scheduler: {e}")


# Application FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API d'orchestration IA avec moteur ReAct et auto-apprentissage",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Request Tracing & Performance Monitoring (v7.1)
from app.api.middleware import (PerformanceMonitoringMiddleware,
                                PrometheusMiddleware, RequestTracingMiddleware,
                                SecurityHeadersMiddleware)

app.add_middleware(RequestTracingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)  # Headers OWASP
app.add_middleware(PrometheusMiddleware)  # Métriques HTTP
app.add_middleware(PerformanceMonitoringMiddleware, threshold_ms=5000)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS
    + ([settings.CORS_DEV_ORIGIN] if settings.CORS_DEV_ORIGIN else []),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routes API
app.include_router(api_router)

# Inclure les métriques Prometheus (sans auth)
app.include_router(metrics_router)


# Route racine
@app.get("/")
async def root():
    """Racine de l'API"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/system/health",
        "metrics": "/metrics",
    }


# Health check (racine pour compatibilité)
@app.get("/health")
async def health():
    """Health check rapide"""
    return {"status": "healthy", "version": settings.APP_VERSION}


# Monter les fichiers statiques du frontend
try:
    app.mount("/app", StaticFiles(directory="static", html=True), name="static")
except Exception:
    logger.warning("⚠️ Dossier static non trouvé")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS,
        ws_ping_interval=20,
        ws_ping_timeout=20,
    )
