"""
Governance Module - AI Orchestrator v7
Gestion des rôles, permissions et vérifications

Principes:
1. Toute action admin doit être justifiée
2. Phase de vérification obligatoire
3. Rollback prévu pour actions sensibles
4. Traçabilité complète
"""

import asyncio
import logging
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class GovernanceError(Exception):
    """Exception levée quand la gouvernance bloque une action (CRQ-P0-2)"""

    def __init__(self, message: str, action_category: str = None, action_id: str = None):
        super().__init__(message)
        self.action_category = action_category
        self.action_id = action_id


class ActionCategory(Enum):
    """Catégories d'actions avec niveau de risque"""

    READ = "read"  # Lecture seule - aucun risque
    SAFE = "safe"  # Actions sûres - risque minimal
    MODERATE = "moderate"  # Actions modérées - vérification recommandée
    SENSITIVE = "sensitive"  # Actions sensibles - vérification + rollback obligatoires
    CRITICAL = "critical"  # Actions critiques - approbation manuelle requise


@dataclass
class ActionContext:
    """Contexte d'une action pour audit et rollback"""

    action_id: str
    category: ActionCategory
    description: str
    justification: str
    timestamp: datetime = field(default_factory=datetime.now)
    user: str = "system"
    rollback_data: Optional[Dict] = None
    verification_required: bool = False
    verified: bool = False
    verification_result: Optional[Dict] = None


@dataclass
class RollbackInfo:
    """Informations pour rollback d'une action"""

    action_id: str
    rollback_type: str  # file_restore, service_restart, config_revert
    original_state: Any
    rollback_command: Optional[str] = None
    backup_path: Optional[str] = None


class GovernanceManager:
    """Gestionnaire de gouvernance des actions"""

    def __init__(self, backup_dir: str = "/home/lalpha/orchestrator-backups"):
        self.backup_dir = backup_dir
        self.action_history: List[ActionContext] = []
        self.pending_verifications: Dict[str, ActionContext] = {}
        self.rollback_registry: Dict[str, RollbackInfo] = {}
        self._ensure_backup_dir()

    def _ensure_backup_dir(self):
        """Crée le répertoire de backup"""
        os.makedirs(self.backup_dir, exist_ok=True)

    def _generate_action_id(self) -> str:
        """Génère un ID unique pour une action"""
        import uuid

        return f"action_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def classify_action(self, tool_name: str, params: Dict) -> ActionCategory:
        """
        Classifie une action selon son niveau de risque.

        Args:
            tool_name: Nom de l'outil
            params: Paramètres de l'action

        Returns:
            Catégorie de l'action
        """
        # Actions READ (lecture seule)
        read_tools = {
            "read_file",
            "list_directory",
            "search_files",
            "search_directory",
            "get_system_info",
            "get_datetime",
            "get_audit_log",
            "git_status",
            "git_diff",
            "list_llm_models",
        }

        # Actions SAFE (sûres)
        safe_tools = {"calculate", "http_request"}  # GET only

        # Actions MODERATE (modérées)
        moderate_tools = {
            "execute_command",  # Dépend de la commande
            "run_tests",
            "run_lint",
            "run_format",
            "run_typecheck",
        }

        # Actions SENSITIVE (sensibles)
        sensitive_tools = {"write_file", "run_build"}

        if tool_name in read_tools:
            return ActionCategory.READ

        if tool_name in safe_tools:
            return ActionCategory.SAFE

        if tool_name in moderate_tools:
            # Pour execute_command, analyser la commande
            if tool_name == "execute_command":
                cmd = params.get("command", "")
                role = params.get("role", "operator")

                if role == "admin":
                    return ActionCategory.SENSITIVE
                elif role == "operator":
                    return ActionCategory.MODERATE
                else:
                    return ActionCategory.SAFE

            return ActionCategory.MODERATE

        if tool_name in sensitive_tools:
            return ActionCategory.SENSITIVE

        # Par défaut: MODERATE
        return ActionCategory.MODERATE

    def requires_verification(self, category: ActionCategory) -> bool:
        """Détermine si une action nécessite vérification"""
        return category in [ActionCategory.SENSITIVE, ActionCategory.CRITICAL]

    def requires_rollback(self, category: ActionCategory) -> bool:
        """Détermine si une action nécessite un plan de rollback"""
        return category in [ActionCategory.SENSITIVE, ActionCategory.CRITICAL]

    async def prepare_action(
        self, tool_name: str, params: Dict, justification: str = ""
    ) -> Tuple[bool, ActionContext, str]:
        """
        Prépare une action avant exécution.

        Args:
            tool_name: Nom de l'outil
            params: Paramètres
            justification: Justification de l'action

        Returns:
            (approved, context, message)
        """
        action_id = self._generate_action_id()
        category = self.classify_action(tool_name, params)

        context = ActionContext(
            action_id=action_id,
            category=category,
            description=f"{tool_name}({params})",
            justification=justification,
            verification_required=self.requires_verification(category),
        )

        # Vérifier si l'action nécessite une justification
        if category in [ActionCategory.SENSITIVE, ActionCategory.CRITICAL]:
            if not justification:
                return False, context, f"Action {category.value} requiert une justification"

        # Préparer le rollback si nécessaire
        if self.requires_rollback(category):
            rollback_info = await self._prepare_rollback(tool_name, params, action_id)
            if rollback_info:
                self.rollback_registry[action_id] = rollback_info
                context.rollback_data = {"type": rollback_info.rollback_type}

        self.action_history.append(context)
        logger.info(f"[GOVERNANCE] Action préparée: {action_id} ({category.value})")

        return True, context, "Action approuvée"

    async def _prepare_rollback(
        self, tool_name: str, params: Dict, action_id: str
    ) -> Optional[RollbackInfo]:
        """Prépare les informations de rollback pour une action"""

        if tool_name == "write_file":
            path = params.get("path", "")
            if os.path.exists(path):
                # Sauvegarder le fichier existant
                backup_path = os.path.join(
                    self.backup_dir, f"{action_id}_{os.path.basename(path)}.backup"
                )
                try:
                    shutil.copy2(path, backup_path)
                    return RollbackInfo(
                        action_id=action_id,
                        rollback_type="file_restore",
                        original_state={"path": path},
                        backup_path=backup_path,
                    )
                except Exception as e:
                    logger.warning(f"Impossible de créer le backup: {e}")

        elif tool_name == "execute_command":
            cmd = params.get("command", "")
            role = params.get("role", "operator")

            # Pour les commandes admin, enregistrer la possibilité de rollback
            if role == "admin":
                # Certaines commandes ont des inverses connus
                rollback_commands = {
                    "systemctl start": "systemctl stop",
                    "systemctl stop": "systemctl start",
                    "systemctl enable": "systemctl disable",
                    "systemctl disable": "systemctl enable",
                }

                for prefix, rollback in rollback_commands.items():
                    if cmd.startswith(prefix):
                        service = cmd.replace(prefix, "").strip()
                        return RollbackInfo(
                            action_id=action_id,
                            rollback_type="command_inverse",
                            original_state={"command": cmd},
                            rollback_command=f"{rollback} {service}",
                        )

        return None

    async def record_result(self, action_id: str, success: bool, result: Dict):
        """Enregistre le résultat d'une action"""
        for action in self.action_history:
            if action.action_id == action_id:
                action.verified = True
                action.verification_result = {
                    "success": success,
                    "result": result,
                    "verified_at": datetime.now().isoformat(),
                }
                logger.info(f"[GOVERNANCE] Résultat enregistré: {action_id} -> {success}")
                break

    async def rollback(self, action_id: str) -> Tuple[bool, str]:
        """
        Effectue le rollback d'une action.

        Args:
            action_id: ID de l'action à annuler

        Returns:
            (success, message)
        """
        if action_id not in self.rollback_registry:
            return False, f"Pas de rollback disponible pour {action_id}"

        rollback_info = self.rollback_registry[action_id]

        try:
            if rollback_info.rollback_type == "file_restore":
                if rollback_info.backup_path and os.path.exists(rollback_info.backup_path):
                    original_path = rollback_info.original_state["path"]
                    shutil.copy2(rollback_info.backup_path, original_path)
                    logger.info(f"[GOVERNANCE] Rollback fichier: {original_path}")
                    return True, f"Fichier restauré: {original_path}"

            elif rollback_info.rollback_type == "command_inverse":
                if rollback_info.rollback_command:
                    from .secure_executor import ExecutionRole, secure_executor

                    result = await secure_executor.execute(
                        rollback_info.rollback_command, role=ExecutionRole.ADMIN, timeout=30
                    )
                    if result.success:
                        logger.info(
                            f"[GOVERNANCE] Rollback commande: {rollback_info.rollback_command}"
                        )
                        return True, f"Commande inverse exécutée: {rollback_info.rollback_command}"
                    else:
                        return False, f"Échec rollback: {result.error_message}"

            return False, f"Type de rollback non supporté: {rollback_info.rollback_type}"

        except Exception as e:
            logger.error(f"[GOVERNANCE] Erreur rollback: {e}")
            return False, str(e)

    def get_action_history(self, last_n: int = 20) -> List[Dict]:
        """Récupère l'historique des actions"""
        actions = self.action_history[-last_n:]
        return [
            {
                "action_id": a.action_id,
                "category": a.category.value,
                "description": a.description[:100],
                "justification": a.justification,
                "timestamp": a.timestamp.isoformat(),
                "verification_required": a.verification_required,
                "verified": a.verified,
                "has_rollback": a.action_id in self.rollback_registry,
            }
            for a in actions
        ]

    def get_pending_verifications(self) -> List[Dict]:
        """Récupère les actions en attente de vérification"""
        pending = [a for a in self.action_history if a.verification_required and not a.verified]
        return [
            {
                "action_id": a.action_id,
                "category": a.category.value,
                "description": a.description,
                "timestamp": a.timestamp.isoformat(),
            }
            for a in pending
        ]


# Instance globale
governance_manager = GovernanceManager()
