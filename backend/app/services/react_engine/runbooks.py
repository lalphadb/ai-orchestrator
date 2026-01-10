"""
Runbooks Module - AI Orchestrator v7
Procédures standardisées pour tâches récurrentes

Principe: Suivre les runbooks, ne pas improviser
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class RunbookCategory(Enum):
    """Catégories de runbooks"""
    DEPLOYMENT = "deployment"     # Déploiement
    DIAGNOSTIC = "diagnostic"     # Diagnostic
    RECOVERY = "recovery"         # Récupération
    MAINTENANCE = "maintenance"   # Maintenance
    SECURITY = "security"         # Sécurité


@dataclass
class RunbookStep:
    """Étape d'un runbook"""
    name: str
    description: str
    command: Optional[str] = None  # Commande à exécuter
    tool: Optional[str] = None     # Outil à utiliser
    tool_params: Dict = field(default_factory=dict)
    verify_command: Optional[str] = None  # Commande de vérification
    expected_result: Optional[str] = None
    on_failure: str = "stop"  # stop, continue, rollback


@dataclass
class Runbook:
    """Procédure standardisée"""
    id: str
    name: str
    description: str
    category: RunbookCategory
    steps: List[RunbookStep]
    tags: List[str] = field(default_factory=list)
    requires_admin: bool = False
    estimated_duration: str = "unknown"


class RunbookRegistry:
    """Registre des runbooks disponibles"""
    
    def __init__(self):
        self.runbooks: Dict[str, Runbook] = {}
        self._register_builtin_runbooks()
    
    def register(self, runbook: Runbook):
        """Enregistre un runbook"""
        self.runbooks[runbook.id] = runbook
        logger.info(f"[RUNBOOK] Enregistré: {runbook.id}")
    
    def get(self, runbook_id: str) -> Optional[Runbook]:
        """Récupère un runbook par ID"""
        return self.runbooks.get(runbook_id)
    
    def list_all(self) -> List[Dict]:
        """Liste tous les runbooks"""
        return [
            {
                "id": rb.id,
                "name": rb.name,
                "category": rb.category.value,
                "description": rb.description[:100],
                "steps_count": len(rb.steps),
                "requires_admin": rb.requires_admin,
                "estimated_duration": rb.estimated_duration
            }
            for rb in self.runbooks.values()
        ]
    
    def list_by_category(self, category: RunbookCategory) -> List[Runbook]:
        """Liste les runbooks par catégorie"""
        return [
            rb for rb in self.runbooks.values()
            if rb.category == category
        ]
    
    def search(self, query: str) -> List[Runbook]:
        """Recherche dans les runbooks"""
        query_lower = query.lower()
        results = []
        
        for rb in self.runbooks.values():
            searchable = f"{rb.name} {rb.description} {' '.join(rb.tags)}"
            if query_lower in searchable.lower():
                results.append(rb)
        
        return results
    
    def _register_builtin_runbooks(self):
        """Enregistre les runbooks intégrés"""
        
        # === DIAGNOSTIC ===
        
        self.register(Runbook(
            id="diag-service-down",
            name="Diagnostic Service Down",
            description="Procédure de diagnostic quand un service ne répond plus",
            category=RunbookCategory.DIAGNOSTIC,
            tags=["service", "down", "debug"],
            steps=[
                RunbookStep(
                    name="check_service_status",
                    description="Vérifier le statut du service",
                    command="systemctl status {service_name}",
                    verify_command="systemctl is-active {service_name}"
                ),
                RunbookStep(
                    name="check_logs",
                    description="Examiner les logs récents",
                    command="journalctl -u {service_name} -n 50 --no-pager"
                ),
                RunbookStep(
                    name="check_resources",
                    description="Vérifier les ressources système",
                    tool="get_system_info",
                    tool_params={}
                ),
                RunbookStep(
                    name="check_ports",
                    description="Vérifier si le port est utilisé",
                    command="ss -tlnp | grep {port}"
                ),
                RunbookStep(
                    name="check_disk",
                    description="Vérifier l'espace disque",
                    command="df -h"
                )
            ],
            estimated_duration="2-5 min"
        ))
        
        self.register(Runbook(
            id="diag-docker-container",
            name="Diagnostic Container Docker",
            description="Procédure de diagnostic pour un container Docker",
            category=RunbookCategory.DIAGNOSTIC,
            tags=["docker", "container", "debug"],
            steps=[
                RunbookStep(
                    name="check_container_status",
                    description="Vérifier le statut du container",
                    command="docker ps -a --filter name={container_name}"
                ),
                RunbookStep(
                    name="check_container_logs",
                    description="Examiner les logs du container",
                    command="docker logs --tail 100 {container_name}"
                ),
                RunbookStep(
                    name="check_container_inspect",
                    description="Inspecter la configuration",
                    command="docker inspect {container_name}"
                ),
                RunbookStep(
                    name="check_network",
                    description="Vérifier le réseau Docker",
                    command="docker network ls && docker network inspect unified-net"
                )
            ],
            estimated_duration="2-5 min"
        ))
        
        # === RECOVERY ===
        
        self.register(Runbook(
            id="recover-service-restart",
            name="Redémarrage Service",
            description="Procédure standard de redémarrage d'un service",
            category=RunbookCategory.RECOVERY,
            tags=["service", "restart", "recovery"],
            requires_admin=True,
            steps=[
                RunbookStep(
                    name="stop_service",
                    description="Arrêter le service",
                    command="systemctl stop {service_name}",
                    on_failure="continue"
                ),
                RunbookStep(
                    name="wait",
                    description="Attendre 3 secondes",
                    command="sleep 3"
                ),
                RunbookStep(
                    name="start_service",
                    description="Démarrer le service",
                    command="systemctl start {service_name}",
                    on_failure="stop"
                ),
                RunbookStep(
                    name="verify_status",
                    description="Vérifier que le service est actif",
                    command="systemctl is-active {service_name}",
                    expected_result="active"
                ),
                RunbookStep(
                    name="check_logs",
                    description="Vérifier les logs de démarrage",
                    command="journalctl -u {service_name} -n 20 --no-pager"
                )
            ],
            estimated_duration="1-2 min"
        ))
        
        self.register(Runbook(
            id="recover-docker-restart",
            name="Redémarrage Container Docker",
            description="Procédure de redémarrage d'un container Docker",
            category=RunbookCategory.RECOVERY,
            tags=["docker", "restart", "recovery"],
            requires_admin=True,
            steps=[
                RunbookStep(
                    name="restart_container",
                    description="Redémarrer le container",
                    command="docker restart {container_name}",
                    on_failure="stop"
                ),
                RunbookStep(
                    name="wait",
                    description="Attendre le démarrage",
                    command="sleep 5"
                ),
                RunbookStep(
                    name="check_status",
                    description="Vérifier le statut",
                    command="docker ps --filter name={container_name} --format '{{.Status}}'"
                ),
                RunbookStep(
                    name="check_health",
                    description="Vérifier la santé",
                    command="docker inspect --format='{{.State.Health.Status}}' {container_name} 2>/dev/null || echo 'no healthcheck'"
                )
            ],
            estimated_duration="1-2 min"
        ))
        
        # === DEPLOYMENT ===
        
        self.register(Runbook(
            id="deploy-stack-update",
            name="Mise à jour Stack Docker",
            description="Procédure de mise à jour de la stack unified-stack",
            category=RunbookCategory.DEPLOYMENT,
            tags=["docker", "stack", "deployment", "update"],
            requires_admin=True,
            steps=[
                RunbookStep(
                    name="backup_config",
                    description="Sauvegarder la configuration actuelle",
                    command="cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)"
                ),
                RunbookStep(
                    name="pull_images",
                    description="Télécharger les nouvelles images",
                    command="docker compose pull"
                ),
                RunbookStep(
                    name="down_stack",
                    description="Arrêter la stack",
                    command="./stack.sh down"
                ),
                RunbookStep(
                    name="up_stack",
                    description="Démarrer la stack mise à jour",
                    command="./stack.sh up"
                ),
                RunbookStep(
                    name="verify_services",
                    description="Vérifier tous les services",
                    command="./stack.sh status"
                ),
                RunbookStep(
                    name="run_tests",
                    description="Exécuter les tests de santé",
                    command="./stack.sh test"
                )
            ],
            estimated_duration="5-10 min"
        ))
        
        self.register(Runbook(
            id="deploy-ai-orchestrator",
            name="Déploiement AI Orchestrator",
            description="Procédure de déploiement de l'AI Orchestrator",
            category=RunbookCategory.DEPLOYMENT,
            tags=["ai-orchestrator", "deployment", "backend"],
            requires_admin=True,
            steps=[
                RunbookStep(
                    name="git_pull",
                    description="Récupérer les dernières modifications",
                    command="git pull origin main"
                ),
                RunbookStep(
                    name="install_deps",
                    description="Installer les dépendances",
                    command="cd backend && .venv/bin/pip install -r requirements.txt --quiet"
                ),
                RunbookStep(
                    name="run_tests",
                    description="Exécuter les tests",
                    command="cd backend && .venv/bin/python -m pytest tests/ -q"
                ),
                RunbookStep(
                    name="restart_service",
                    description="Redémarrer le service",
                    command="sudo systemctl restart ai-orchestrator"
                ),
                RunbookStep(
                    name="verify_health",
                    description="Vérifier la santé",
                    command="curl -s http://localhost:8001/api/v1/system/health",
                    expected_result="healthy"
                )
            ],
            estimated_duration="3-5 min"
        ))
        
        # === MAINTENANCE ===
        
        self.register(Runbook(
            id="maint-disk-cleanup",
            name="Nettoyage Disque",
            description="Procédure de nettoyage de l'espace disque",
            category=RunbookCategory.MAINTENANCE,
            tags=["disk", "cleanup", "maintenance"],
            requires_admin=True,
            steps=[
                RunbookStep(
                    name="check_disk_before",
                    description="Vérifier l'espace avant nettoyage",
                    command="df -h"
                ),
                RunbookStep(
                    name="clean_docker",
                    description="Nettoyer les ressources Docker inutilisées",
                    command="docker system prune -f"
                ),
                RunbookStep(
                    name="clean_apt",
                    description="Nettoyer le cache APT",
                    command="sudo apt clean && sudo apt autoremove -y"
                ),
                RunbookStep(
                    name="clean_journals",
                    description="Limiter les journaux système",
                    command="sudo journalctl --vacuum-time=7d"
                ),
                RunbookStep(
                    name="check_disk_after",
                    description="Vérifier l'espace après nettoyage",
                    command="df -h"
                )
            ],
            estimated_duration="5-10 min"
        ))
        
        self.register(Runbook(
            id="maint-backup-create",
            name="Création Backup",
            description="Procédure de création de sauvegarde",
            category=RunbookCategory.MAINTENANCE,
            tags=["backup", "maintenance", "safety"],
            requires_admin=True,
            steps=[
                RunbookStep(
                    name="create_backup_dir",
                    description="Créer le répertoire de backup",
                    command="mkdir -p /home/lalpha/backups/$(date +%Y%m%d)"
                ),
                RunbookStep(
                    name="backup_configs",
                    description="Sauvegarder les configurations",
                    command="tar -czf /home/lalpha/backups/$(date +%Y%m%d)/configs.tar.gz /home/lalpha/projets/infrastructure/unified-stack/configs/"
                ),
                RunbookStep(
                    name="backup_db",
                    description="Sauvegarder la base de données",
                    command="cp /home/lalpha/projets/ai-tools/ai-orchestrator/backend/ai_orchestrator.db /home/lalpha/backups/$(date +%Y%m%d)/"
                ),
                RunbookStep(
                    name="verify_backup",
                    description="Vérifier le backup",
                    command="ls -lah /home/lalpha/backups/$(date +%Y%m%d)/"
                )
            ],
            estimated_duration="2-5 min"
        ))
        
        # === SECURITY ===
        
        self.register(Runbook(
            id="sec-check-services",
            name="Vérification Sécurité Services",
            description="Procédure de vérification de sécurité des services",
            category=RunbookCategory.SECURITY,
            tags=["security", "audit", "services"],
            steps=[
                RunbookStep(
                    name="check_open_ports",
                    description="Vérifier les ports ouverts",
                    command="ss -tlnp"
                ),
                RunbookStep(
                    name="check_firewall",
                    description="Vérifier le firewall",
                    command="sudo ufw status verbose"
                ),
                RunbookStep(
                    name="check_failed_logins",
                    description="Vérifier les tentatives de connexion échouées",
                    command="sudo journalctl -u ssh -n 50 | grep -i 'failed\\|invalid'"
                ),
                RunbookStep(
                    name="check_docker_security",
                    description="Vérifier la sécurité Docker",
                    command="docker info --format '{{.SecurityOptions}}'"
                )
            ],
            estimated_duration="2-3 min"
        ))
        
        logger.info(f"[RUNBOOK] {len(self.runbooks)} runbooks enregistrés")


# Instance globale
runbook_registry = RunbookRegistry()
