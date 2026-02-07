"""
Verifier Service - Second modèle LLM pour valider les résultats
AI Orchestrator v6.1

Rôle du Verifier:
- Critiquer le travail de l'Executor
- Exiger des preuves (outputs des outils QA)
- Émettre un verdict PASS/FAIL avec justification
"""
import json
import logging
from typing import Dict, Any, List, Optional

from app.core.config import settings
from app.services.ollama.client import ollama_client
from app.models.workflow import (
    JudgeVerdict,
    VerificationReport,
    ExecutionResult,
    TaskSpec,
)

logger = logging.getLogger(__name__)


class VerifierService:
    """
    Service de vérification utilisant un second modèle LLM.
    Le Verifier est critique et exige des preuves concrètes.
    """
    
    JUDGE_SYSTEM_PROMPT = """Tu es un Verifier critique et rigoureux. Ton rôle est de valider le travail d'un autre agent IA.

## Règles ABSOLUES
1. Tu DOIS voir des PREUVES CONCRÈTES (outputs d'outils de vérification) pour valider
2. Sans preuve, ton verdict est FAIL
3. Les déclarations de l'agent ne sont PAS des preuves
4. Seuls les outputs de: run_tests, run_lint, run_format, run_build, git_diff comptent comme preuves

## Critères de validation
- Tests: returncode=0 ET pas d'erreurs dans stderr
- Lint: returncode=0 (aucune erreur/warning)
- Build: returncode=0 (compilation réussie)
- Fichiers modifiés: git_diff montre les changements attendus

## Format de réponse OBLIGATOIRE (JSON)
```json
{
  "status": "PASS" ou "FAIL",
  "confidence": 0.0 à 1.0,
  "issues": ["liste des problèmes trouvés"],
  "suggested_fixes": ["corrections suggérées si FAIL"],
  "reasoning": "explication détaillée du verdict"
}
```

Réponds UNIQUEMENT avec ce JSON, sans texte autour."""

    SIMPLE_JUDGE_PROMPT = """Tu es un assistant de vérification. Analyse si la tâche est bien accomplie.

Réponds UNIQUEMENT avec ce JSON:
```json
{
  "status": "PASS" ou "FAIL",
  "confidence": 0.0 à 1.0,
  "issues": [],
  "suggested_fixes": [],
  "reasoning": "ton analyse"
}
```"""

    def __init__(self):
        self.model = settings.VERIFIER_MODEL
    
    async def judge(
        self,
        original_request: str,
        spec: Optional[TaskSpec],
        execution: ExecutionResult,
        verification: VerificationReport,
    ) -> JudgeVerdict:
        """
        Émet un verdict sur le travail accompli.
        
        Args:
            original_request: La demande originale de l'utilisateur
            spec: La spécification de la tâche (si générée)
            execution: Le résultat de l'exécution ReAct
            verification: Le rapport de vérification QA
        
        Returns:
            JudgeVerdict avec status PASS/FAIL
        """
        
        # Construire le prompt de jugement
        prompt = self._build_judge_prompt(
            original_request, spec, execution, verification
        )
        
        try:
            # Appeler le modèle Verifier
            response = await ollama_client.chat(
                messages=[
                    {"role": "system", "content": self.JUDGE_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                options={"temperature": 0.1, "num_ctx": 8192}  # Température basse pour être déterministe
            )
            
            if "error" in response:
                logger.error(f"Verifier LLM error: {response['error']}")
                # En cas d'erreur, se baser sur les résultats QA uniquement
                return self._fallback_verdict(verification)
            
            # Extraire la réponse
            content = response.get("message", {}).get("content", "")
            
            # Parser le JSON
            verdict = self._parse_verdict(content)
            
            logger.info(f"Verifier verdict: {verdict.status} (confidence: {verdict.confidence})")
            return verdict
            
        except Exception as e:
            logger.error(f"Verifier failed: {e}")
            return self._fallback_verdict(verification)
    
    def _build_judge_prompt(
        self,
        original_request: str,
        spec: Optional[TaskSpec],
        execution: ExecutionResult,
        verification: VerificationReport,
    ) -> str:
        """Construit le prompt pour le Verifier"""
        
        parts = []
        
        parts.append(f"## Demande originale\n{original_request}")
        
        if spec:
            parts.append(f"""
## Spécification acceptée
- Objectif: {spec.objective}
- Critères d'acceptation: {', '.join(spec.acceptance.checks)}
""")
        
        parts.append(f"""
## Réponse de l'Executor
{execution.response[:2000]}

## Outils utilisés ({len(execution.tools_used)})
""")
        
        for tool in execution.tools_used[-5:]:  # Derniers 5 outils
            tool_dict = tool.model_dump() if hasattr(tool, 'model_dump') else tool
            parts.append(f"- {tool_dict.get('tool', 'unknown')}: {str(tool_dict.get('result', {}))[:300]}")
        
        parts.append(f"""
## Rapport de vérification QA
- Passed: {verification.passed}
- Checks exécutés: {', '.join(verification.checks_run)}
- Échecs: {', '.join(verification.failures) if verification.failures else 'Aucun'}
""")
        
        # Ajouter les preuves détaillées
        if verification.evidence:
            parts.append("## Preuves (outputs des outils)")
            for check_name, evidence in verification.evidence.items():
                if isinstance(evidence, dict):
                    stdout = evidence.get("stdout", "")[:500]
                    returncode = evidence.get("returncode", "?")
                    parts.append(f"### {check_name} (code={returncode})\n```\n{stdout}\n```")
        
        parts.append("""
## Ta tâche
Analyse les preuves ci-dessus et émets ton verdict JSON.
- Si TOUS les checks QA sont PASS avec preuves → PASS
- Si au moins un check FAIL ou manque de preuve → FAIL
""")
        
        return "\n".join(parts)
    
    def _parse_verdict(self, content: str) -> JudgeVerdict:
        """Parse la réponse JSON du Verifier"""
        
        # Extraire le JSON du contenu
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1)
        else:
            # Essayer de parser directement
            json_str = content.strip()
        
        try:
            data = json.loads(json_str)
            
            return JudgeVerdict(
                status=data.get("status", "FAIL"),
                confidence=float(data.get("confidence", 0.5)),
                issues=data.get("issues", []),
                suggested_fixes=data.get("suggested_fixes", []),
                reasoning=data.get("reasoning", "")
            )
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Verifier JSON: {e}")
            # Heuristique: chercher PASS/FAIL dans le texte
            if "PASS" in content.upper() and "FAIL" not in content.upper():
                return JudgeVerdict(
                    status="PASS",
                    confidence=0.6,
                    reasoning=content[:500]
                )
            return JudgeVerdict(
                status="FAIL",
                confidence=0.5,
                issues=["Impossible de parser la réponse du Verifier"],
                reasoning=content[:500]
            )
    
    def _fallback_verdict(self, verification: VerificationReport) -> JudgeVerdict:
        """Verdict de fallback basé uniquement sur les résultats QA"""
        
        if verification.passed:
            return JudgeVerdict(
                status="PASS",
                confidence=0.8,
                reasoning="Basé uniquement sur les résultats QA (Verifier LLM indisponible)"
            )
        else:
            return JudgeVerdict(
                status="FAIL",
                confidence=0.9,
                issues=verification.failures,
                suggested_fixes=["Corriger les échecs QA identifiés"],
                reasoning=f"Échecs QA: {', '.join(verification.failures)}"
            )
    
    async def quick_check(
        self,
        response: str,
        tools_used: List[Dict[str, Any]],
    ) -> JudgeVerdict:
        """
        Vérification rapide pour les réponses conversationnelles.
        Utilisé quand VERIFY_REQUIRED=False ou pour les questions simples.
        """
        
        # Si aucun outil utilisé, c'est une réponse conversationnelle → PASS
        if not tools_used:
            return JudgeVerdict(
                status="PASS",
                confidence=1.0,
                reasoning="Réponse conversationnelle sans modification système"
            )
        
        # Vérifier si des outils critiques ont été utilisés
        critical_tools = {"write_file", "execute_command"}
        used_critical = any(
            t.get("tool") in critical_tools for t in tools_used
        )
        
        if not used_critical:
            return JudgeVerdict(
                status="PASS",
                confidence=0.9,
                reasoning="Aucun outil critique utilisé"
            )
        
        # Pour les outils critiques, vérifier les résultats
        failures = []
        for tool in tools_used:
            result = tool.get("output", {}) or tool.get("result", {})
            if isinstance(result, dict):
                if not result.get("success", True):
                    error = result.get("error", {})
                    if isinstance(error, dict):
                        failures.append(f"{tool.get('tool')}: {error.get('message', 'erreur')}")
                    else:
                        failures.append(f"{tool.get('tool')}: {error}")
        
        if failures:
            return JudgeVerdict(
                status="FAIL",
                confidence=0.95,
                issues=failures,
                reasoning=f"Certains outils ont échoué: {', '.join(failures)}"
            )
        
        return JudgeVerdict(
            status="PASS",
            confidence=0.85,
            reasoning="Tous les outils critiques ont réussi"
        )


# Singleton
verifier_service = VerifierService()
