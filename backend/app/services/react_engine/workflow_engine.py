"""
Workflow Engine - Pipeline Spec→Plan→Execute→Verify→Repair
AI Orchestrator v7.0

Orchestre le flux complet:
1. SPEC: Générer spécification + critères d'acceptation
2. PLAN: Générer plan d'exécution
3. EXECUTE: Exécuter via ReAct Engine
4. VERIFY: Exécuter outils QA obligatoires
5. REPAIR: Si échec, corriger et re-vérifier (max N cycles)
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.metrics import record_workflow_phase
from app.models.workflow import (AcceptanceCriteria, CheckResult,
                                 ExecutionResult, JudgeVerdict, PlanStep,
                                 RepairAttempt, TaskPlan, TaskSpec,
                                 ToolExecution, VerificationReport,
                                 WorkflowPhase, WorkflowResponse,
                                 WorkflowState)
from app.services.ollama.client import ollama_client
from app.services.react_engine.engine import react_engine
from app.services.react_engine.tools import BUILTIN_TOOLS
from app.services.react_engine.verifier import verifier_service
from app.services.websocket.event_emitter import event_emitter
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    Moteur de workflow orchestrant le pipeline complet.
    """

    SPEC_PROMPT = """Analyse cette demande et génère une SPÉCIFICATION.

Demande: {request}

Réponds UNIQUEMENT avec ce JSON:
```json
{{
  "objective": "objectif clair et mesurable",
  "assumptions": ["hypothèse 1", "hypothèse 2"],
  "acceptance": {{
    "checks": ["pytest passes", "ruff clean", "fichier créé"]
  }},
  "risks": ["risque potentiel"],
  "out_of_scope": ["ce qui n'est pas inclus"]
}}
```"""

    PLAN_PROMPT = """Crée un PLAN d'exécution pour cette tâche.

Objectif: {objective}
Critères d'acceptation: {acceptance}

Outils disponibles: {tools}

Réponds UNIQUEMENT avec ce JSON:
```json
{{
  "steps": [
    {{"id": "1", "action": "description", "tools": ["outil1"], "expected_output": "résultat attendu"}},
    {{"id": "2", "action": "description", "tools": ["outil2"], "expected_output": "résultat attendu"}}
  ],
  "estimated_duration_s": 60
}}
```"""

    REPAIR_PROMPT = """La vérification a ÉCHOUÉ. Tu dois réparer.

Problèmes identifiés:
{issues}

Corrections suggérées:
{fixes}

Contexte:
- Réponse précédente: {previous_response}
- Dernier outil utilisé: {last_tool}

Effectue les corrections minimales nécessaires. Tu as accès aux mêmes outils.
Après correction, vérifie avec les outils QA (run_tests, run_lint, etc.)."""

    def __init__(self):
        self.executor_model = settings.EXECUTOR_MODEL
        self.verify_required = settings.VERIFY_REQUIRED
        self.max_repair_cycles = settings.MAX_REPAIR_CYCLES

    async def run(
        self,
        user_message: str,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        websocket: Optional[WebSocket] = None,
        skip_spec: bool = False,
        run_id: Optional[str] = None,
    ) -> WorkflowResponse:
        """
        Exécute le workflow complet.

        Args:
            user_message: Message de l'utilisateur
            conversation_id: ID de conversation (optionnel)
            model: Modèle à utiliser (défaut: EXECUTOR_MODEL)
            history: Historique de conversation
            websocket: WebSocket pour streaming
            skip_spec: Sauter la génération de spec (pour questions simples)
            run_id: Run identifier for WebSocket v8 (will use workflow_id if not provided)

        Returns:
            WorkflowResponse avec résultats et preuves
        """
        start_time = time.time()
        model = model or self.executor_model
        workflow_id = str(uuid.uuid4())[:8]
        run_id = run_id or workflow_id

        # État du workflow
        state = WorkflowState(
            id=workflow_id,
            original_request=user_message,
        )

        try:
            # Détecter si c'est une question simple (pas besoin de spec/plan)
            is_simple = self._is_simple_request(user_message)
            logger.debug(
                f"Run {run_id}: is_simple={is_simple}, skip_spec={skip_spec}, model={model}"
            )
            logger.debug(f"Run {run_id}: message={user_message[:80]}")

            if is_simple or skip_spec:
                # Mode simplifié: exécuter directement
                state.phase = WorkflowPhase.EXECUTE
                if websocket:
                    await event_emitter.emit(
                        websocket,
                        "phase",
                        run_id,
                        {
                            "phase": "execute",
                            "status": "starting",
                            "message": "Traitement de la demande...",
                        },
                    )

                logger.debug(f"Run {run_id}: calling _execute (simple path)")
                execution = await self._execute(user_message, model, history, websocket, run_id)
                logger.debug(
                    f"Run {run_id}: _execute returned, response length={len(execution.response) if execution.response else 0}"
                )
                state.execution = execution

                # Quick check sans QA complet
                verdict = await verifier_service.quick_check(
                    execution.response,
                    [
                        t.model_dump() if hasattr(t, "model_dump") else t
                        for t in execution.tools_used
                    ],
                )
                state.verdict = verdict

            else:
                # Mode complet: Spec → Plan → Execute → Verify → Repair

                # 1. SPEC
                state.phase = WorkflowPhase.SPEC
                if websocket:
                    await event_emitter.emit(
                        websocket,
                        "phase",
                        run_id,
                        {
                            "phase": "spec",
                            "status": "starting",
                            "message": "Analyse et spécification...",
                        },
                    )

                phase_start = time.time()
                spec = await self._generate_spec(user_message, model)
                state.spec = spec
                record_workflow_phase("SPEC", time.time() - phase_start)  # PHASE 6

                # 2. PLAN
                state.phase = WorkflowPhase.PLAN
                if websocket:
                    await event_emitter.emit(
                        websocket,
                        "phase",
                        run_id,
                        {"phase": "plan", "status": "starting", "message": "Planification..."},
                    )

                phase_start = time.time()
                plan = await self._generate_plan(spec, model)
                state.plan = plan
                record_workflow_phase("PLAN", time.time() - phase_start)  # PHASE 6

                # 3. EXECUTE
                state.phase = WorkflowPhase.EXECUTE
                if websocket:
                    await event_emitter.emit(
                        websocket,
                        "phase",
                        run_id,
                        {
                            "phase": "execute",
                            "status": "starting",
                            "message": "Exécution du plan...",
                        },
                    )

                # Enrichir le prompt avec le contexte du plan
                enriched_message = self._enrich_with_plan(user_message, spec, plan)

                phase_start = time.time()
                execution = await self._execute(enriched_message, model, history, websocket, run_id)
                state.execution = execution
                record_workflow_phase("EXECUTE", time.time() - phase_start)  # PHASE 6

                # 4. VERIFY (obligatoire si configuré)
                if self.verify_required:
                    state.phase = WorkflowPhase.VERIFY
                    if websocket:
                        await event_emitter.emit(
                            websocket,
                            "phase",
                            run_id,
                            {
                                "phase": "verify",
                                "status": "starting",
                                "message": "Vérification QA...",
                            },
                        )

                    phase_start = time.time()
                    verification = await self._run_verification(spec, websocket, run_id)
                    state.verification = verification
                    record_workflow_phase("VERIFY", time.time() - phase_start)  # PHASE 6

                    # 5. JUDGE
                    verdict = await verifier_service.judge(
                        user_message, spec, execution, verification
                    )
                    state.verdict = verdict

                    # 6. REPAIR si nécessaire
                    while verdict.status == "FAIL" and state.repair_cycles < self.max_repair_cycles:
                        state.phase = WorkflowPhase.REPAIR
                        state.repair_cycles += 1

                        if websocket:
                            await event_emitter.emit(
                                websocket,
                                "phase",
                                run_id,
                                {
                                    "phase": "repair",
                                    "status": "starting",
                                    "cycle": state.repair_cycles,
                                    "message": f"Réparation (cycle {state.repair_cycles}/{self.max_repair_cycles})...",
                                },
                            )

                        # Réparer
                        phase_start = time.time()
                        repair_attempt = await self._repair(state, verdict, model, websocket)
                        state.repair_history.append(repair_attempt)
                        record_workflow_phase("REPAIR", time.time() - phase_start)  # PHASE 6

                        # Re-vérifier
                        verification = await self._run_verification(spec, websocket, run_id)
                        state.verification = verification

                        # Re-juger
                        verdict = await verifier_service.judge(
                            user_message, spec, state.execution, verification
                        )
                        state.verdict = verdict
                else:
                    # Pas de vérification obligatoire - quick check
                    verdict = await verifier_service.quick_check(
                        execution.response,
                        [
                            t.model_dump() if hasattr(t, "model_dump") else t
                            for t in execution.tools_used
                        ],
                    )
                    state.verdict = verdict

            # Finaliser
            state.phase = (
                WorkflowPhase.COMPLETE if state.verdict.status == "PASS" else WorkflowPhase.FAILED
            )
            state.completed_at = datetime.now(timezone.utc)
            state.total_duration_ms = int((time.time() - start_time) * 1000)

            # Construire la réponse
            response = self._build_response(state, model, conversation_id)

            # Envoyer le message complete (terminal event)
            if websocket:
                terminal_data = {
                    "message": "Workflow completed successfully",
                    "response": response.response,
                    "verification": (
                        response.verification.model_dump() if response.verification else None
                    ),
                    "verdict": response.verdict.model_dump() if response.verdict else None,
                    "tools_used": response.tools_used,
                    "iterations": response.iterations,
                    "duration_ms": response.duration_ms,
                    "repair_cycles": response.repair_cycles,
                }
                logger.debug(
                    f"Sending 'complete' event for run {run_id}, response length: {len(response.response) if response.response else 0}"
                )

                await event_emitter.emit_terminal(
                    websocket,
                    "complete",
                    run_id,
                    terminal_data,
                )

            return response

        except Exception as e:
            logger.error(f"Workflow error: {e}")
            state.phase = WorkflowPhase.FAILED
            state.error = str(e)

            # Envoyer le message error (terminal event)
            if websocket:
                await event_emitter.emit_terminal(
                    websocket, "error", run_id, {"message": str(e), "phase": state.phase.value}
                )

            return WorkflowResponse(
                response=f"Erreur dans le workflow: {e}",
                model_used=model,
                workflow_phase=WorkflowPhase.FAILED,
                duration_ms=int((time.time() - start_time) * 1000),
            )

    def _is_simple_request(self, message: str) -> bool:
        """Détecte si c'est une question simple ne nécessitant pas spec/plan.

        Règles:
        - Conversational queries sont simples.
        - Les questions (avec "?" ou mots interrogatifs) sont simples SAUF
          si elles contiennent des verbes d'action potentiellement dangereux
          (install, update, create, delete, etc.).
        - Les messages très courts ne sont simples que s'ils sont des questions.
        """

        message_lower = message.lower().strip()

        # Heuristique stricte: indicateurs de modification système/fichier
        unsafe_indicators = [
            "fichier",
            "dossier",
            "répertoire",
            "repertoire",
            "config",
            ".yml",
            "/tmp",
            "utilisateur",
            "user",
        ]
        if any(ind in message_lower for ind in unsafe_indicators):
            return False

        # Conversational / small talk
        conversational = [
            "bonjour",
            "salut",
            "hello",
            "hi",
            "comment ça va",
            "how are you",
            "qui es-tu",
            "who are you",
            "merci",
            "thanks",
            "au revoir",
            "bye",
        ]
        if any(p in message_lower for p in conversational):
            return True

        # Interrogatives / question detection
        question_words = [
            # French
            "qui",
            "quoi",
            "où",
            "ou",
            "quand",
            "comment",
            "pourquoi",
            "quel",
            "quelle",
            "quels",
            "quelles",
            "est-ce",
            # English
            "who",
            "what",
            "where",
            "when",
            "how",
            "why",
        ]
        is_question = ("?" in message_lower) or any(w in message_lower for w in question_words)

        # Allowed info verbs (still safe when phrased as a question)
        info_verbs = [
            "affiche",
            "montre",
            "liste",  # fr
            "show",
            "display",
            "list",  # en
        ]

        # Dangerous action verbs / intents → must be COMPLEX
        dangerous_actions = [
            # fr
            "installe",
            "install",
            "met à jour",
            "met a jour",
            "update",
            "crée",
            "cree",
            "create",
            "supprime",
            "delete",
            "modifie",
            "edit",
            "écris",
            "ecris",
            "write",
            "configure",
            "change",
            "exécute",
            "execute",
            "lance",
            "start",
            "arrête",
            "stop",
            "redémarre",
            "restart",
        ]

        dangerous_hit = any(a in message_lower for a in dangerous_actions)
        if dangerous_hit:
            # Log classification decision for observability
            logger.debug(
                "[simple-detector] Dangerous action detected, forcing workflow mode",
                extra={
                    "classification_reason": "dangerous_action",
                    "message_preview": message_lower[:100],
                    "is_simple": False,
                },
            )
            return False

        # Short messages are only simple if they're questions
        if len(message_lower.split()) <= 5 and is_question:
            return True

        # Info questions are simple
        info_patterns = [
            "qu'est-ce que",
            "what is",
            "explique",
            "explain",
            "définis",
            "define",
        ]

        if is_question and (
            any(p in message_lower for p in info_patterns)
            or any(v in message_lower for v in info_verbs)
        ):
            return True

        # Generic question without dangerous actions is simple (e.g. "uptime du serveur?")
        if is_question:
            return True

        return False

    async def _generate_spec(self, request: str, model: str) -> TaskSpec:
        """Génère la spécification de la tâche"""
        prompt = self.SPEC_PROMPT.format(request=request)

        response = await ollama_client.generate(
            prompt=prompt, model=model, options={"temperature": 0.3}
        )

        content = response.get("response", "")

        # Parser le JSON
        try:
            import re

            json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                data = json.loads(content)

            return TaskSpec(
                objective=data.get("objective", request),
                assumptions=data.get("assumptions", []),
                acceptance=AcceptanceCriteria(
                    checks=data.get("acceptance", {}).get("checks", ["task completed"])
                ),
                risks=data.get("risks", []),
                out_of_scope=data.get("out_of_scope", []),
            )
        except Exception as e:
            logger.warning(f"Failed to parse spec: {e}")
            return TaskSpec(
                objective=request, acceptance=AcceptanceCriteria(checks=["task completed"])
            )

    async def _generate_plan(self, spec: TaskSpec, model: str) -> TaskPlan:
        """Génère le plan d'exécution"""
        tools_list = ", ".join([t["name"] for t in BUILTIN_TOOLS.list_tools()])

        prompt = self.PLAN_PROMPT.format(
            objective=spec.objective, acceptance=", ".join(spec.acceptance.checks), tools=tools_list
        )

        response = await ollama_client.generate(
            prompt=prompt, model=model, options={"temperature": 0.3}
        )

        content = response.get("response", "")

        try:
            import re

            json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                data = json.loads(content)

            steps = [
                PlanStep(
                    id=str(s.get("id", i)),
                    action=s.get("action", ""),
                    tools=s.get("tools", []),
                    expected_output=s.get("expected_output", ""),
                )
                for i, s in enumerate(data.get("steps", []))
            ]

            return TaskPlan(steps=steps, estimated_duration_s=data.get("estimated_duration_s"))
        except Exception as e:
            logger.warning(f"Failed to parse plan: {e}")
            return TaskPlan(
                steps=[PlanStep(id="1", action="Execute task", tools=["execute_command"])]
            )

    def _enrich_with_plan(self, message: str, spec: TaskSpec, plan: TaskPlan) -> str:
        """Enrichit le message avec le contexte du plan"""
        steps_str = "\n".join(
            [f"  {s.id}. {s.action} (outils: {', '.join(s.tools)})" for s in plan.steps]
        )

        return f"""{message}

---
CONTEXTE (généré automatiquement):
Objectif: {spec.objective}
Plan:
{steps_str}

Critères d'acceptation: {', '.join(spec.acceptance.checks)}

IMPORTANT: Après avoir terminé, tu DOIS vérifier avec les outils QA (run_tests, run_lint, etc.)
---"""

    async def _execute(
        self,
        message: str,
        model: str,
        history: Optional[List[Dict]],
        websocket: Optional[WebSocket],
        run_id: Optional[str] = None,
    ) -> ExecutionResult:
        """Exécute via le ReAct Engine"""
        result = await react_engine.run(
            user_message=message, model=model, history=history, websocket=websocket, run_id=run_id
        )

        # Convertir en ExecutionResult
        tools_used = []
        for t in result.get("tools_used", []):
            tools_used.append(
                ToolExecution(
                    tool=t.get("tool", "unknown"),
                    params=t.get("input", {}),
                    result=t.get("output", {}),
                    duration_ms=t.get("duration_ms", 0),
                )
            )

        return ExecutionResult(
            response=result.get("response", ""),
            tools_used=tools_used,
            iterations=result.get("iterations", 0),
            thinking=result.get("thinking", ""),
            duration_ms=result.get("duration_ms", 0),
        )

    async def run_qa_checks(
        self,
        websocket: Optional[WebSocket] = None,
        run_id: str = None,
        checks: Optional[List[str]] = None,
    ) -> VerificationReport:
        """
        Exécute des checks QA basiques sans nécessiter un TaskSpec.
        Utilisé pour Re-verify depuis l'UI.

        Args:
            websocket: WebSocket pour streaming
            run_id: ID du run pour les événements
            checks: Liste des checks à exécuter (défaut: git_status, run_lint)
        """
        start = time.time()
        checks_run = []
        results = []
        evidence = {}
        failures = []

        # Checks par défaut si non spécifiés
        default_checks = [
            ("git_status", "git_status", {}),
            ("run_lint:backend", "run_lint", {"target": "backend"}),
        ]

        qa_checks = []
        if checks:
            for check in checks:
                if check == "tests":
                    qa_checks.append(("run_tests:backend", "run_tests", {"target": "backend"}))
                elif check == "lint":
                    qa_checks.append(("run_lint:backend", "run_lint", {"target": "backend"}))
                elif check == "format":
                    qa_checks.append(("run_format:backend", "run_format", {"target": "backend"}))
                elif check == "typecheck":
                    qa_checks.append(
                        ("run_typecheck:backend", "run_typecheck", {"target": "backend"})
                    )
                elif check == "git":
                    qa_checks.append(("git_status", "git_status", {}))
        else:
            qa_checks = default_checks

        for check_name, tool_name, params in qa_checks:
            checks_run.append(check_name)

            if websocket:
                await event_emitter.emit(
                    websocket,
                    "verification_item",
                    run_id,
                    {"name": check_name, "passed": False, "status": "running"},
                )

            result = await BUILTIN_TOOLS.execute(tool_name, **params)

            passed = result.get("success", False)
            output = ""
            error = None

            if result.get("data"):
                output = result["data"].get("stdout", "")[:1000]
            if result.get("error"):
                error = result["error"].get("message", str(result["error"]))
                failures.append(f"{check_name}: {error}")

            if websocket:
                await event_emitter.emit(
                    websocket,
                    "verification_item",
                    run_id,
                    {
                        "name": check_name,
                        "passed": passed,
                        "status": "passed" if passed else "failed",
                        "output": output[:500] if output else None,
                        "error": error,
                    },
                )

            results.append(CheckResult(name=check_name, passed=passed, output=output, error=error))
            evidence[check_name] = result.get("data") or {"error": error}

        return VerificationReport(
            passed=len(failures) == 0,
            checks_run=checks_run,
            results=results,
            evidence=evidence,
            failures=failures,
            duration_ms=int((time.time() - start) * 1000),
        )

    async def _run_verification(
        self, spec: TaskSpec, websocket: Optional[WebSocket] = None, run_id: str = None
    ) -> VerificationReport:
        """Exécute les outils de vérification QA avec événements WS"""
        start = time.time()
        checks_run = []
        results = []
        evidence = {}
        failures = []

        # Mapper les critères d'acceptation aux outils QA
        qa_checks = self._map_acceptance_to_qa(spec.acceptance.checks)

        for check_name, tool_name, params in qa_checks:
            checks_run.append(check_name)

            # Envoyer événement "running"
            if websocket:
                await event_emitter.emit(
                    websocket,
                    "verification_item",
                    run_id,
                    {"name": check_name, "passed": False, "status": "running"},
                )

            # Exécuter l'outil QA
            result = await BUILTIN_TOOLS.execute(tool_name, **params)

            passed = result.get("success", False)
            output = ""
            error = None

            if result.get("data"):
                output = result["data"].get("stdout", "")[:1000]
            if result.get("error"):
                error = result["error"].get("message", str(result["error"]))
                failures.append(f"{check_name}: {error}")

            # Envoyer événement "passed" ou "failed"
            if websocket:
                await event_emitter.emit(
                    websocket,
                    "verification_item",
                    run_id,
                    {
                        "name": check_name,
                        "passed": passed,
                        "status": "passed" if passed else "failed",
                        "output": output[:500] if output else None,
                        "error": error,
                    },
                )

            results.append(CheckResult(name=check_name, passed=passed, output=output, error=error))

            evidence[check_name] = result.get("data") or {"error": error}

        return VerificationReport(
            passed=len(failures) == 0,
            checks_run=checks_run,
            results=results,
            evidence=evidence,
            failures=failures,
            duration_ms=int((time.time() - start) * 1000),
        )

    def _map_acceptance_to_qa(self, checks: List[str]) -> List[tuple]:
        """Mappe les critères d'acceptation aux outils QA"""
        qa_checks = []

        for check in checks:
            check_lower = check.lower()

            if "test" in check_lower or "pytest" in check_lower:
                qa_checks.append(("run_tests:backend", "run_tests", {"target": "backend"}))

            if "lint" in check_lower or "ruff" in check_lower:
                qa_checks.append(("run_lint:backend", "run_lint", {"target": "backend"}))

            if "format" in check_lower or "black" in check_lower:
                qa_checks.append(("run_format:backend", "run_format", {"target": "backend"}))

            if "build" in check_lower:
                qa_checks.append(("run_build:frontend", "run_build", {"target": "frontend"}))

            if "type" in check_lower or "mypy" in check_lower:
                qa_checks.append(("run_typecheck:backend", "run_typecheck", {"target": "backend"}))

        # Si aucun check spécifique, ajouter des checks par défaut
        if not qa_checks:
            qa_checks.append(("git_status", "git_status", {}))

        return qa_checks

    async def _repair(
        self,
        state: WorkflowState,
        verdict: JudgeVerdict,
        model: str,
        websocket: Optional[WebSocket],
    ) -> RepairAttempt:
        """Tente de réparer les problèmes identifiés"""

        last_tool = "unknown"
        if state.execution and state.execution.tools_used:
            last_tool = state.execution.tools_used[-1].tool

        repair_prompt = self.REPAIR_PROMPT.format(
            issues="\n".join(f"- {i}" for i in verdict.issues),
            fixes="\n".join(f"- {f}" for f in verdict.suggested_fixes),
            previous_response=state.execution.response[:500] if state.execution else "",
            last_tool=last_tool,
        )

        # Exécuter la réparation via ReAct
        result = await react_engine.run(
            user_message=repair_prompt, model=model, websocket=websocket
        )

        # Mettre à jour l'execution avec le résultat de réparation
        tools_used = []
        for t in result.get("tools_used", []):
            tools_used.append(
                ToolExecution(
                    tool=t.get("tool", "unknown"),
                    params=t.get("input", {}),
                    result=t.get("output", {}),
                    duration_ms=t.get("duration_ms", 0),
                )
            )

        # Mettre à jour la réponse
        if state.execution:
            state.execution.response = result.get("response", state.execution.response)
            state.execution.tools_used.extend(tools_used)

        return RepairAttempt(
            cycle=state.repair_cycles,
            issues_addressed=verdict.issues,
            changes_made=[f"Outil utilisé: {t.tool}" for t in tools_used],
            tools_used=tools_used,
        )

    def _build_response(
        self, state: WorkflowState, model: str, conversation_id: Optional[str]
    ) -> WorkflowResponse:
        """Construit la réponse finale"""

        tools_used = []
        if state.execution:
            for t in state.execution.tools_used:
                # NE PAS inclure les résultats bruts (output) pour éviter d'afficher du JSON
                # Le frontend n'a besoin que des noms des outils utilisés
                tools_used.append(
                    {
                        "tool": t.tool,
                        # "input": t.params,  # Commenté: pas nécessaire pour l'affichage
                        # "output": t.result,  # CRITIQUE: Ne JAMAIS envoyer ça au frontend
                        "duration_ms": t.duration_ms,
                    }
                )

        return WorkflowResponse(
            response=state.execution.response if state.execution else "Aucune réponse générée",
            conversation_id=conversation_id,
            model_used=model,
            tools_used=tools_used,
            iterations=state.execution.iterations if state.execution else 0,
            thinking=state.execution.thinking if state.execution else "",
            duration_ms=state.total_duration_ms,
            verification=state.verification,
            verdict=state.verdict,
            workflow_phase=state.phase,
            repair_cycles=state.repair_cycles,
        )


# Singleton
workflow_engine = WorkflowEngine()
