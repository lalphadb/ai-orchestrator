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

## INTERDICTIONS ABSOLUES - CRITIQUE
🚫 NE JAMAIS copier ou afficher de données JSON brutes dans ta réponse
🚫 NE JAMAIS afficher des objets {{"key": "value"}} dans ta réponse
🚫 NE JAMAIS afficher des listes d'objets [{{}}, {{}}, {{}}] dans ta réponse
✅ TOUJOURS reformuler les résultats en phrases naturelles et lisibles
✅ Exemple: "J'ai trouvé 50 fichiers dans le répertoire" au lieu de {{"files": [...]}}

## Outils Disponibles (utiliser avec parcimonie)
{tools}

## Format
Pour utiliser un outil:
```tool
{{"tool": "nom_outil", "params": {{"param1": "valeur"}}}}
```

Pour répondre à l'utilisateur:
```response
Ta réponse en langage naturel, JAMAIS en JSON
```

## Exemples de bonnes réponses
- "Bonjour" → "Bonjour ! Comment puis-je vous aider ?"
- Après list_directory → "J'ai trouvé 25 fichiers dans /var/log, notamment syslog, auth.log et kern.log"
- Après list_models → "Il y a 15 modèles LLM disponibles, dont llama3.2, deepseek-coder et qwen2.5"

Date actuelle: {datetime}
"""

    def __init__(self, tools=None):
        self.tools = tools or BUILTIN_TOOLS
        self.max_iterations = settings.MAX_ITERATIONS

    def _clean_tools_for_frontend(self, tools_used: List[Dict]) -> List[Dict]:
        """
        Nettoie les tools_used pour le frontend en supprimant les données JSON brutes.
        Le frontend n'a besoin que des noms des outils, pas des résultats complets.
        """
        cleaned = []
        for t in tools_used:
            cleaned.append(
                {
                    "tool": t.get("tool", "unknown"),
                    "duration_ms": t.get("duration_ms", 0),
                    # NE PAS inclure "input" ni "output" pour éviter d'afficher du JSON
                }
            )
        return cleaned

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

    def _format_tool_result_for_llm(self, tool_name: str, tool_result: Dict[str, Any]) -> str:
        """
        Formate le résultat d'un outil de manière lisible pour le LLM (sans JSON brut).
        CRITIQUE: Ne JAMAIS inclure de données JSON brutes, seulement du texte descriptif.
        """
        if not tool_result.get("success"):
            error_msg = tool_result.get("error", {}).get("message", "Erreur inconnue")
            return f"❌ Erreur: {error_msg}"

        data = tool_result.get("data", {})

        # === CAS SPÉCIFIQUES PAR OUTIL ===

        # list_directory: Lister les fichiers d'un répertoire
        if tool_name == "list_directory":
            path = data.get("path", "répertoire")
            entries = data.get("entries", [])
            if entries:
                # Limiter à 15 entrées pour éviter de surcharger
                entry_names = [e.get("name", str(e)) for e in entries[:15]]
                result = f"✅ Le répertoire '{path}' contient {len(entries)} éléments"
                if len(entries) <= 15:
                    result += f":\n  • " + "\n  • ".join(entry_names)
                else:
                    result += f" (affichage des 15 premiers):\n  • " + "\n  • ".join(entry_names)
                    result += f"\n  ... et {len(entries) - 15} autres"
                return result
            return f"✅ Le répertoire '{path}' est vide"

        # read_file: Lire un fichier
        if tool_name == "read_file":
            content = data.get("content", "")
            path = data.get("path", "fichier")
            lines = content.count("\n") + 1 if content else 0
            chars = len(content)
            return f"✅ Fichier '{path}' lu avec succès ({lines} lignes, {chars} caractères)"

        # list_llm_models: Lister les modèles LLM
        if tool_name == "list_llm_models":
            if isinstance(data, dict) and "models" in data:
                models = data.get("models", [])
                total = data.get("total", len(models))
                model_list = []
                for m in models[:10]:
                    name = m.get("name", "inconnu")
                    size_gb = m.get("size", 0) / (1024**3) if m.get("size", 0) > 0 else 0
                    model_list.append(f"  • {name} ({size_gb:.1f} GB)")
                result = f"✅ {total} modèles LLM disponibles"
                if model_list:
                    result += ":\n" + "\n".join(model_list)
                    if len(models) > 10:
                        result += f"\n  ... et {len(models) - 10} autres"
                return result
            return "✅ Modèles récupérés"

        # execute_command: Exécuter une commande système
        if tool_name == "execute_command" or "stdout" in data:
            stdout = data.get("stdout", "").strip()
            stderr = data.get("stderr", "").strip()
            if stderr:
                return f"⚠️ Commande exécutée avec avertissements:\n{stderr[:300]}"
            if stdout:
                # Limiter à 400 caractères
                return (
                    f"✅ Sortie de la commande:\n{stdout[:400]}{'...' if len(stdout) > 400 else ''}"
                )
            return "✅ Commande exécutée (aucune sortie)"

        # write_file: Écrire un fichier
        if tool_name == "write_file":
            path = data.get("path", "fichier")
            return f"✅ Fichier '{path}' créé/écrit avec succès"

        # search_files: Rechercher des fichiers
        if tool_name == "search_files":
            matches = data.get("matches", [])
            pattern = data.get("pattern", "")
            if matches:
                match_paths = [m.get("path", str(m)) for m in matches[:10]]
                result = f"✅ {len(matches)} fichier(s) trouvé(s) pour '{pattern}'"
                if len(matches) <= 10:
                    result += ":\n  • " + "\n  • ".join(match_paths)
                else:
                    result += f" (10 premiers):\n  • " + "\n  • ".join(match_paths)
                return result
            return f"❌ Aucun fichier trouvé pour le pattern '{pattern}'"

        # === CAS GÉNÉRIQUES ===

        # Compter les éléments selon les clés connues
        if isinstance(data, dict):
            for key in [
                "containers",
                "processes",
                "files",
                "entries",
                "items",
                "matches",
                "results",
            ]:
                if key in data:
                    items = data[key]
                    if isinstance(items, list):
                        count = len(items)
                        return f"✅ {count} {key} trouvé(s)"

        # Fallback ultra-minimal
        return f"✅ Outil '{tool_name}' exécuté avec succès"

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
        # MAIS nettoyer aggressivement tout JSON résiduel
        clean_text = re.sub(r"```\w*\n?", "", text)
        clean_text = clean_text.strip()

        # CRITIQUE: Supprimer les blocs JSON bruts qui peuvent traîner à la fin
        # Pattern 1: Objets JSON multi-lignes avec tool/output/data
        clean_text = re.sub(
            r'\n\s*\{\s*"(?:tool|output|data|success|error)"[\s\S]*?\}\s*$',
            "",
            clean_text,
            flags=re.MULTILINE,
        )

        # Pattern 2: Objets JSON compacts sur une seule ligne
        clean_text = re.sub(r'\n\s*\{["\w\s:,\[\]\{\}]+\}\s*$', "", clean_text)

        # Pattern 3: Retirer tout ce qui suit si on détecte un gros bloc JSON structuré
        # Chercher le dernier paragraphe de texte naturel avant du JSON
        json_start = re.search(r"\n\s*(\{[\s\S]{100,}\})\s*$", clean_text)
        if json_start:
            # Garder seulement ce qui précède le JSON
            clean_text = clean_text[: json_start.start()].strip()

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
                        "tools_used": self._clean_tools_for_frontend(tools_used),
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
                # Extraire uniquement les données pertinentes (pas le JSON brut complet)
                result_summary = self._format_tool_result_for_llm(tool_name, tool_result)

                current_prompt = f"""Résultat de l'outil {tool_name}:
{result_summary}{recovery_hint}

🚫 INTERDICTION ABSOLUE: NE copie PAS ce résultat tel quel. NE mets PAS de JSON dans ta réponse.
✅ OBLIGATION: Reformule ce résultat en phrases naturelles et lisibles pour l'utilisateur.

Utilise ```response``` avec ta réponse en langage naturel."""

            else:
                # Type inconnu - traiter comme réponse
                duration = int((time.time() - start_time) * 1000)

                await self._send_ws(
                    websocket,
                    "complete",
                    {
                        "response": parsed["data"] or response_text,
                        "tools_used": self._clean_tools_for_frontend(tools_used),
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
        logger.warning(
            f"Max iterations ({self.max_iterations}) reached, generating fallback response"
        )
        duration = int((time.time() - start_time) * 1000)
        last_tool_result = (
            tools_used[-1]["output"] if tools_used else {"success": False, "data": "Aucun résultat"}
        )

        # Formater SANS JSON brut - résumé lisible uniquement
        if tools_used and tools_used[-1].get("tool") == "list_llm_models":
            # Cas spécial: liste de modèles - formater en Markdown
            models_data = last_tool_result.get("data", {})
            if isinstance(models_data, dict) and "models" in models_data:
                total = models_data.get("total", len(models_data["models"]))
                models_list = models_data.get("models", [])

                # Construire une liste Markdown lisible
                model_lines = []
                for m in models_list[:20]:  # Limiter à 20 modèles
                    name = m.get("name", "inconnu")
                    size_bytes = m.get("size", 0)
                    size_gb = size_bytes / (1024**3) if size_bytes > 0 else 0
                    available = "✓" if m.get("available", True) else "✗"
                    model_lines.append(f"- **{name}** ({size_gb:.1f} GB) {available}")

                response_text = (
                    f"J'ai trouvé **{total} modèles LLM** disponibles :\n\n"
                    + "\n".join(model_lines)
                )
                if len(models_list) > 20:
                    response_text += f"\n\n_...et {len(models_list) - 20} autres modèles_"
            else:
                response_text = "Les modèles LLM ont été récupérés avec succès."
        elif last_tool_result.get("success"):
            # Résultat d'outil réussi - message simple
            tool_name = tools_used[-1].get("tool", "outil") if tools_used else "outil"
            data = last_tool_result.get("data", {})

            # Extraire un résumé selon le type de données
            if isinstance(data, dict):
                if "containers" in data:
                    count = len(data.get("containers", []))
                    response_text = f"L'outil `{tool_name}` a trouvé **{count} conteneurs** Docker."
                elif "processes" in data:
                    count = len(data.get("processes", []))
                    response_text = f"L'outil `{tool_name}` a listé **{count} processus**."
                elif "files" in data:
                    count = len(data.get("files", []))
                    response_text = f"L'outil `{tool_name}` a trouvé **{count} fichiers**."
                elif "stdout" in data:
                    # Résultat de commande
                    stdout = data.get("stdout", "").strip()
                    if stdout:
                        response_text = f"Résultat de la commande :\n\n```\n{stdout[:1500]}\n```"
                    else:
                        response_text = "Commande exécutée avec succès (aucune sortie)."
                else:
                    response_text = f"L'outil `{tool_name}` s'est exécuté avec succès."
            elif isinstance(data, list):
                response_text = f"L'outil `{tool_name}` a retourné **{len(data)} éléments**."
            else:
                response_text = f"L'outil `{tool_name}` s'est exécuté avec succès."
        else:
            # Erreur
            error_msg = last_tool_result.get("error", {}).get("message", "Erreur inconnue")
            response_text = f"Une erreur s'est produite: {error_msg}"

        # IMPORTANT: Envoyer l'événement complete via WebSocket
        await self._send_ws(
            websocket,
            "complete",
            {
                "response": response_text,
                "tools_used": self._clean_tools_for_frontend(tools_used),
                "iterations": iteration,
                "duration_ms": duration,
            },
        )

        return {
            "response": response_text,
            "model": model,
            "tools_used": tools_used,
            "iterations": iteration,
            "thinking": "\n".join(thinking_log),
            "duration_ms": duration,
        }


# Singleton
react_engine = ReactEngine()
