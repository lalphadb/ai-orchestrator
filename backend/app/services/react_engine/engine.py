"""
ReAct Engine - Reason-Act-Observe Loop avec Streaming
Moteur principal pour l'exécution autonome de tâches
"""

import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.ollama.client import ollama_client
from app.services.websocket.event_emitter import event_emitter
from fastapi import WebSocket

from .tools import BUILTIN_TOOLS, RECOVERABLE_ERRORS, search_directory

logger = logging.getLogger(__name__)

# Erreurs qui déclenchent une recherche automatique
AUTO_RECOVERY_ERRORS = {"E_DIR_NOT_FOUND", "E_FILE_NOT_FOUND", "E_PATH_NOT_FOUND"}


class ReactEngine:
    """
    Moteur ReAct (Reason-Act-Observe) avec Streaming
    """

    SYSTEM_PROMPT = """Tu es un assistant IA expert en développement, DevOps et administration système.
Tu fournis des réponses APPROFONDIES basées sur une analyse réelle, pas des réponses génériques.

## Contexte Infrastructure
Tu assistes l'administrateur d'un serveur Ubuntu avec:
- Stack Docker unifiée (/home/lalpha/projets/infrastructure/unified-stack/)
- Projets IA (/home/lalpha/projets/ai-tools/)
- Frontend AI Orchestrator (/home/lalpha/projets/ai-tools/ai-orchestrator/frontend/)
- Backend AI Orchestrator (/home/lalpha/projets/ai-tools/ai-orchestrator/backend/)

## Principes de Réponse
1. **Salutations simples** ("Bonjour", "Merci") → Réponds directement sans outil
2. **Questions factuelles sur le système** → Utilise les outils pour obtenir des données RÉELLES, puis analyse les résultats
3. **Demandes d'analyse/diagnostic** → Utilise PLUSIEURS outils pour investiguer en profondeur, croise les informations, puis fournis une analyse structurée
4. **Questions de conseil/amélioration** → Lis d'abord le code/la config concerné(e) avec les outils, PUIS donne des conseils basés sur l'état réel du projet
5. **Ne donne JAMAIS de réponse générique** quand tu peux vérifier la réalité avec un outil

## Méthodologie d'Analyse
- **Collecte**: Utilise autant d'outils que nécessaire pour rassembler les données pertinentes
- **Vérification**: Croise les résultats de plusieurs sources (fichiers, commandes, état système)
- **Analyse**: Interprète les données dans leur contexte, identifie patterns et anomalies
- **Recommandation**: Base tes suggestions sur les données collectées, pas sur des généralités

## Quand utiliser un outil
- Lister des fichiers/répertoires → list_directory
- Lire un fichier → read_file
- État système → get_system_info
- Exécuter une commande → execute_command
- Analyser du code → read_file sur les fichiers concernés
- Diagnostiquer → combiner get_system_info, execute_command, read_file
- Modèles LLM → list_llm_models

## Outils Disponibles
{tools}

## Format de Réponse
Pour utiliser un outil:
```tool
{{"tool": "nom_outil", "params": {{"param1": "valeur"}}}}
```

Pour répondre à l'utilisateur:
```response
Ta réponse détaillée et utile ici
```

## Exemples de Bonne Pratique
- "Quels fichiers dans le projet?" → ```tool``` list_directory, PUIS analyse la structure et explique l'organisation
- "Comment va le serveur?" → ```tool``` get_system_info, PUIS analyse CPU/mémoire/disque et signale les anomalies
- "Propose des améliorations pour mon frontend" → ```tool``` read_file sur package.json et les composants principaux, PUIS conseils basés sur le code réel
- "Analyse les logs d'erreur" → ```tool``` execute_command pour lire les logs, PUIS identifier les patterns d'erreurs

Date actuelle: {datetime}
"""

    def __init__(self, tools=None):
        self.tools = tools or BUILTIN_TOOLS
        self.max_iterations = settings.MAX_ITERATIONS

    def _build_tools_description(self) -> str:
        """Construit la description des outils pour le prompt"""
        tools_list = self.tools.list_tools()
        descriptions = []

        for tool in tools_list:
            params = tool.get("parameters", {})
            params_str = ", ".join(f"{k}: {v}" for k, v in params.items())
            descriptions.append(
                f"- **{tool['name']}**: {tool['description']}\n"
                f"  Paramètres: {params_str or 'aucun'}"
            )

        return "\n".join(descriptions)

    def _parse_response(self, text: str) -> Dict[str, Any]:
        """Parse la réponse du LLM pour extraire tool ou response"""

        # Chercher un bloc tool
        tool_match = re.search(r"```tool\s*\n?(.*?)\n?```", text, re.DOTALL)
        if tool_match:
            try:
                tool_data = json.loads(tool_match.group(1).strip())
                return {"type": "tool", "data": tool_data}
            except json.JSONDecodeError:
                pass

        # Chercher un bloc response
        response_match = re.search(r"```response\s*\n?(.*?)\n?```", text, re.DOTALL)
        if response_match:
            return {"type": "response", "data": response_match.group(1).strip()}

        # Si aucun bloc trouvé, considérer comme réponse directe
        clean_text = re.sub(r"```\w*\n?", "", text)
        clean_text = clean_text.strip()

        if clean_text:
            return {"type": "response", "data": clean_text}

        return {"type": "unknown", "data": text}

    async def run(
        self,
        user_message: str,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        websocket: Optional[WebSocket] = None,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Exécute la boucle ReAct avec streaming

        Args:
            user_message: User's message
            conversation_id: Conversation ID (optional)
            model: Model to use (default: DEFAULT_MODEL)
            history: Conversation history (optional)
            websocket: WebSocket for streaming (optional)
            run_id: Run identifier for WebSocket v8 (auto-generated if not provided)
        """
        start_time = time.time()
        model = model or settings.DEFAULT_MODEL
        history = history or []
        run_id = run_id or str(uuid.uuid4())[:8]

        system_prompt = self.SYSTEM_PROMPT.format(
            tools=self._build_tools_description(),
            datetime=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        )

        # === FIX: Construire le contexte conversationnel ===
        conversation_context = ""
        if history and len(history) > 0:
            # Prendre les 10 derniers messages pour le contexte
            recent_history = history[-10:]
            context_parts = []
            for msg in recent_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")[:500]  # Limiter la taille
                context_parts.append(f"[{role}]: {content}")
            conversation_context = (
                "\n\n=== Historique récent ===\n"
                + "\n".join(context_parts)
                + "\n=== Fin historique ===\n\n"
            )
            logger.debug(f"Context loaded: {len(recent_history)} messages")

        tools_used = []
        thinking_log = []
        current_prompt = conversation_context + user_message
        iteration = 0

        logger.info(
            f"[DEBUG ReactEngine] Run {run_id}: starting, model={model}, history_len={len(history)}"
        )

        if websocket:
            await event_emitter.emit(
                websocket, "thinking", run_id, {"message": "Analyse...", "iteration": 0}
            )

        while iteration < self.max_iterations:
            iteration += 1

            # Mode streaming si WebSocket disponible
            if websocket:
                full_response = ""

                logger.info(
                    f"[DEBUG ReactEngine] Run {run_id}: starting LLM stream (iteration {iteration})"
                )
                async for token in ollama_client.generate_stream(
                    prompt=current_prompt,
                    model=model,
                    system=system_prompt,
                ):
                    full_response += token
                    # Token streaming via event_emitter (v8 compliance: includes run_id)
                    try:
                        await event_emitter.emit(
                            websocket,
                            "tokens",
                            run_id,
                            {"content": token},
                            validate=False,  # Skip validation for high-frequency tokens
                        )
                    except Exception as e:
                        logger.warning(f"Token emit failed: {e}")

                response_text = full_response
                logger.info(
                    f"[DEBUG ReactEngine] Run {run_id}: LLM stream complete, response_len={len(full_response)}"
                )
                logger.info(
                    f"[DEBUG ReactEngine] Run {run_id}: response preview: {full_response[:200]}"
                )
            else:
                result = await ollama_client.generate(
                    prompt=current_prompt,
                    model=model,
                    system=system_prompt,
                )

                if "error" in result:
                    return {
                        "response": f"Erreur LLM: {result['error']}",
                        "model": model,
                        "tools_used": tools_used,
                        "iterations": iteration,
                        "thinking": "\n".join(thinking_log),
                        "duration_ms": 0,
                    }

                response_text = result.get("response", "")

            thinking_log.append(f"[{iteration}] {response_text[:300]}...")

            # Parser la réponse
            parsed = self._parse_response(response_text)

            if parsed["type"] == "response":
                duration = int((time.time() - start_time) * 1000)

                # Note: This is NOT a terminal event - workflow_engine handles terminals
                if websocket:
                    await event_emitter.emit(
                        websocket,
                        "thinking",
                        run_id,
                        {
                            "message": "Réponse générée",
                            "response": parsed["data"],
                            "tools_used": tools_used,
                            "iterations": iteration,
                            "duration_ms": duration,
                        },
                    )

                return {
                    "response": parsed["data"],
                    "model": model,
                    "tools_used": tools_used,
                    "iterations": iteration,
                    "thinking": "\n".join(thinking_log),
                    "duration_ms": duration,
                }

            elif parsed["type"] == "tool":
                tool_data = parsed["data"]
                tool_name = tool_data.get("tool")
                tool_params = tool_data.get("params", {})

                if websocket:
                    await event_emitter.emit(
                        websocket,
                        "tool",
                        run_id,
                        {
                            "tool": tool_name,
                            "status": "starting",
                            "params": tool_params,
                            "iteration": iteration,
                        },
                    )

                tool_start = time.time()
                tool_result = await self.tools.execute(tool_name, **tool_params)
                tool_duration = int((time.time() - tool_start) * 1000)

                tools_used.append(
                    {
                        "tool": tool_name,
                        "input": tool_params,
                        "output": tool_result,
                        "duration_ms": tool_duration,
                    }
                )

                thinking_log.append(f"[Tool] {tool_name}: {str(tool_result)[:200]}...")

                # === AUTO-RECOVERY pour erreurs récupérables ===
                recovery_hint = ""
                if not tool_result.get("success", True):
                    error_code = tool_result.get("error", {}).get("code", "")
                    if error_code in AUTO_RECOVERY_ERRORS:
                        # Tenter une recherche automatique
                        logger.info(f"Auto-recovery pour erreur {error_code}")

                        # Extraire le nom du chemin recherché
                        error_msg = tool_result.get("error", {}).get("message", "")
                        # Pattern: "Répertoire non trouvé: /path/to/dir"
                        path_match = re.search(r"[:/]\s*([^\s]+)$", error_msg)
                        search_name = None

                        if path_match:
                            full_path = path_match.group(1)
                            # Extraire le dernier segment du chemin
                            search_name = full_path.rstrip("/").split("/")[-1]

                        if search_name:
                            if websocket:
                                await event_emitter.emit(
                                    websocket,
                                    "thinking",
                                    run_id,
                                    {
                                        "message": f"Recherche automatique: {search_name}...",
                                        "iteration": iteration,
                                        "phase": "recovery",
                                    },
                                )

                            search_result = search_directory(name=search_name)

                            if (
                                search_result.get("success")
                                and search_result.get("data", {}).get("count", 0) > 0
                            ):
                                matches = search_result["data"]["matches"]
                                suggestion = search_result["data"].get("suggestion")

                                tools_used.append(
                                    {
                                        "tool": "search_directory",
                                        "input": {"name": search_name},
                                        "output": search_result,
                                        "duration_ms": 0,
                                        "auto_recovery": True,
                                    }
                                )

                                recovery_hint = f"""

**RÉCUPÉRATION AUTOMATIQUE**: Le chemin demandé n'existait pas, mais j'ai trouvé des alternatives:
- Suggestion: `{suggestion}`
- Autres correspondances: {[m['path'] for m in matches[:3]]}

Tu peux retenter avec le bon chemin."""

                # Prompt suivant - laisser le LLM décider s'il a besoin de plus d'info
                current_prompt = f"""Résultat de {tool_name}:
```
{json.dumps(tool_result, ensure_ascii=False, indent=2)[:1500]}
```{recovery_hint}

Analyse ce résultat. Si tu as besoin de plus d'informations pour répondre de manière complète et précise, utilise un autre outil avec ```tool```. Sinon, fournis ta réponse détaillée avec ```response```."""

            else:
                # Type inconnu - traiter comme réponse
                duration = int((time.time() - start_time) * 1000)

                if websocket:
                    await event_emitter.emit(
                        websocket,
                        "thinking",
                        run_id,
                        {
                            "message": "Réponse générée",
                            "response": parsed["data"] or response_text,
                            "tools_used": tools_used,
                            "iterations": iteration,
                            "duration_ms": duration,
                        },
                    )

                return {
                    "response": parsed["data"] or response_text,
                    "model": model,
                    "tools_used": tools_used,
                    "iterations": iteration,
                    "thinking": "\n".join(thinking_log),
                    "duration_ms": duration,
                }

        # Max iterations - forcer une réponse
        duration = int((time.time() - start_time) * 1000)
        last_tool_result = tools_used[-1]["output"] if tools_used else "Aucun résultat"

        return {
            "response": f"Voici les informations trouvées:\n{json.dumps(last_tool_result, ensure_ascii=False, indent=2)[:500]}",
            "model": model,
            "tools_used": tools_used,
            "iterations": iteration,
            "thinking": "\n".join(thinking_log),
            "duration_ms": duration,
        }


# Singleton
react_engine = ReactEngine()
