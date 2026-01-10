"""
AI Orchestrator v6.1 - Main Application
Architecture professionnelle avec FastAPI + Métriques Prometheus
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db
from app.core.metrics import router as metrics_router, init_metrics, OLLAMA_CONNECTED
from app.api import api_router

# Configuration logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)


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
    
    # Vérifier Ollama
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
        from app.services.learning import get_learning_memory
        from app.core.metrics import update_learning_metrics
        memory = get_learning_memory()
        stats = memory.get_stats()
        update_learning_metrics(stats)
        logger.info(f"✅ Mémoire d'apprentissage: {stats.get('experiences_count', 0)} expériences")
    except Exception as e:
        logger.warning(f"⚠️ Mémoire d'apprentissage non disponible: {e}")
    
    logger.info(f"🎯 Serveur prêt sur http://{settings.HOST}:{settings.PORT}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Arrêt de l'application")


# Application FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API d'orchestration IA avec moteur ReAct et auto-apprentissage",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
    )
