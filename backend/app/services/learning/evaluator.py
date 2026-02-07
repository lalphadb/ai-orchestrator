"""
PerformanceEvaluator - Évaluation automatique des exécutions

Analyse les résultats pour:
- Calculer un score de performance
- Détecter les patterns de succès/échec
- Identifier les améliorations possibles
- Extraire des corrections automatiques
"""

import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Résultat d'une exécution à évaluer."""
    query: str
    response: str
    tools_used: List[str]
    tool_results: List[Dict[str, Any]]
    iterations: int
    duration_ms: int
    error: Optional[str] = None


@dataclass
class EvaluationScore:
    """Score d'évaluation détaillé."""
    overall: float  # Score global 0-1
    success: bool
    efficiency: float  # Efficacité (moins d'itérations = mieux)
    accuracy: float  # Précision des outils utilisés
    speed: float  # Rapidité
    completeness: float  # Réponse complète
    details: Dict[str, Any]  # Détails du scoring


class PerformanceEvaluator:
    """Évalue automatiquement la performance des exécutions."""
    
    # Patterns d'erreurs connus
    ERROR_PATTERNS = {
        "command_not_found": r"command not found|No such file or directory",
        "permission_denied": r"Permission denied|Access denied|EACCES",
        "timeout": r"timeout|timed out|deadline exceeded",
        "connection_error": r"Connection refused|ECONNREFUSED|network unreachable",
        "syntax_error": r"SyntaxError|syntax error|unexpected token",
        "resource_error": r"out of memory|disk full|no space left",
        "api_error": r"API error|rate limit|quota exceeded",
    }
    
    # Patterns de succès
    SUCCESS_INDICATORS = [
        r"successfully|completed|done|finished",
        r"created|updated|deleted|modified",
        r"found|located|retrieved",
        r"installed|configured|deployed",
    ]
    
    # Benchmarks de performance
    SPEED_BENCHMARKS = {
        "fast": 2000,      # < 2s
        "normal": 5000,    # < 5s
        "slow": 10000,     # < 10s
        "very_slow": 30000 # < 30s
    }
    
    def __init__(self):
        """Initialise l'évaluateur."""
        self.evaluation_history: List[EvaluationScore] = []
    
    def evaluate(self, result: ExecutionResult) -> EvaluationScore:
        """
        Évalue une exécution et retourne un score détaillé.
        
        Args:
            result: Résultat de l'exécution
            
        Returns:
            Score d'évaluation complet
        """
        # 1. Détection succès/échec
        success, success_reason = self._detect_success(result)
        
        # 2. Score d'efficacité (itérations)
        efficiency = self._score_efficiency(result.iterations)
        
        # 3. Score de précision des outils
        accuracy = self._score_tool_accuracy(result.tools_used, result.tool_results)
        
        # 4. Score de vitesse
        speed = self._score_speed(result.duration_ms)
        
        # 5. Score de complétude de la réponse
        completeness = self._score_completeness(result.query, result.response)
        
        # 6. Calcul du score global pondéré
        weights = {
            "success": 0.35,
            "efficiency": 0.15,
            "accuracy": 0.20,
            "speed": 0.10,
            "completeness": 0.20
        }
        
        overall = (
            (1.0 if success else 0.0) * weights["success"] +
            efficiency * weights["efficiency"] +
            accuracy * weights["accuracy"] +
            speed * weights["speed"] +
            completeness * weights["completeness"]
        )
        
        # Détails du scoring
        details = {
            "success_reason": success_reason,
            "iterations": result.iterations,
            "duration_ms": result.duration_ms,
            "tools_count": len(result.tools_used),
            "tools_used": result.tools_used,
            "error_type": self._classify_error(result.error) if result.error else None,
            "response_length": len(result.response),
            "weights": weights
        }
        
        score = EvaluationScore(
            overall=round(overall, 3),
            success=success,
            efficiency=round(efficiency, 3),
            accuracy=round(accuracy, 3),
            speed=round(speed, 3),
            completeness=round(completeness, 3),
            details=details
        )
        
        self.evaluation_history.append(score)
        
        logger.info(f"Évaluation: overall={score.overall}, success={success}")
        
        return score
    
    def _detect_success(self, result: ExecutionResult) -> Tuple[bool, str]:
        """
        Détecte si l'exécution a réussi.
        
        Returns:
            (success, reason)
        """
        # Échec explicite
        if result.error:
            return False, f"error: {result.error[:100]}"
        
        # Vérifier les résultats des outils
        tool_failures = 0
        for tool_result in result.tool_results:
            if not tool_result.get("success", True):
                tool_failures += 1
        
        if tool_failures > 0 and tool_failures == len(result.tool_results):
            return False, "all_tools_failed"
        
        # Vérifier les patterns d'erreur dans la réponse
        for error_type, pattern in self.ERROR_PATTERNS.items():
            if re.search(pattern, result.response, re.IGNORECASE):
                return False, f"error_pattern: {error_type}"
        
        # Vérifier les indicateurs de succès
        for pattern in self.SUCCESS_INDICATORS:
            if re.search(pattern, result.response, re.IGNORECASE):
                return True, "success_indicator_found"
        
        # Par défaut, si pas d'erreur et réponse non vide
        if result.response and len(result.response) > 50:
            return True, "response_complete"
        
        return False, "insufficient_response"
    
    def _score_efficiency(self, iterations: int) -> float:
        """Score basé sur le nombre d'itérations (moins = mieux)."""
        if iterations <= 1:
            return 1.0
        elif iterations <= 2:
            return 0.9
        elif iterations <= 3:
            return 0.7
        elif iterations <= 5:
            return 0.5
        elif iterations <= 8:
            return 0.3
        else:
            return 0.1
    
    def _score_tool_accuracy(
        self,
        tools_used: List[str],
        tool_results: List[Dict[str, Any]]
    ) -> float:
        """Score basé sur la pertinence des outils utilisés."""
        if not tools_used:
            return 0.5  # Pas d'outils peut être OK ou non
        
        successful_tools = sum(
            1 for r in tool_results if r.get("success", True)
        )
        
        return successful_tools / len(tools_used) if tools_used else 0.5
    
    def _score_speed(self, duration_ms: int) -> float:
        """Score basé sur la durée d'exécution."""
        if duration_ms < self.SPEED_BENCHMARKS["fast"]:
            return 1.0
        elif duration_ms < self.SPEED_BENCHMARKS["normal"]:
            return 0.8
        elif duration_ms < self.SPEED_BENCHMARKS["slow"]:
            return 0.6
        elif duration_ms < self.SPEED_BENCHMARKS["very_slow"]:
            return 0.4
        else:
            return 0.2
    
    def _score_completeness(self, query: str, response: str) -> float:
        """Score basé sur la complétude de la réponse."""
        if not response:
            return 0.0
        
        # Heuristiques simples
        response_len = len(response)
        query_len = len(query)
        
        # Une bonne réponse devrait être plus longue que la question
        ratio = response_len / max(query_len, 1)
        
        if ratio < 0.5:
            return 0.2
        elif ratio < 1:
            return 0.4
        elif ratio < 2:
            return 0.6
        elif ratio < 5:
            return 0.8
        else:
            return 1.0
    
    def _classify_error(self, error: str) -> Optional[str]:
        """Classifie le type d'erreur."""
        if not error:
            return None
        
        for error_type, pattern in self.ERROR_PATTERNS.items():
            if re.search(pattern, error, re.IGNORECASE):
                return error_type
        
        return "unknown"
    
    def extract_improvement_suggestions(
        self,
        result: ExecutionResult,
        score: EvaluationScore
    ) -> List[Dict[str, str]]:
        """
        Extrait des suggestions d'amélioration basées sur l'évaluation.
        
        Returns:
            Liste de suggestions
        """
        suggestions = []
        
        # Suggestions basées sur l'efficacité
        if score.efficiency < 0.5:
            suggestions.append({
                "type": "efficiency",
                "priority": "high",
                "suggestion": f"Réduire les itérations (actuellement {result.iterations})",
                "action": "Améliorer le prompt ou utiliser des outils plus directs"
            })
        
        # Suggestions basées sur la vitesse
        if score.speed < 0.4:
            suggestions.append({
                "type": "speed",
                "priority": "medium",
                "suggestion": f"Optimiser la durée ({result.duration_ms}ms)",
                "action": "Utiliser des commandes plus efficaces ou paralléliser"
            })
        
        # Suggestions basées sur les erreurs
        if result.error:
            error_type = self._classify_error(result.error)
            suggestions.append({
                "type": "error",
                "priority": "high",
                "suggestion": f"Corriger l'erreur de type '{error_type}'",
                "action": f"Analyser et stocker la correction pour '{result.error[:100]}'"
            })
        
        # Suggestions basées sur la complétude
        if score.completeness < 0.5:
            suggestions.append({
                "type": "completeness",
                "priority": "medium",
                "suggestion": "Améliorer la complétude de la réponse",
                "action": "Ajouter plus de détails ou vérifier que la question est bien comprise"
            })
        
        return suggestions
    
    def detect_pattern(
        self,
        results: List[Tuple[ExecutionResult, EvaluationScore]]
    ) -> Optional[Dict[str, Any]]:
        """
        Détecte un pattern récurrent dans les résultats.
        
        Args:
            results: Liste de (résultat, score)
            
        Returns:
            Pattern détecté ou None
        """
        if len(results) < 3:
            return None
        
        # Analyser les outils utilisés
        tool_sequences = []
        success_rates = {}
        
        for result, score in results:
            seq = tuple(result.tools_used)
            tool_sequences.append(seq)
            
            if seq not in success_rates:
                success_rates[seq] = {"success": 0, "total": 0}
            
            success_rates[seq]["total"] += 1
            if score.success:
                success_rates[seq]["success"] += 1
        
        # Trouver la séquence la plus fréquente avec bon taux de succès
        best_pattern = None
        best_rate = 0
        
        for seq, stats in success_rates.items():
            if stats["total"] >= 2:
                rate = stats["success"] / stats["total"]
                if rate > best_rate and rate >= 0.7:
                    best_rate = rate
                    best_pattern = {
                        "tools_sequence": list(seq),
                        "success_rate": rate,
                        "usage_count": stats["total"]
                    }
        
        return best_pattern
    
    def get_average_scores(self) -> Dict[str, float]:
        """Retourne les scores moyens de l'historique."""
        if not self.evaluation_history:
            return {}
        
        n = len(self.evaluation_history)
        return {
            "overall": sum(s.overall for s in self.evaluation_history) / n,
            "success_rate": sum(1 for s in self.evaluation_history if s.success) / n,
            "efficiency": sum(s.efficiency for s in self.evaluation_history) / n,
            "accuracy": sum(s.accuracy for s in self.evaluation_history) / n,
            "speed": sum(s.speed for s in self.evaluation_history) / n,
            "completeness": sum(s.completeness for s in self.evaluation_history) / n,
            "total_evaluations": n
        }
