"""
FeedbackCollector - Collecte et traitement du feedback utilisateur

Gère:
- Feedback positif/négatif sur les réponses
- Analyse des tendances
- Mise à jour des scores d'apprentissage
- Export des données pour fine-tuning
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """Types de feedback."""
    POSITIVE = "positive"      # 👍
    NEGATIVE = "negative"      # 👎
    CORRECTION = "correction"  # Correction fournie par l'utilisateur
    REGENERATE = "regenerate"  # Demande de régénération


@dataclass
class Feedback:
    """Structure d'un feedback."""
    id: str
    message_id: str
    conversation_id: str
    user_id: str
    feedback_type: FeedbackType
    timestamp: str
    query: str
    response: str
    correction: Optional[str] = None
    comment: Optional[str] = None
    tools_used: Optional[List[str]] = None
    score_impact: float = 0.0


class FeedbackCollector:
    """Collecteur et analyseur de feedback."""
    
    def __init__(self):
        """Initialise le collecteur."""
        self.feedbacks: List[Feedback] = []
        self.feedback_by_message: Dict[str, List[Feedback]] = {}
        
    def record_feedback(
        self,
        message_id: str,
        conversation_id: str,
        user_id: str,
        feedback_type: FeedbackType,
        query: str,
        response: str,
        correction: Optional[str] = None,
        comment: Optional[str] = None,
        tools_used: Optional[List[str]] = None
    ) -> Feedback:
        """
        Enregistre un feedback utilisateur.
        
        Args:
            message_id: ID du message évalué
            conversation_id: ID de la conversation
            user_id: ID de l'utilisateur
            feedback_type: Type de feedback
            query: Question originale
            response: Réponse évaluée
            correction: Correction fournie (optionnel)
            comment: Commentaire libre (optionnel)
            tools_used: Outils utilisés (optionnel)
            
        Returns:
            Feedback enregistré
        """
        # Calculer l'impact sur le score
        score_impact = self._calculate_score_impact(feedback_type)
        
        feedback = Feedback(
            id=f"fb_{message_id}_{datetime.now().timestamp()}",
            message_id=message_id,
            conversation_id=conversation_id,
            user_id=user_id,
            feedback_type=feedback_type,
            timestamp=datetime.now().isoformat(),
            query=query,
            response=response,
            correction=correction,
            comment=comment,
            tools_used=tools_used,
            score_impact=score_impact
        )
        
        self.feedbacks.append(feedback)
        
        if message_id not in self.feedback_by_message:
            self.feedback_by_message[message_id] = []
        self.feedback_by_message[message_id].append(feedback)
        
        logger.info(f"Feedback enregistré: {feedback_type} pour message {message_id}")
        
        return feedback
    
    def _calculate_score_impact(self, feedback_type: FeedbackType) -> float:
        """Calcule l'impact du feedback sur le score."""
        impacts = {
            FeedbackType.POSITIVE: 0.1,
            FeedbackType.NEGATIVE: -0.15,
            FeedbackType.CORRECTION: -0.1,  # Négatif car nécessite correction
            FeedbackType.REGENERATE: -0.05  # Légèrement négatif
        }
        return impacts.get(feedback_type, 0.0)
    
    def get_feedback_for_message(self, message_id: str) -> List[Feedback]:
        """Récupère tous les feedbacks pour un message."""
        return self.feedback_by_message.get(message_id, [])
    
    def get_net_score(self, message_id: str) -> float:
        """Calcule le score net pour un message."""
        feedbacks = self.get_feedback_for_message(message_id)
        return sum(f.score_impact for f in feedbacks)
    
    def get_feedback_stats(
        self,
        hours: int = 24,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retourne les statistiques de feedback.
        
        Args:
            hours: Période en heures
            user_id: Filtrer par utilisateur (optionnel)
            
        Returns:
            Statistiques détaillées
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Filtrer les feedbacks récents
        recent = [
            f for f in self.feedbacks
            if datetime.fromisoformat(f.timestamp) > cutoff
            and (user_id is None or f.user_id == user_id)
        ]
        
        if not recent:
            return {
                "period_hours": hours,
                "total": 0,
                "by_type": {},
                "net_score": 0,
                "positive_rate": 0
            }
        
        # Compter par type
        by_type = {}
        for f in recent:
            t = f.feedback_type.value
            by_type[t] = by_type.get(t, 0) + 1
        
        # Calculer les métriques
        total = len(recent)
        positive = by_type.get(FeedbackType.POSITIVE.value, 0)
        negative = by_type.get(FeedbackType.NEGATIVE.value, 0)
        
        return {
            "period_hours": hours,
            "total": total,
            "by_type": by_type,
            "net_score": sum(f.score_impact for f in recent),
            "positive_rate": positive / total if total > 0 else 0,
            "negative_rate": negative / total if total > 0 else 0,
            "corrections_count": by_type.get(FeedbackType.CORRECTION.value, 0)
        }
    
    def get_problematic_patterns(
        self,
        min_negative: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Identifie les patterns problématiques.
        
        Args:
            min_negative: Minimum de feedbacks négatifs pour considérer
            
        Returns:
            Liste des patterns problématiques
        """
        # Grouper par type de query (approximatif)
        query_patterns = {}
        
        for f in self.feedbacks:
            if f.feedback_type in [FeedbackType.NEGATIVE, FeedbackType.CORRECTION]:
                # Extraire les premiers mots comme pattern
                words = f.query.lower().split()[:3]
                pattern = " ".join(words)
                
                if pattern not in query_patterns:
                    query_patterns[pattern] = {
                        "pattern": pattern,
                        "negative_count": 0,
                        "examples": [],
                        "tools_involved": set()
                    }
                
                query_patterns[pattern]["negative_count"] += 1
                if len(query_patterns[pattern]["examples"]) < 3:
                    query_patterns[pattern]["examples"].append({
                        "query": f.query,
                        "response": f.response[:200],
                        "correction": f.correction
                    })
                if f.tools_used:
                    query_patterns[pattern]["tools_involved"].update(f.tools_used)
        
        # Filtrer et trier
        problematic = [
            {**p, "tools_involved": list(p["tools_involved"])}
            for p in query_patterns.values()
            if p["negative_count"] >= min_negative
        ]
        
        return sorted(problematic, key=lambda x: x["negative_count"], reverse=True)
    
    def get_corrections_for_training(
        self,
        min_count: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Récupère les corrections pour le fine-tuning.
        
        Args:
            min_count: Minimum d'occurrences similaires
            
        Returns:
            Liste de paires (mauvaise réponse, correction)
        """
        corrections = []
        
        for f in self.feedbacks:
            if f.feedback_type == FeedbackType.CORRECTION and f.correction:
                corrections.append({
                    "query": f.query,
                    "bad_response": f.response,
                    "good_response": f.correction,
                    "tools_used": f.tools_used,
                    "timestamp": f.timestamp
                })
        
        return corrections
    
    def export_for_finetuning(
        self,
        format: str = "jsonl"
    ) -> str:
        """
        Exporte les données pour fine-tuning.
        
        Args:
            format: Format d'export (jsonl, json)
            
        Returns:
            Données exportées en string
        """
        # Collecter les données positives et corrections
        training_data = []
        
        # Feedbacks positifs = bons exemples
        for f in self.feedbacks:
            if f.feedback_type == FeedbackType.POSITIVE:
                training_data.append({
                    "messages": [
                        {"role": "user", "content": f.query},
                        {"role": "assistant", "content": f.response}
                    ],
                    "source": "positive_feedback"
                })
            
            # Corrections = meilleurs exemples
            elif f.feedback_type == FeedbackType.CORRECTION and f.correction:
                training_data.append({
                    "messages": [
                        {"role": "user", "content": f.query},
                        {"role": "assistant", "content": f.correction}
                    ],
                    "source": "user_correction"
                })
        
        if format == "jsonl":
            return "\n".join(json.dumps(d) for d in training_data)
        else:
            return json.dumps(training_data, indent=2)
    
    def get_improvement_priorities(self) -> List[Dict[str, Any]]:
        """
        Identifie les priorités d'amélioration.
        
        Returns:
            Liste triée des priorités
        """
        priorities = []
        
        # Analyser les patterns problématiques
        problematic = self.get_problematic_patterns(min_negative=2)
        for p in problematic[:5]:
            priorities.append({
                "type": "pattern",
                "priority": "high" if p["negative_count"] >= 5 else "medium",
                "description": f"Pattern problématique: '{p['pattern']}'",
                "negative_count": p["negative_count"],
                "tools_involved": p["tools_involved"],
                "action": "Analyser et améliorer le traitement de ce type de requête"
            })
        
        # Analyser les outils problématiques
        tool_failures = {}
        for f in self.feedbacks:
            if f.feedback_type in [FeedbackType.NEGATIVE, FeedbackType.CORRECTION]:
                for tool in (f.tools_used or []):
                    tool_failures[tool] = tool_failures.get(tool, 0) + 1
        
        for tool, count in sorted(tool_failures.items(), key=lambda x: x[1], reverse=True)[:3]:
            if count >= 2:
                priorities.append({
                    "type": "tool",
                    "priority": "high" if count >= 5 else "medium",
                    "description": f"Outil problématique: {tool}",
                    "failure_count": count,
                    "action": "Vérifier la configuration et l'utilisation de cet outil"
                })
        
        return sorted(priorities, key=lambda x: 0 if x["priority"] == "high" else 1)
    
    def clear_old_feedback(self, days: int = 30):
        """Nettoie les feedbacks anciens."""
        cutoff = datetime.now() - timedelta(days=days)
        
        self.feedbacks = [
            f for f in self.feedbacks
            if datetime.fromisoformat(f.timestamp) > cutoff
        ]
        
        # Reconstruire l'index
        self.feedback_by_message = {}
        for f in self.feedbacks:
            if f.message_id not in self.feedback_by_message:
                self.feedback_by_message[f.message_id] = []
            self.feedback_by_message[f.message_id].append(f)
        
        logger.info(f"Feedback nettoyé, {len(self.feedbacks)} restants")


# Instance singleton
_feedback_collector: Optional[FeedbackCollector] = None

def get_feedback_collector() -> FeedbackCollector:
    """Retourne l'instance singleton."""
    global _feedback_collector
    if _feedback_collector is None:
        _feedback_collector = FeedbackCollector()
    return _feedback_collector
