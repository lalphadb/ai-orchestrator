"""
API Endpoints pour le système d'apprentissage.

Endpoints:
- POST /feedback : Envoyer un feedback
- GET /feedback/stats : Statistiques de feedback
- GET /learning/stats : Statistiques mémoire d'apprentissage
- GET /learning/patterns : Patterns détectés
- GET /learning/improvements : Priorités d'amélioration
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (get_admin_user, get_current_user,
                               get_current_user_optional)
from app.services.learning import (FeedbackType, PerformanceEvaluator,
                                   get_feedback_collector, get_learning_memory)

router = APIRouter(prefix="/learning", tags=["learning"])


# ==================== SCHEMAS ====================


class FeedbackTypeEnum(str, Enum):
    positive = "positive"
    negative = "negative"
    correction = "correction"


class FeedbackRequest(BaseModel):
    """Requête de feedback."""

    message_id: str = Field(..., description="ID du message évalué")
    conversation_id: str = Field(..., description="ID de la conversation")
    feedback_type: FeedbackTypeEnum = Field(..., description="Type de feedback")
    query: str = Field(..., description="Question originale")
    response: str = Field(..., description="Réponse évaluée")
    correction: Optional[str] = Field(None, description="Correction fournie")
    comment: Optional[str] = Field(None, description="Commentaire optionnel")
    tools_used: Optional[List[str]] = Field(None, description="Outils utilisés")


class FeedbackResponse(BaseModel):
    """Réponse après enregistrement du feedback."""

    success: bool
    feedback_id: str
    message: str


class LearningStatsResponse(BaseModel):
    """Statistiques de la mémoire d'apprentissage."""

    status: str
    experiences_count: int = 0
    patterns_count: int = 0
    corrections_count: int = 0
    user_contexts_count: int = 0


class FeedbackStatsResponse(BaseModel):
    """Statistiques de feedback."""

    period_hours: int
    total: int
    positive: int
    negative: int
    corrections: int
    positive_rate: float
    negative_rate: float


# ==================== ENDPOINTS ====================


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional),
):
    """
    Soumet un feedback sur une réponse.

    - **positive**: La réponse était utile 👍
    - **negative**: La réponse n'était pas utile 👎
    - **correction**: Fourni une correction
    - **regenerate**: Demande de régénération

    Note: L'authentification est optionnelle. Les feedbacks anonymes sont acceptés.
    """
    import logging

    logger = logging.getLogger(__name__)
    logger.info(
        f"📥 Feedback reçu: type={request.feedback_type}, message_id={request.message_id}, conversation_id={request.conversation_id}"
    )

    collector = get_feedback_collector()
    memory = get_learning_memory()

    # Mapper le type de feedback
    fb_type_map = {
        "positive": FeedbackType.POSITIVE,
        "negative": FeedbackType.NEGATIVE,
        "correction": FeedbackType.CORRECTION,
    }

    feedback_type = fb_type_map.get(request.feedback_type.value)

    # Déterminer l'user_id (authentifié ou anonyme)
    user_id = current_user.get("sub") if current_user else "anonymous"

    # Enregistrer le feedback (utiliser add_feedback au lieu de record_feedback)
    feedback = collector.add_feedback(
        db=db,
        message_id=int(request.message_id) if request.message_id.isdigit() else 0,
        conversation_id=request.conversation_id,
        user_id=user_id,
        feedback_type=feedback_type,
        query=request.query,
        response=request.response,
        tools_used=request.tools_used or [],
        corrected_response=request.correction,
        reason=request.comment,
    )

    # Si correction fournie, stocker dans la mémoire
    if request.correction and feedback_type == FeedbackType.CORRECTION:
        memory.store_correction(
            error_type="user_correction",
            error_message=f"Response not satisfactory for: {request.query[:100]}",
            failed_approach=request.response[:500],
            successful_correction=request.correction,
            context=request.comment or "",
        )

    # Si positif, améliorer le score de l'expérience
    if feedback_type == FeedbackType.POSITIVE:
        # Note: Ici on pourrait chercher l'experience_id correspondant
        pass

    return FeedbackResponse(
        success=True,
        feedback_id=str(feedback.message_id),
        message=f"Feedback {request.feedback_type.value} enregistré. Merci!",
    )


@router.get("/feedback/stats", response_model=FeedbackStatsResponse)
async def get_feedback_stats(
    hours: int = 24, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    """
    Récupère les statistiques de feedback.

    - **hours**: Période en heures (défaut: 24)
    """
    collector = get_feedback_collector()
    stats = collector.get_feedback_stats(db=db, hours=hours)

    return FeedbackStatsResponse(**stats)


@router.get("/stats", response_model=LearningStatsResponse)
async def get_learning_stats(current_user: dict = Depends(get_current_user)):
    """
    Récupère les statistiques de la mémoire d'apprentissage.
    """
    memory = get_learning_memory()
    stats = memory.get_stats()

    return LearningStatsResponse(**stats)


@router.get("/patterns")
async def get_learning_patterns(
    query: Optional[str] = None, limit: int = 10, current_user: dict = Depends(get_current_user)
):
    """
    Récupère les patterns de résolution appris.

    - **query**: Rechercher des patterns pertinents pour cette requête
    - **limit**: Nombre maximum de résultats
    """
    memory = get_learning_memory()

    if query:
        patterns = memory.get_relevant_patterns(query, n_results=limit)
    else:
        # Retourner les patterns les plus utilisés
        patterns = []  # TODO: Implémenter get_top_patterns

    return {"patterns": patterns, "count": len(patterns)}


@router.get("/experiences")
async def get_similar_experiences(
    query: str,
    limit: int = 5,
    success_only: bool = True,
    current_user: dict = Depends(get_current_user),
):
    """
    Recherche des expériences similaires.

    - **query**: Requête de recherche
    - **limit**: Nombre maximum de résultats
    - **success_only**: Ne retourner que les succès
    """
    memory = get_learning_memory()

    experiences = memory.get_similar_experiences(
        query=query, n_results=limit, success_only=success_only
    )

    return {"experiences": experiences, "count": len(experiences)}


@router.get("/improvements")
async def get_improvement_priorities(
    db: Session = Depends(get_db), current_user: dict = Depends(get_admin_user)
):
    """
    [Admin] Récupère les priorités d'amélioration basées sur les feedbacks.
    """
    collector = get_feedback_collector()

    priorities = collector.get_improvement_priorities(db=db)

    return {
        "priorities": priorities,
        "stats": collector.get_feedback_stats(db=db, hours=168),  # 7 jours
    }


@router.get("/export/training")
async def export_training_data(
    format: str = "jsonl",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_admin_user),
):
    """
    [Admin] Exporte les données pour le fine-tuning.

    - **format**: jsonl ou json
    """
    collector = get_feedback_collector()

    data = collector.export_for_finetuning(db=db, format=format)
    corrections = collector.get_corrections_for_training(db=db)

    return {"training_data": data, "corrections_count": len(corrections), "format": format}


@router.post("/preference")
async def set_user_preference(
    preference_type: str, preference_value: str, current_user: dict = Depends(get_current_user)
):
    """
    Enregistre une préférence utilisateur.

    - **preference_type**: Type de préférence (ex: "verbose_output", "coding_style")
    - **preference_value**: Valeur de la préférence
    """
    memory = get_learning_memory()
    user_id = current_user.get("user_id", "anonymous")

    memory.store_user_preference(
        user_id=user_id, preference_type=preference_type, preference_value=preference_value
    )

    return {"success": True, "message": f"Préférence '{preference_type}' enregistrée"}


@router.get("/context")
async def get_user_context(current_user: dict = Depends(get_current_user)):
    """
    Récupère le contexte utilisateur stocké.
    """
    memory = get_learning_memory()
    user_id = current_user.get("user_id", "anonymous")

    context = memory.get_user_context(user_id)

    return {"user_id": user_id, "context": context}
