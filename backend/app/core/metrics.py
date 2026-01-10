"""
Métriques Prometheus pour l'AI Orchestrator
Expose les statistiques d'apprentissage et de performance
"""

from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter()

# ==================== MÉTRIQUES GÉNÉRALES ====================

# Requêtes
REQUESTS_TOTAL = Counter(
    'ai_orchestrator_requests_total',
    'Total des requêtes traitées',
    ['endpoint', 'method', 'status']
)

# Durée des requêtes
REQUEST_DURATION = Histogram(
    'ai_orchestrator_request_duration_seconds',
    'Durée des requêtes en secondes',
    ['endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# ==================== MÉTRIQUES REACT ====================

# Exécutions ReAct
REACT_EXECUTIONS = Counter(
    'ai_orchestrator_react_executions_total',
    'Total des exécutions ReAct',
    ['status', 'model']
)

# Itérations par exécution
REACT_ITERATIONS = Histogram(
    'ai_orchestrator_react_iterations',
    'Nombre d\'itérations par exécution ReAct',
    buckets=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
)

# Durée des exécutions ReAct
REACT_DURATION = Histogram(
    'ai_orchestrator_react_duration_seconds',
    'Durée des exécutions ReAct en secondes',
    ['model'],
    buckets=[1, 2, 5, 10, 20, 30, 60, 120]
)

# Outils utilisés
TOOLS_USED = Counter(
    'ai_orchestrator_tools_used_total',
    'Total des outils utilisés',
    ['tool_name', 'success']
)

# ==================== MÉTRIQUES APPRENTISSAGE ====================

# Expériences stockées
LEARNING_EXPERIENCES = Gauge(
    'ai_orchestrator_learning_experiences_total',
    'Nombre total d\'expériences stockées'
)

# Patterns détectés
LEARNING_PATTERNS = Gauge(
    'ai_orchestrator_learning_patterns_total',
    'Nombre total de patterns détectés'
)

# Corrections stockées
LEARNING_CORRECTIONS = Gauge(
    'ai_orchestrator_learning_corrections_total',
    'Nombre total de corrections stockées'
)

# Feedback reçu
FEEDBACK_RECEIVED = Counter(
    'ai_orchestrator_feedback_total',
    'Total des feedbacks reçus',
    ['type']  # positive, negative, correction
)

# Score moyen des évaluations
EVALUATION_SCORE = Gauge(
    'ai_orchestrator_evaluation_score_avg',
    'Score moyen des évaluations récentes',
    ['metric']  # overall, efficiency, speed, accuracy
)

# Taux de succès
SUCCESS_RATE = Gauge(
    'ai_orchestrator_success_rate',
    'Taux de succès des exécutions (0-1)'
)

# ==================== MÉTRIQUES SYSTÈME ====================

# Connexion ChromaDB
CHROMADB_CONNECTED = Gauge(
    'ai_orchestrator_chromadb_connected',
    'État de connexion à ChromaDB (1=connecté, 0=déconnecté)'
)

# Connexion Ollama
OLLAMA_CONNECTED = Gauge(
    'ai_orchestrator_ollama_connected',
    'État de connexion à Ollama (1=connecté, 0=déconnecté)'
)

# Info système
SYSTEM_INFO = Info(
    'ai_orchestrator',
    'Informations sur l\'AI Orchestrator'
)


# ==================== ENDPOINT METRICS ====================

@router.get("/metrics")
async def metrics():
    """Endpoint Prometheus pour les métriques."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ==================== HELPERS ====================

def update_learning_metrics(memory_stats: dict, evaluator_stats: dict = None):
    """Met à jour les métriques d'apprentissage."""
    if memory_stats.get('status') == 'connected':
        CHROMADB_CONNECTED.set(1)
        LEARNING_EXPERIENCES.set(memory_stats.get('experiences_count', 0))
        LEARNING_PATTERNS.set(memory_stats.get('patterns_count', 0))
        LEARNING_CORRECTIONS.set(memory_stats.get('corrections_count', 0))
    else:
        CHROMADB_CONNECTED.set(0)
    
    if evaluator_stats:
        EVALUATION_SCORE.labels(metric='overall').set(evaluator_stats.get('overall', 0))
        EVALUATION_SCORE.labels(metric='efficiency').set(evaluator_stats.get('efficiency', 0))
        EVALUATION_SCORE.labels(metric='speed').set(evaluator_stats.get('speed', 0))
        EVALUATION_SCORE.labels(metric='accuracy').set(evaluator_stats.get('accuracy', 0))
        SUCCESS_RATE.set(evaluator_stats.get('success_rate', 0))


def record_react_execution(success: bool, model: str, duration_s: float, iterations: int, tools: list):
    """Enregistre une exécution ReAct."""
    status = 'success' if success else 'failure'
    REACT_EXECUTIONS.labels(status=status, model=model).inc()
    REACT_DURATION.labels(model=model).observe(duration_s)
    REACT_ITERATIONS.observe(iterations)
    
    for tool in tools:
        TOOLS_USED.labels(tool_name=tool, success='true').inc()


def record_feedback(feedback_type: str):
    """Enregistre un feedback."""
    FEEDBACK_RECEIVED.labels(type=feedback_type).inc()


def init_metrics(version: str):
    """Initialise les métriques au démarrage."""
    SYSTEM_INFO.info({
        'version': version,
        'name': 'AI Orchestrator'
    })
