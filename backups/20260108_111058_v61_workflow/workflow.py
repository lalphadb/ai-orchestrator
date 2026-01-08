"""
Modèles Pydantic pour le pipeline Spec/Plan/Execute/Verify/Repair
AI Orchestrator v6.1
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from enum import Enum


class WorkflowPhase(str, Enum):
    """Phases du workflow"""
    SPEC = "spec"
    PLAN = "plan"
    EXECUTE = "execute"
    VERIFY = "verify"
    REPAIR = "repair"
    COMPLETE = "complete"
    FAILED = "failed"


# ===== SPECIFICATION =====

class AcceptanceCriteria(BaseModel):
    """Critères d'acceptation de la tâche"""
    checks: List[str] = Field(
        ..., 
        description="Liste des vérifications requises. Ex: 'pytest passes', 'ruff clean', 'build ok'"
    )


class TaskSpec(BaseModel):
    """Spécification de la tâche générée par l'Executor"""
    objective: str = Field(..., description="Objectif clair et mesurable")
    assumptions: List[str] = Field(default=[], description="Hypothèses faites sur le contexte")
    acceptance: AcceptanceCriteria = Field(..., description="Critères d'acceptation")
    risks: List[str] = Field(default=[], description="Risques identifiés")
    out_of_scope: List[str] = Field(default=[], description="Ce qui n'est pas inclus")


# ===== PLANNING =====

class PlanStep(BaseModel):
    """Une étape du plan d'exécution"""
    id: str = Field(..., description="Identifiant unique de l'étape")
    action: str = Field(..., description="Description de l'action")
    tools: List[str] = Field(default=[], description="Outils à utiliser")
    expected_output: str = Field(default="", description="Résultat attendu")
    dependencies: List[str] = Field(default=[], description="IDs des étapes dépendantes")


class TaskPlan(BaseModel):
    """Plan d'exécution de la tâche"""
    steps: List[PlanStep] = Field(..., description="Étapes ordonnées")
    estimated_duration_s: Optional[int] = Field(None, description="Durée estimée en secondes")
    
    def get_step(self, step_id: str) -> Optional[PlanStep]:
        """Récupère une étape par son ID"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None


# ===== EXECUTION =====

class ToolExecution(BaseModel):
    """Trace d'exécution d'un outil"""
    tool: str = Field(..., description="Nom de l'outil")
    params: Dict[str, Any] = Field(default={}, description="Paramètres utilisés")
    result: Dict[str, Any] = Field(..., description="Résultat (ToolResult)")
    duration_ms: int = Field(default=0, description="Durée d'exécution")
    timestamp: datetime = Field(default_factory=datetime.now)


class ExecutionResult(BaseModel):
    """Résultat de l'exécution ReAct"""
    response: str = Field(..., description="Réponse finale")
    tools_used: List[ToolExecution] = Field(default=[], description="Outils exécutés")
    iterations: int = Field(default=0, description="Nombre d'itérations ReAct")
    thinking: str = Field(default="", description="Trace de réflexion")
    duration_ms: int = Field(default=0, description="Durée totale")


# ===== VERIFICATION =====

class CheckResult(BaseModel):
    """Résultat d'un check de vérification"""
    name: str = Field(..., description="Nom du check (ex: run_tests:backend)")
    passed: bool = Field(..., description="Le check a réussi?")
    output: str = Field(default="", description="Sortie du check (truncated)")
    error: Optional[str] = Field(None, description="Message d'erreur si échec")


class VerificationReport(BaseModel):
    """Rapport de vérification"""
    passed: bool = Field(..., description="Tous les checks ont réussi?")
    checks_run: List[str] = Field(default=[], description="Liste des checks exécutés")
    results: List[CheckResult] = Field(default=[], description="Résultats détaillés")
    evidence: Dict[str, Any] = Field(default={}, description="Preuves (stdout, etc.)")
    failures: List[str] = Field(default=[], description="Messages d'échec")
    duration_ms: int = Field(default=0)


# ===== VERIFIER JUDGMENT =====

class JudgeVerdict(BaseModel):
    """Verdict du Verifier (second modèle)"""
    status: Literal["PASS", "FAIL"] = Field(..., description="Verdict final")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Niveau de confiance")
    issues: List[str] = Field(default=[], description="Problèmes identifiés")
    suggested_fixes: List[str] = Field(default=[], description="Corrections suggérées")
    reasoning: str = Field(default="", description="Raisonnement du Verifier")


# ===== REPAIR =====

class RepairAttempt(BaseModel):
    """Tentative de réparation"""
    cycle: int = Field(..., description="Numéro du cycle de réparation")
    issues_addressed: List[str] = Field(default=[], description="Problèmes ciblés")
    changes_made: List[str] = Field(default=[], description="Modifications effectuées")
    tools_used: List[ToolExecution] = Field(default=[])
    verification_after: Optional[VerificationReport] = None


# ===== WORKFLOW STATE =====

class WorkflowState(BaseModel):
    """État complet du workflow"""
    id: str = Field(..., description="ID unique du workflow")
    phase: WorkflowPhase = Field(default=WorkflowPhase.SPEC)
    original_request: str = Field(..., description="Requête originale de l'utilisateur")
    
    # Résultats de chaque phase
    spec: Optional[TaskSpec] = None
    plan: Optional[TaskPlan] = None
    execution: Optional[ExecutionResult] = None
    verification: Optional[VerificationReport] = None
    verdict: Optional[JudgeVerdict] = None
    
    # Réparation
    repair_cycles: int = Field(default=0)
    repair_history: List[RepairAttempt] = Field(default=[])
    
    # Métadonnées
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_duration_ms: int = Field(default=0)
    error: Optional[str] = None


# ===== API RESPONSE EXTENSION =====

class WorkflowResponse(BaseModel):
    """Réponse API enrichie avec preuves de vérification"""
    # Champs existants (compatibilité)
    response: str
    conversation_id: Optional[str] = None
    model_used: str
    tools_used: List[Dict[str, Any]] = []
    iterations: int = 0
    thinking: str = ""
    duration_ms: int = 0
    
    # Nouveaux champs v6.1
    verification: Optional[VerificationReport] = None
    verdict: Optional[JudgeVerdict] = None
    workflow_phase: WorkflowPhase = WorkflowPhase.COMPLETE
    repair_cycles: int = 0
    
    class Config:
        use_enum_values = True
