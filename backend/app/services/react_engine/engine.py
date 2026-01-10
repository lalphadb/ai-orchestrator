"""
ReAct Engine - Reason-Act-Observe Loop avec Streaming
Moteur principal pour l'exécution autonome de tâches
"""

import json
import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.ollama.client import ollama_client
from fastapi import WebSocket

from .tools import BUILTIN_TOOLS, RECOVERABLE_ERRORS, search_directory

logger = logging.getLogger(__name__)

# Erreurs qui déclenchent une recherche automatique
AUTO_RECOVERY_ERRORS = {"E_DIR_NOT_FOUND", "E_FILE_NOT_FOUND", "E_PATH_NOT_FOUND"}


class ReactEngine:
    """
    Moteur ReAct (Reason-Act-Observe) avec Streaming
    """

    SYSTEM_PROMPT = """Tu es un assistant IA. Tu dois répondre de manière concise et utile.

## Règles IMPORTANTES
1. Pour les questions simples (salutations, questions générales, conversations), réponds DIRECTEMENT sans utiliser d'outil
2. Utilise un outil UNIQUEMENT si l'utilisateur demande explicitement une action système
3. Après avoir utilisé un outil, réponds IMMÉDIATEMENT à l'utilisateur avec le résultat
4. NE JAMAIS enchaîner plus de 2-3 outils pour une même demande
5. Si tu as déjà les informations, réponds sans outil

## Outils Disponibles (utiliser avec parcimonie)
{tools}

## Format
Pour utiliser un outil:
```tool
{{"tool": "nom_outil", "params": {{"param1": "valeur"}}}}
```

Pour répondre à l'utilisateur:
```response
Ta réponse ici
```

## Exemples
- "Bonjour" → Réponds directement avec ```response```
- "Quelle heure est-il?" → Utilise get_datetime puis réponds
- "Comment ça va?" → Réponds directement
- "Montre les processus" → Utilise execute_command puis réponds
- "Est-ce que tout est à jour?" → Utilise UNE commande (apt list --upgradable) puis réponds

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

    async def _send_ws(self, ws: Optional[WebSocket], msg_type: str, data: Any):
        """Envoie un message WebSocket si disponible"""
        if ws:
            try:
                await ws.send_json(
                    {"type": msg_type, "data": data, "timestamp": datetime.utcnow().isoformat()}
                )
            except Exception as e:
                logger.warning(f"WS send failed: {e}")

    async def run(
        self,
        user_message: str,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        websocket: Optional[WebSocket] = None,
    ) -> Dict[str, Any]:
        """
        Exécute la boucle ReAct avec streaming
        """
        start_time = time.time()
        model = model or settings.DEFAULT_MODEL
        history = history or []

        system_prompt = self.SYSTEM_PROMPT.format(
            tools=self._build_tools_description(),
            datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        tools_used = []
        thinking_log = []
        current_prompt = user_message
        iteration = 0

        await self._send_ws(websocket, "thinking", {"message": "Analyse...", "iteration": 0})

        while iteration < self.max_iterations:
            iteration += 1

            # Mode streaming si WebSocket disponible
            if websocket:
                full_response = ""

                async for token in ollama_client.generate_stream(
                    prompt=current_prompt,
                    model=model,
                    system=system_prompt,
                ):
                    full_response += token
                    await self._send_ws(websocket, "token", token)

                response_text = full_response
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

                await self._send_ws(
                    websocket,
                    "complete",
                    {
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

                await self._send_ws(
                    websocket,
                    "tool",
                    {"tool": tool_name, "params": tool_params, "iteration": iteration},
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
                            await self._send_ws(
                                websocket,
                                "thinking",
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

                # Prompt suivant - forcer une réponse après l'outil
                current_prompt = f"""Résultat de {tool_name}:
```
{json.dumps(tool_result, ensure_ascii=False, indent=2)[:1500]}
```{recovery_hint}

MAINTENANT, réponds à l'utilisateur avec ces informations. Utilise ```response``` pour ta réponse finale."""

            else:
                # Type inconnu - traiter comme réponse
                duration = int((time.time() - start_time) * 1000)

                await self._send_ws(
                    websocket,
                    "complete",
                    {
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
