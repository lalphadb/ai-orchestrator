"""
Learning Wrapper pour ReAct Engine

Intègre le système d'apprentissage au moteur ReAct:
- Enrichit les prompts avec le contexte appris
- Évalue automatiquement les exécutions
- Stocke les expériences pour amélioration future
- Suggère des corrections en cas d'erreur
"""

import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import WebSocket

from app.services.learning import (
    get_learning_memory,
    get_context_enricher,
    PerformanceEvaluator,
    ExecutionResult,
    EvaluationScore
)

logger = logging.getLogger(__name__)


class LearningReactWrapper:
    """
    Wrapper qui ajoute les capacités d'apprentissage au ReAct Engine.
    """
    
    def __init__(self, react_engine):
        """
        Initialise le wrapper.
        
        Args:
            react_engine: Instance du ReactEngine original
        """
        self.engine = react_engine
        self.memory = get_learning_memory()
        self.enricher = get_context_enricher()
        self.evaluator = PerformanceEvaluator()
        
        # Tracking de l'exécution courante
        self.current_execution = {
            "tools_used": [],
            "tool_results": [],
            "start_time": None
        }
    
    async def execute_with_learning(
        self,
        query: str,
        websocket: Optional[WebSocket] = None,
        conversation_history: Optional[List[Dict]] = None,
        user_id: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exécute une requête avec apprentissage intégré.
        
        1. Enrichit le prompt avec le contexte appris
        2. Exécute via le ReAct Engine
        3. Évalue le résultat
        4. Stocke l'expérience
        
        Args:
            query: Question de l'utilisateur
            websocket: WebSocket pour streaming
            conversation_history: Historique de conversation
            user_id: ID utilisateur
            model: Modèle à utiliser
            
        Returns:
            Résultat enrichi avec métadonnées d'apprentissage
        """
        # Reset tracking
        self.current_execution = {
            "tools_used": [],
            "tool_results": [],
            "start_time": time.time()
        }
        
        # 1. Enrichir le prompt avec le contexte appris
        learned_context = self.enricher.enrich_prompt(
            query=query,
            user_id=user_id,
            include_experiences=True,
            include_patterns=True
        )
        
        # Injecter le contexte dans la conversation
        enriched_history = conversation_history or []
        if learned_context:
            # Ajouter le contexte comme message système invisible
            enriched_history = [
                {"role": "system", "content": learned_context}
            ] + enriched_history
            
            logger.info(f"Contexte appris injecté ({len(learned_context)} chars)")
        
        # 2. Exécuter via le ReAct Engine avec callback pour tracking
        result = await self._execute_with_tracking(
            query=query,
            websocket=websocket,
            conversation_history=enriched_history,
            model=model
        )
        
        # 3. Calculer la durée
        duration_ms = int((time.time() - self.current_execution["start_time"]) * 1000)
        
        # 4. Évaluer le résultat
        exec_result = ExecutionResult(
            query=query,
            response=result.get("response", ""),
            tools_used=self.current_execution["tools_used"],
            tool_results=self.current_execution["tool_results"],
            iterations=result.get("iterations", 0),
            duration_ms=duration_ms,
            error=result.get("error")
        )
        
        evaluation = self.evaluator.evaluate(exec_result)
        
        # 5. Stocker l'expérience
        experience_id = self.memory.store_experience(
            query=query,
            response=result.get("response", ""),
            tools_used=self.current_execution["tools_used"],
            success=evaluation.success,
            duration_ms=duration_ms,
            iterations=result.get("iterations", 0),
            error=result.get("error"),
            user_id=user_id
        )
        
        # 6. Si succès, détecter et stocker un pattern potentiel
        if evaluation.success and len(self.current_execution["tools_used"]) > 0:
            self._try_store_pattern(query, evaluation)
        
        # 7. Si erreur, chercher une correction connue
        correction_hint = None
        if result.get("error"):
            correction_hint = self.enricher.get_correction_hint(
                error_message=result["error"],
                context=query
            )
        
        # 8. Enrichir le résultat avec les métadonnées d'apprentissage
        result["learning"] = {
            "experience_id": experience_id,
            "evaluation": {
                "overall_score": evaluation.overall,
                "success": evaluation.success,
                "efficiency": evaluation.efficiency,
                "speed": evaluation.speed
            },
            "context_used": bool(learned_context),
            "correction_hint": correction_hint
        }
        
        logger.info(
            f"Exécution avec apprentissage: score={evaluation.overall:.2f}, "
            f"success={evaluation.success}, tools={len(self.current_execution['tools_used'])}"
        )
        
        return result
    
    async def _execute_with_tracking(
        self,
        query: str,
        websocket: Optional[WebSocket] = None,
        conversation_history: Optional[List[Dict]] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exécute avec tracking des outils utilisés.
        """
        # Wrapper pour capturer les appels d'outils
        original_execute_tool = self.engine.tools.execute
        
        async def tracked_execute(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
            """Wrapper qui track les exécutions d'outils."""
            self.current_execution["tools_used"].append(tool_name)
            
            result = await original_execute_tool(tool_name, params)
            
            self.current_execution["tool_results"].append({
                "tool": tool_name,
                "success": result.get("success", True),
                "has_output": bool(result.get("output"))
            })
            
            return result
        
        # Remplacer temporairement
        self.engine.tools.execute = tracked_execute
        
        try:
            # Exécuter le moteur ReAct
            result = await self.engine.execute(
                query=query,
                websocket=websocket,
                conversation_history=conversation_history,
                model=model
            )
            return result
        finally:
            # Restaurer
            self.engine.tools.execute = original_execute_tool
    
    def _try_store_pattern(self, query: str, evaluation: EvaluationScore):
        """
        Tente de stocker un pattern de résolution si pertinent.
        """
        tools = self.current_execution["tools_used"]
        
        if len(tools) < 1 or len(tools) > 5:
            return  # Trop peu ou trop d'outils pour un pattern utile
        
        # Détecter le type de problème basé sur les outils utilisés
        problem_type = self._detect_problem_type(tools)
        
        if problem_type:
            self.memory.store_pattern(
                problem_type=problem_type,
                solution_steps=[f"Utilisé {t}" for t in tools],
                tools_sequence=tools,
                success_rate=1.0 if evaluation.success else 0.0,
                examples=[query[:200]]
            )
            
            logger.info(f"Pattern stocké: {problem_type} avec outils {tools}")
    
    def _detect_problem_type(self, tools: List[str]) -> Optional[str]:
        """
        Détecte le type de problème basé sur les outils utilisés.
        """
        tool_set = set(tools)
        
        # Mapping outils → type de problème
        patterns = {
            "docker_debug": {"docker_ps", "docker_logs", "docker_inspect"},
            "file_operations": {"file_read", "file_write", "file_list"},
            "system_monitoring": {"execute_command", "get_system_info"},
            "network_check": {"execute_command"},  # avec commandes réseau
            "service_management": {"systemctl_status", "execute_command"},
        }
        
        for problem_type, required_tools in patterns.items():
            if tool_set & required_tools:  # Intersection non vide
                return problem_type
        
        # Type générique
        if "execute_command" in tool_set:
            return "command_execution"
        
        return None
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'apprentissage."""
        return {
            "memory_stats": self.memory.get_stats(),
            "evaluator_stats": self.evaluator.get_average_scores(),
            "current_session": {
                "tools_used_total": len(self.current_execution.get("tools_used", []))
            }
        }


def create_learning_engine(react_engine) -> LearningReactWrapper:
    """
    Factory pour créer un moteur ReAct avec apprentissage.
    
    Args:
        react_engine: Instance du ReactEngine
        
    Returns:
        LearningReactWrapper configuré
    """
    return LearningReactWrapper(react_engine)
