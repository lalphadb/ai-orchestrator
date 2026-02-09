"""
Métriques Prometheus pour l'AI Orchestrator
Expose les statistiques d'apprentissage et de performance
"""

from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import (CONTENT_TYPE_LATEST, Counter, Gauge, Histogram,
                               Info, generate_latest)

router = APIRouter()

# ==================== MÉTRIQUES GÉNÉRALES ====================

# Requêtes (nom personnalisé)
REQUESTS_TOTAL = Counter(
    "ai_orchestrator_requests_total",
    "Total des requêtes traitées",
    ["endpoint", "method", "status"],
)

# Requêtes (nom standard pour compatibilité dashboards)
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["endpoint", "method", "status_code"],
)

# Durée des requêtes (nom personnalisé)
REQUEST_DURATION = Histogram(
    "ai_orchestrator_request_duration_seconds",
    "Durée des requêtes en secondes",
    ["endpoint"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

# Durée des requêtes (nom standard pour compatibilité dashboards)
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["endpoint", "method"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ==================== MÉTRIQUES REACT ====================

# Exécutions ReAct
REACT_EXECUTIONS = Counter(
    "ai_orchestrator_react_executions_total", "Total des exécutions ReAct", ["status", "model"]
)

# Itérations par exécution
REACT_ITERATIONS = Histogram(
    "ai_orchestrator_react_iterations",
    "Nombre d'itérations par exécution ReAct",
    buckets=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
)

# Durée des exécutions ReAct
REACT_DURATION = Histogram(
    "ai_orchestrator_react_duration_seconds",
    "Durée des exécutions ReAct en secondes",
    ["model"],
    buckets=[1, 2, 5, 10, 20, 30, 60, 120],
)

# Outils utilisés
TOOLS_USED = Counter(
    "ai_orchestrator_tools_used_total", "Total des outils utilisés", ["tool_name", "success"]
)

# Latences par outil (PHASE 6)
TOOL_LATENCY = Histogram(
    "tool_execution_duration_seconds",
    "Durée d'exécution des outils en secondes",
    ["tool_name", "success"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

# Erreurs par type (PHASE 6)
TOOL_ERRORS = Counter(
    "tool_errors_total", "Erreurs d'exécution par type", ["tool_name", "error_code"]
)

# LLM Calls (PHASE 6)
LLM_CALLS = Counter("llm_calls_total", "Nombre d'appels LLM", ["model", "success"])

# LLM Tokens (PHASE 6)
LLM_TOKENS = Counter(
    "llm_tokens_total", "Tokens LLM utilisés", ["model", "type"]  # type: prompt ou completion
)

# Durée des phases workflow (PHASE 6)
WORKFLOW_PHASE_DURATION = Histogram(
    "workflow_phase_duration_seconds",
    "Durée des phases du workflow",
    ["phase"],  # SPEC, PLAN, EXECUTE, VERIFY, REPAIR, COMPLETE
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0],
)

# ==================== MÉTRIQUES APPRENTISSAGE ====================

# Expériences stockées
LEARNING_EXPERIENCES = Gauge(
    "ai_orchestrator_learning_experiences_total", "Nombre total d'expériences stockées"
)

# Patterns détectés
LEARNING_PATTERNS = Gauge(
    "ai_orchestrator_learning_patterns_total", "Nombre total de patterns détectés"
)

# Corrections stockées
LEARNING_CORRECTIONS = Gauge(
    "ai_orchestrator_learning_corrections_total", "Nombre total de corrections stockées"
)

# Feedback reçu
FEEDBACK_RECEIVED = Counter(
    "ai_orchestrator_feedback_total",
    "Total des feedbacks reçus",
    ["type"],  # positive, negative, correction
)

# Score moyen des évaluations
EVALUATION_SCORE = Gauge(
    "ai_orchestrator_evaluation_score_avg",
    "Score moyen des évaluations récentes",
    ["metric"],  # overall, efficiency, speed, accuracy
)

# Taux de succès
SUCCESS_RATE = Gauge("ai_orchestrator_success_rate", "Taux de succès des exécutions (0-1)")

# ==================== MÉTRIQUES SYSTÈME ====================

# Connexion Learning Memory (PostgreSQL + pgvector)
LEARNING_MEMORY_CONNECTED = Gauge(
    "ai_orchestrator_learning_memory_connected",
    "Learning memory connection state (1=connected, 0=disconnected)",
)

# Connexion Ollama
OLLAMA_CONNECTED = Gauge(
    "ai_orchestrator_ollama_connected", "État de connexion à Ollama (1=connecté, 0=déconnecté)"
)

# Info système
SYSTEM_INFO = Info("ai_orchestrator", "Informations sur l'AI Orchestrator")


# ==================== ENDPOINT METRICS ====================


@router.get("/metrics")
async def metrics():
    """Endpoint Prometheus pour les métriques."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ==================== HELPERS ====================


def update_learning_metrics(memory_stats: dict, evaluator_stats: dict = None):
    """Met à jour les métriques d'apprentissage."""
    if memory_stats.get("status") == "connected":
        LEARNING_MEMORY_CONNECTED.set(1)
        LEARNING_EXPERIENCES.set(memory_stats.get("experiences_count", 0))
        LEARNING_PATTERNS.set(memory_stats.get("patterns_count", 0))
        LEARNING_CORRECTIONS.set(memory_stats.get("corrections_count", 0))
    else:
        LEARNING_MEMORY_CONNECTED.set(0)

    if evaluator_stats:
        EVALUATION_SCORE.labels(metric="overall").set(evaluator_stats.get("overall", 0))
        EVALUATION_SCORE.labels(metric="efficiency").set(evaluator_stats.get("efficiency", 0))
        EVALUATION_SCORE.labels(metric="speed").set(evaluator_stats.get("speed", 0))
        EVALUATION_SCORE.labels(metric="accuracy").set(evaluator_stats.get("accuracy", 0))
        SUCCESS_RATE.set(evaluator_stats.get("success_rate", 0))


def record_react_execution(
    success: bool, model: str, duration_s: float, iterations: int, tools: list
):
    """Enregistre une exécution ReAct."""
    status = "success" if success else "failure"
    REACT_EXECUTIONS.labels(status=status, model=model).inc()
    REACT_DURATION.labels(model=model).observe(duration_s)
    REACT_ITERATIONS.observe(iterations)

    for tool in tools:
        TOOLS_USED.labels(tool_name=tool, success="true").inc()


def record_feedback(feedback_type: str):
    """Enregistre un feedback."""
    FEEDBACK_RECEIVED.labels(type=feedback_type).inc()


def init_metrics(version: str):
    """Initialise les métriques au démarrage."""
    SYSTEM_INFO.info({"version": version, "name": "AI Orchestrator"})


# ==================== HELPERS PHASE 6 ====================


def record_tool_execution(tool_name: str, duration_s: float, success: bool, error_code: str = None):
    """
    Enregistre l'exécution d'un outil avec latence et erreurs.

    Args:
        tool_name: Nom de l'outil
        duration_s: Durée d'exécution en secondes
        success: Si l'exécution a réussi
        error_code: Code d'erreur si échec (ex: E_FILE_NOT_FOUND)
    """
    # Enregistrer latence
    TOOL_LATENCY.labels(tool_name=tool_name, success=str(success).lower()).observe(duration_s)

    # Enregistrer erreur si échec
    if not success and error_code:
        TOOL_ERRORS.labels(tool_name=tool_name, error_code=error_code).inc()


def record_llm_call(model: str, success: bool, prompt_tokens: int = 0, completion_tokens: int = 0):
    """
    Enregistre un appel LLM avec tokens utilisés.

    Args:
        model: Nom du modèle LLM
        success: Si l'appel a réussi
        prompt_tokens: Tokens du prompt
        completion_tokens: Tokens de la complétion
    """
    LLM_CALLS.labels(model=model, success=str(success).lower()).inc()

    if prompt_tokens > 0:
        LLM_TOKENS.labels(model=model, type="prompt").inc(prompt_tokens)

    if completion_tokens > 0:
        LLM_TOKENS.labels(model=model, type="completion").inc(completion_tokens)


def record_workflow_phase(phase: str, duration_s: float):
    """
    Enregistre la durée d'une phase du workflow.

    Args:
        phase: Nom de la phase (SPEC, PLAN, EXECUTE, VERIFY, REPAIR, COMPLETE)
        duration_s: Durée en secondes
    """
    WORKFLOW_PHASE_DURATION.labels(phase=phase).observe(duration_s)
