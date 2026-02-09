"""
Self-Improve Module - AI Orchestrator v8

Auto-amélioration contrôlée du système avec:
- Analyse des logs et feedback
- Génération de patches
- Validation QA obligatoire
- Rollback automatique en cas d'échec
- Stockage des améliorations dans PostgreSQL (pgvector)
"""

import json
import logging
import os
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.services.ollama.client import ollama_client
from app.services.react_engine.tools import (BUILTIN_TOOLS, ToolResult, fail,
                                             ok, read_file, write_file)
from app.services.react_engine.verifier import verifier_service

logger = logging.getLogger(__name__)


class SelfImproveResult:
    """Résultat d'une opération SELF_IMPROVE"""

    def __init__(self):
        self.run_id: str = str(uuid.uuid4())
        self.status: str = (
            "pending"  # pending, analyzing, patching, verifying, complete, failed, rolled_back
        )
        self.analysis: Dict[str, Any] = {}
        self.patches: List[Dict[str, Any]] = []
        self.qa_results: Dict[str, Any] = {}
        self.rollback_info: Optional[Dict[str, Any]] = None
        self.memory_id: Optional[str] = None
        self.error: Optional[str] = None
        self.started_at: datetime = datetime.now(timezone.utc)
        self.completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "analysis": self.analysis,
            "patches": self.patches,
            "qa_results": self.qa_results,
            "rollback_info": self.rollback_info,
            "memory_id": self.memory_id,
            "error": self.error,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class SelfImproveEngine:
    """
    Moteur d'auto-amélioration du système.

    Pipeline:
    1. ANALYZE: Analyse des logs, feedback, et métriques
    2. PATCH: Génération et application de patches
    3. VERIFY: Validation QA (tests, lint)
    4. STORE: Stockage dans PostgreSQL si succes
    5. ROLLBACK: Annulation si échec
    """

    # Tools autorisés pour SELF_IMPROVE (liste restrictive)
    ALLOWED_TOOLS = [
        "read_file",
        "write_file",
        "patch_file",
        "list_directory",
        "search_directory",
        "run_tests",
        "run_lint",
        "git_status",
        "git_diff",
        "git_log",
        "memory_store",
        "memory_search",
    ]

    ANALYSIS_PROMPT = """Analyse ces données pour identifier des améliorations potentielles.

Logs récents:
{logs}

Feedback utilisateur:
{feedback}

Métriques système:
{metrics}

Réponds avec ce JSON:
```json
{{
  "improvements": [
    {{
      "type": "bug_fix|optimization|feature|refactor",
      "priority": "high|medium|low",
      "description": "description claire",
      "files": ["fichier1.py", "fichier2.py"],
      "estimated_impact": "impact attendu"
    }}
  ],
  "no_action_reason": "raison si aucune amélioration nécessaire"
}}
```"""

    PATCH_PROMPT = """Génère un patch pour cette amélioration.

Amélioration:
{improvement}

Contenu actuel du fichier {file}:
```
{content}
```

Génère le code corrigé COMPLET. Réponds UNIQUEMENT avec le nouveau contenu du fichier, sans explication."""

    def __init__(self):
        self.workspace = Path(settings.WORKSPACE_DIR)
        self.backup_dir = self.workspace / ".self_improve_backups"
        self.backup_dir.mkdir(exist_ok=True)

    async def run(
        self,
        logs: Optional[List[str]] = None,
        feedback: Optional[List[Dict]] = None,
        metrics: Optional[Dict] = None,
        dry_run: bool = False,
    ) -> SelfImproveResult:
        """
        Exécute le pipeline SELF_IMPROVE.

        Args:
            logs: Logs récents à analyser
            feedback: Feedback utilisateur
            metrics: Métriques système
            dry_run: Si True, n'applique pas les patches

        Returns:
            SelfImproveResult avec le statut et les détails
        """
        result = SelfImproveResult()

        try:
            # PHASE 1: ANALYZE
            result.status = "analyzing"
            logger.info(f"[SELF_IMPROVE] Starting analysis run_id={result.run_id}")

            analysis = await self._analyze(logs, feedback, metrics)
            result.analysis = analysis

            if not analysis.get("improvements"):
                result.status = "complete"
                result.completed_at = datetime.now(timezone.utc)
                logger.info("[SELF_IMPROVE] No improvements needed")
                return result

            # PHASE 2: PATCH
            result.status = "patching"

            for improvement in analysis["improvements"]:
                if improvement["priority"] != "high":
                    continue  # Only process high priority in auto mode

                for file_path in improvement.get("files", []):
                    backup_path = await self._create_backup(file_path)

                    if not dry_run:
                        patch_result = await self._apply_patch(improvement, file_path)
                        result.patches.append(
                            {
                                "file": file_path,
                                "backup": str(backup_path),
                                "success": patch_result["success"],
                                "details": patch_result,
                            }
                        )

            # PHASE 3: VERIFY
            result.status = "verifying"

            qa_results = await self._run_qa()
            result.qa_results = qa_results

            if not qa_results.get("all_passed"):
                # ROLLBACK
                result.status = "rolling_back"
                rollback_result = await self._rollback(result.patches)
                result.rollback_info = rollback_result
                result.status = "rolled_back"
                result.error = "QA verification failed, changes rolled back"
                logger.warning(f"[SELF_IMPROVE] Rolled back due to QA failure")
            else:
                # PHASE 4: STORE in memory (PostgreSQL)
                result.status = "storing"

                memory_id = await self._store_in_memory(result)
                result.memory_id = memory_id
                result.status = "complete"
                logger.info(f"[SELF_IMPROVE] Success, stored as {memory_id}")

            result.completed_at = datetime.now(timezone.utc)
            return result

        except Exception as e:
            result.status = "failed"
            result.error = str(e)
            result.completed_at = datetime.now(timezone.utc)
            logger.error(f"[SELF_IMPROVE] Failed: {e}")

            # Attempt rollback on any failure
            if result.patches:
                try:
                    await self._rollback(result.patches)
                except Exception as rollback_error:
                    logger.error(f"[SELF_IMPROVE] Rollback also failed: {rollback_error}")

            return result

    async def _analyze(
        self,
        logs: Optional[List[str]],
        feedback: Optional[List[Dict]],
        metrics: Optional[Dict],
    ) -> Dict[str, Any]:
        """Analyse les données et identifie les améliorations."""
        prompt = self.ANALYSIS_PROMPT.format(
            logs=json.dumps(logs or [], indent=2),
            feedback=json.dumps(feedback or [], indent=2),
            metrics=json.dumps(metrics or {}, indent=2),
        )

        result = await ollama_client.generate(
            prompt=prompt,
            model=settings.JUDGE_MODEL,
            system="Tu es un analyste système expert. Identifie les améliorations prioritaires.",
        )

        try:
            # Extract JSON from response
            response_text = result.get("response", "")
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            else:
                json_str = response_text

            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            return {"improvements": [], "no_action_reason": "Could not parse analysis"}

    async def _create_backup(self, file_path: str) -> Path:
        """Crée une sauvegarde du fichier avant modification."""
        source = self.workspace / file_path
        if not source.exists():
            return None

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.replace('/', '_')}_{timestamp}.bak"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(source, backup_path)
        logger.info(f"[SELF_IMPROVE] Backup created: {backup_path}")

        return backup_path

    async def _apply_patch(self, improvement: Dict, file_path: str) -> Dict[str, Any]:
        """Génère et applique un patch pour un fichier."""
        full_path = self.workspace / file_path

        if not full_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        current_content = full_path.read_text()

        prompt = self.PATCH_PROMPT.format(
            improvement=json.dumps(improvement, indent=2),
            file=file_path,
            content=current_content[:10000],  # Limit content size
        )

        result = await ollama_client.generate(
            prompt=prompt,
            model=settings.EXECUTOR_MODEL,
            system="Tu es un développeur expert. Génère du code propre et testé.",
        )

        new_content = result.get("response", "").strip()

        # Remove markdown code blocks if present
        if new_content.startswith("```"):
            lines = new_content.split("\n")
            new_content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        if not new_content:
            return {"success": False, "error": "Empty patch generated"}

        # Apply patch
        try:
            full_path.write_text(new_content)
            return {"success": True, "file": file_path, "size": len(new_content)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _run_qa(self) -> Dict[str, Any]:
        """Exécute les outils QA pour valider les changements."""
        results = {
            "tests": None,
            "lint": None,
            "all_passed": True,
        }

        # Run tests
        test_result = await verifier_service.run_tests()
        results["tests"] = test_result
        if not test_result.get("success"):
            results["all_passed"] = False

        # Run lint
        lint_result = await verifier_service.run_lint()
        results["lint"] = lint_result
        if not lint_result.get("success"):
            results["all_passed"] = False

        return results

    async def _rollback(self, patches: List[Dict]) -> Dict[str, Any]:
        """Annule les patches en restaurant les backups."""
        restored = []
        failed = []

        for patch in patches:
            if not patch.get("backup"):
                continue

            backup_path = Path(patch["backup"])
            target_path = self.workspace / patch["file"]

            try:
                if backup_path.exists():
                    shutil.copy2(backup_path, target_path)
                    restored.append(patch["file"])
                    logger.info(f"[SELF_IMPROVE] Restored: {patch['file']}")
            except Exception as e:
                failed.append({"file": patch["file"], "error": str(e)})
                logger.error(f"[SELF_IMPROVE] Rollback failed for {patch['file']}: {e}")

        return {"restored": restored, "failed": failed}

    async def _store_in_memory(self, result: SelfImproveResult) -> Optional[str]:
        """Stocke le resume de l'amelioration dans la memoire PostgreSQL."""
        try:
            from app.services.react_engine.tools import memory_store

            summary = {
                "type": "self_improve",
                "run_id": result.run_id,
                "improvements": result.analysis.get("improvements", []),
                "patches_applied": len([p for p in result.patches if p.get("success")]),
                "qa_passed": result.qa_results.get("all_passed", False),
                "timestamp": result.started_at.isoformat(),
            }

            store_result = await memory_store(
                content=json.dumps(summary),
                topic="self_improve",
                tags=["auto", "improvement", result.status],
            )

            if store_result.get("success"):
                return store_result["data"].get("id")

            return None
        except Exception as e:
            logger.warning(f"[SELF_IMPROVE] Could not store in memory: {e}")
            return None


# Singleton instance
self_improve_engine = SelfImproveEngine()
