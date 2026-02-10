"""
FeedbackCollector - Collecte et traitement du feedback utilisateur

Gere:
- Feedback positif/negatif sur les reponses
- Persistence en base de donnees PostgreSQL
- Analyse des tendances
- Mise a jour des scores d'apprentissage
- Export des donnees pour fine-tuning
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

    POSITIVE = "positive"
    NEGATIVE = "negative"
    CORRECTION = "correction"


@dataclass
class Feedback:
    """Structure d'un feedback (pour compatibilite API)."""

    message_id: str
    conversation_id: str
    feedback_type: FeedbackType
    timestamp: str
    query: str
    response: str
    tools_used: Optional[List[str]] = None
    corrected_response: Optional[str] = None
    reason: Optional[str] = None


def _parse_context(feedback_model: FeedbackModel) -> Dict[str, Any]:
    """Parse the context JSON field from a Feedback model."""
    if feedback_model.context:
        if isinstance(feedback_model.context, dict):
            return feedback_model.context
        try:
            return json.loads(feedback_model.context)
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


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
        Enregistre un feedback en base de donnees.
        """
        # Store all details in context JSON
        context = {
            "query": query,
            "response": response,
            "tools_used": tools_used,
        }
        if corrected_response:
            context["corrected_response"] = corrected_response
        if reason:
            context["reason"] = reason

        feedback_db = FeedbackModel(
            message_id=message_id,
            conversation_id=conversation_id,
            user_id=user_id,
            feedback_type=feedback_type.value,
            context=context,
        )

        db.add(feedback_db)
        db.commit()
        db.refresh(feedback_db)

        logger.info(f"Feedback {feedback_type.value} enregistre pour message {message_id}")

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
        """Retourne les statistiques de feedback."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = db.query(FeedbackModel)

        if user_id:
            query = query.filter(FeedbackModel.user_id == user_id)

        query = query.filter(FeedbackModel.created_at >= cutoff)
        feedbacks = query.all()

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
        """Recupere tous les feedbacks pour un message."""
        return db.query(FeedbackModel).filter(FeedbackModel.message_id == message_id).all()

    def get_corrections_for_training(self, db: Session, limit: int = 100) -> List[Dict[str, Any]]:
        """Recupere les corrections pour le fine-tuning."""
        corrections_db = (
            db.query(FeedbackModel)
            .filter(FeedbackModel.feedback_type == "correction")
            .order_by(FeedbackModel.created_at.desc())
            .limit(limit)
            .all()
        )

        corrections = []
        for f in corrections_db:
            ctx = _parse_context(f)
            if ctx.get("corrected_response"):
                corrections.append(
                    {
                        "query": ctx.get("query", ""),
                        "bad_response": ctx.get("response", ""),
                        "good_response": ctx["corrected_response"],
                        "tools_used": ctx.get("tools_used", []),
                        "timestamp": f.created_at.isoformat(),
                    }
                )

        return corrections

    def export_for_finetuning(self, db: Session, format: str = "jsonl") -> str:
        """Exporte les donnees pour fine-tuning."""
        training_data = []

        positive_feedbacks = (
            db.query(FeedbackModel).filter(FeedbackModel.feedback_type == "positive").all()
        )

        for f in positive_feedbacks:
            ctx = _parse_context(f)
            if ctx.get("query") and ctx.get("response"):
                training_data.append(
                    {
                        "messages": [
                            {"role": "user", "content": ctx["query"]},
                            {"role": "assistant", "content": ctx["response"]},
                        ],
                        "source": "positive_feedback",
                    }
                )

        corrections = (
            db.query(FeedbackModel).filter(FeedbackModel.feedback_type == "correction").all()
        )

        for f in corrections:
            ctx = _parse_context(f)
            if ctx.get("query") and ctx.get("corrected_response"):
                training_data.append(
                    {
                        "messages": [
                            {"role": "user", "content": ctx["query"]},
                            {"role": "assistant", "content": ctx["corrected_response"]},
                        ],
                        "source": "user_correction",
                    }
                )

        if format == "jsonl":
            return "\n".join(json.dumps(d) for d in training_data)
        else:
            return json.dumps(training_data, indent=2)

    def get_improvement_priorities(self, db: Session) -> List[Dict[str, Any]]:
        """Identifie les priorites d'amelioration."""
        priorities = []

        recent_negative = (
            db.query(FeedbackModel)
            .filter(
                FeedbackModel.feedback_type.in_(["negative", "correction"]),
                FeedbackModel.created_at >= datetime.now(timezone.utc) - timedelta(days=7),
            )
            .all()
        )

        tool_failures = {}
        for f in recent_negative:
            ctx = _parse_context(f)
            tools_used = ctx.get("tools_used", [])
            if tools_used:
                for tool in tools_used:
                    tool_name = tool.get("name") if isinstance(tool, dict) else tool
                    tool_failures[tool_name] = tool_failures.get(tool_name, 0) + 1

        for tool, count in sorted(tool_failures.items(), key=lambda x: x[1], reverse=True)[:5]:
            if count >= 2:
                priorities.append(
                    {
                        "type": "tool",
                        "priority": "high" if count >= 5 else "medium",
                        "description": f"Outil problematique: {tool}",
                        "failure_count": count,
                        "action": "Verifier la configuration et l'utilisation de cet outil",
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
