"""
FeedbackCollector - Collecte et traitement du feedback utilisateur

Gère:
- Feedback positif/négatif sur les réponses
- Persistence en base de données SQLite
- Analyse des tendances
- Mise à jour des scores d'apprentissage
- Export des données pour fine-tuning
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.database import Feedback as FeedbackModel
from app.core.database import get_db_session
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """Types de feedback."""

    POSITIVE = "positive"  # 👍
    NEGATIVE = "negative"  # 👎
    CORRECTION = "correction"  # Correction fournie par l'utilisateur


@dataclass
class Feedback:
    """Structure d'un feedback (pour compatibilité API)."""

    message_id: str
    conversation_id: str
    feedback_type: FeedbackType
    timestamp: str
    query: str
    response: str
    tools_used: Optional[List[str]] = None
    corrected_response: Optional[str] = None
    reason: Optional[str] = None


class FeedbackCollector:
    """Collecteur et analyseur de feedback avec persistence DB."""

    def __init__(self):
        """Initialise le collecteur."""
        pass

    def add_feedback(
        self,
        db: Session,
        message_id: int,
        conversation_id: str,
        user_id: str,
        feedback_type: FeedbackType,
        query: str,
        response: str,
        tools_used: List[Dict[str, Any]],
        corrected_response: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Feedback:
        """
        Enregistre un feedback en base de données.

        Args:
            db: Session base de données
            message_id: ID du message évalué
            conversation_id: ID de la conversation
            user_id: ID de l'utilisateur
            feedback_type: Type de feedback
            query: Question originale
            response: Réponse évaluée
            tools_used: Outils utilisés
            corrected_response: Correction fournie (optionnel)
            reason: Raison du feedback négatif (optionnel)

        Returns:
            Feedback enregistré
        """
        # Créer feedback DB
        feedback_db = FeedbackModel(
            message_id=message_id,
            conversation_id=conversation_id,
            user_id=user_id,
            feedback_type=feedback_type.value,
            query=query,
            response=response,
            corrected_response=corrected_response,
            tools_used=json.dumps(tools_used) if tools_used else None,
            reason=reason,
        )

        db.add(feedback_db)
        db.commit()
        db.refresh(feedback_db)

        logger.info(f"Feedback {feedback_type.value} enregistré pour message {message_id}")

        # Retourner objet Feedback pour compatibilité
        return Feedback(
            message_id=str(message_id),
            conversation_id=conversation_id,
            feedback_type=feedback_type,
            timestamp=feedback_db.created_at.isoformat(),
            query=query,
            response=response,
            tools_used=tools_used,
            corrected_response=corrected_response,
            reason=reason,
        )

    def get_feedback_stats(
        self, db: Session, user_id: Optional[str] = None, hours: int = 24
    ) -> Dict[str, Any]:
        """
        Retourne les statistiques de feedback depuis la DB.

        Args:
            db: Session base de données
            user_id: Filtrer par utilisateur (optionnel)
            hours: Période en heures

        Returns:
            Statistiques détaillées
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = db.query(FeedbackModel)

        if user_id:
            query = query.filter(FeedbackModel.user_id == user_id)

        # Filtrer par période
        query = query.filter(FeedbackModel.created_at >= cutoff)

        feedbacks = query.all()

        # Calculer stats
        total = len(feedbacks)
        positive = len([f for f in feedbacks if f.feedback_type == "positive"])
        negative = len([f for f in feedbacks if f.feedback_type == "negative"])
        corrections = len([f for f in feedbacks if f.feedback_type == "correction"])

        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "corrections": corrections,
            "period_hours": hours,
            "positive_rate": positive / total if total > 0 else 0,
            "negative_rate": negative / total if total > 0 else 0,
        }

    def get_feedback_for_message(self, db: Session, message_id: int) -> List[FeedbackModel]:
        """Récupère tous les feedbacks pour un message depuis la DB."""
        return db.query(FeedbackModel).filter(FeedbackModel.message_id == message_id).all()

    def get_corrections_for_training(self, db: Session, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère les corrections pour le fine-tuning depuis la DB.

        Args:
            db: Session base de données
            limit: Nombre maximum de corrections

        Returns:
            Liste de paires (mauvaise réponse, correction)
        """
        corrections_db = (
            db.query(FeedbackModel)
            .filter(
                FeedbackModel.feedback_type == "correction",
                FeedbackModel.corrected_response.isnot(None),
            )
            .order_by(FeedbackModel.created_at.desc())
            .limit(limit)
            .all()
        )

        corrections = []
        for f in corrections_db:
            tools = json.loads(f.tools_used) if f.tools_used else []
            corrections.append(
                {
                    "query": f.query,
                    "bad_response": f.response,
                    "good_response": f.corrected_response,
                    "tools_used": tools,
                    "timestamp": f.created_at.isoformat(),
                }
            )

        return corrections

    def export_for_finetuning(self, db: Session, format: str = "jsonl") -> str:
        """
        Exporte les données pour fine-tuning depuis la DB.

        Args:
            db: Session base de données
            format: Format d'export (jsonl, json)

        Returns:
            Données exportées en string
        """
        # Collecter les données positives et corrections
        training_data = []

        # Feedbacks positifs = bons exemples
        positive_feedbacks = (
            db.query(FeedbackModel).filter(FeedbackModel.feedback_type == "positive").all()
        )

        for f in positive_feedbacks:
            training_data.append(
                {
                    "messages": [
                        {"role": "user", "content": f.query},
                        {"role": "assistant", "content": f.response},
                    ],
                    "source": "positive_feedback",
                }
            )

        # Corrections = meilleurs exemples
        corrections = (
            db.query(FeedbackModel)
            .filter(
                FeedbackModel.feedback_type == "correction",
                FeedbackModel.corrected_response.isnot(None),
            )
            .all()
        )

        for f in corrections:
            training_data.append(
                {
                    "messages": [
                        {"role": "user", "content": f.query},
                        {"role": "assistant", "content": f.corrected_response},
                    ],
                    "source": "user_correction",
                }
            )

        if format == "jsonl":
            return "\n".join(json.dumps(d) for d in training_data)
        else:
            return json.dumps(training_data, indent=2)

    def get_improvement_priorities(self, db: Session) -> List[Dict[str, Any]]:
        """
        Identifie les priorités d'amélioration depuis la DB.

        Args:
            db: Session base de données

        Returns:
            Liste triée des priorités
        """
        priorities = []

        # Analyser les feedbacks négatifs et corrections récents
        recent_negative = (
            db.query(FeedbackModel)
            .filter(
                FeedbackModel.feedback_type.in_(["negative", "correction"]),
                FeedbackModel.created_at >= datetime.now(timezone.utc) - timedelta(days=7),
            )
            .all()
        )

        # Grouper par outils utilisés
        tool_failures = {}
        for f in recent_negative:
            if f.tools_used:
                tools = json.loads(f.tools_used)
                for tool in tools:
                    tool_name = tool.get("name") if isinstance(tool, dict) else tool
                    tool_failures[tool_name] = tool_failures.get(tool_name, 0) + 1

        # Ajouter aux priorités
        for tool, count in sorted(tool_failures.items(), key=lambda x: x[1], reverse=True)[:5]:
            if count >= 2:
                priorities.append(
                    {
                        "type": "tool",
                        "priority": "high" if count >= 5 else "medium",
                        "description": f"Outil problématique: {tool}",
                        "failure_count": count,
                        "action": "Vérifier la configuration et l'utilisation de cet outil",
                    }
                )

        return priorities


# Instance singleton
_feedback_collector: Optional[FeedbackCollector] = None


def get_feedback_collector() -> FeedbackCollector:
    """Retourne l'instance singleton."""
    global _feedback_collector
    if _feedback_collector is None:
        _feedback_collector = FeedbackCollector()
    return _feedback_collector
