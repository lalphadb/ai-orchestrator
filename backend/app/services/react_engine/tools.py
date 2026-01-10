"""
Tools Registry - Outils sécurisés pour le ReAct Engine
AI Orchestrator v6.1 - Pipeline Spec/Plan/Execute/Verify/Repair

Contrat uniforme ToolResult:
- success: bool
- data: dict | null
- error: dict | null
- meta: dict (duration_ms, etc.)
"""

import asyncio
import re
import logging
import os
import shlex
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypedDict

from app.core.config import settings
from app.services.react_engine.secure_executor import secure_executor, ExecutionRole
from app.services.react_engine.governance import governance_manager, ActionCategory
from app.services.react_engine.memory import durable_memory, MemoryCategory
from app.services.react_engine.runbooks import runbook_registry, RunbookCategory

# ===== SECURITY PATTERNS (AUDIT 2026-01-09) =====
DANGEROUS_PATTERNS = [
    r'\$\(',           # $(command)
    r'`[^`]+`',        # `command`
    r'\$\{[^}]+\}',    # ${var}
    r'>\s*/etc', r'>>\s*/etc',
    r'>\s*/root', r'>\s*/home', r'>\s*/var',
    r'\|\s*(bash|sh|zsh|ksh)',
    r';\s*(bash|sh|rm|chmod|chown)',
    r'&&\s*(bash|sh|rm|chmod|chown)',
    r'base64\s+-d', r'base64\s+--decode',
]


def contains_dangerous_patterns(command: str) -> tuple[bool, str]:
    """Vérifie si la commande contient des patterns dangereux"""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, f"Pattern dangereux détecté"
    return False, ""


def contains_dangerous_arguments(command: str) -> tuple[bool, str]:
    """Vérifie si la commande contient des arguments dangereux"""
    dangerous_args = getattr(settings, 'DANGEROUS_ARGUMENTS', [
        "-c", "--command", "-e", "--eval", "--exec",
        "| bash", "| sh", "git push", "git commit",
    ])
    for arg in dangerous_args:
        if arg.lower() in command.lower():
            return True, f"Argument dangereux: {arg}"
    return False, ""

logger = logging.getLogger(__name__)


# ===== ERROR CLASSIFICATION =====

# Erreurs récupérables - le système peut tenter un plan B
RECOVERABLE_ERRORS = {
    "E_FILE_NOT_FOUND",
    "E_DIR_NOT_FOUND",
    "E_PATH_NOT_FOUND",
}

# Erreurs non récupérables - arrêt immédiat
FATAL_ERRORS = {
    "E_PERMISSION",
    "E_CMD_NOT_ALLOWED",
    "E_PATH_FORBIDDEN",
    "E_WRITE_DISABLED",
}


def is_recoverable_error(error_code: str) -> bool:
    """Vérifie si une erreur est récupérable"""
    return error_code in RECOVERABLE_ERRORS


# ===== TOOL RESULT CONTRACT =====


class ToolError(TypedDict):
    code: str
    message: str
    recoverable: bool  # Indique si l'erreur peut être récupérée


class ToolMeta(TypedDict, total=False):
    duration_ms: int
    command: str
    sandbox: bool


class ToolResult(TypedDict):
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[ToolError]
    meta: ToolMeta


def ok(data: Dict[str, Any], **meta_extra) -> ToolResult:
    """Retourne un résultat de succès standardisé"""
    return {"success": True, "data": data, "error": None, "meta": {"duration_ms": 0, **meta_extra}}


def fail(code: str, message: str, **meta_extra) -> ToolResult:
    """Retourne un résultat d'erreur standardisé avec indication de récupérabilité"""
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "recoverable": is_recoverable_error(code),
        },
        "meta": {"duration_ms": 0, **meta_extra},
    }


def with_timing(func):
    """Decorator pour mesurer le temps d'exécution"""

    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = (
            await func(*args, **kwargs)
            if asyncio.iscoroutinefunction(func)
            else func(*args, **kwargs)
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        if isinstance(result, dict) and "meta" in result:
            result["meta"]["duration_ms"] = elapsed_ms
        return result

    return wrapper


# ===== SECURITY HELPERS =====


def is_command_allowed(command: str) -> tuple[bool, str]:
    """Vérifie si la commande est autorisée (allowlist)"""
    try:
        tokens = shlex.split(command)
        if not tokens:
            return False, "Commande vide"

        cmd0 = tokens[0]
        # Extraire le binaire (sans chemin)
        binary = os.path.basename(cmd0)

        # Vérifier blocklist d'abord
        if binary in settings.COMMAND_BLOCKLIST:
            return False, f"Commande interdite (blocklist): {binary}"

        # Vérifier allowlist
        if binary not in settings.COMMAND_ALLOWLIST:
            return (
                False,
                f"Commande non autorisée: {binary}. Allowlist: {', '.join(settings.COMMAND_ALLOWLIST[:10])}...",
            )

        return True, ""
    except ValueError as e:
        return False, f"Erreur parsing commande: {e}"


def is_path_in_workspace(path: str) -> tuple[bool, str]:
    """Vérifie si le chemin est dans le workspace autorisé"""
    try:
        target = Path(path).resolve()
        workspace = Path(settings.WORKSPACE_DIR).resolve()

        # Le chemin doit être sous le workspace
        if not str(target).startswith(str(workspace) + os.sep) and target != workspace:
            return False, f"Chemin hors workspace: {target}. Workspace: {workspace}"

        return True, ""
    except Exception as e:
        return False, f"Erreur validation chemin: {e}"


# ===== TOOL REGISTRY =====


class ToolRegistry:
    """Registre des outils disponibles"""

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        func: Callable,
        description: str,
        category: str = "general",
        parameters: Optional[Dict[str, Any]] = None,
    ):
        """Enregistre un nouvel outil"""
        self.tools[name] = {
            "name": name,
            "func": func,
            "description": description,
            "category": category,
            "parameters": parameters or {},
            "usage_count": 0,
        }

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        """Récupère un outil"""
        return self.tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Liste tous les outils"""
        return [
            {
                "id": name,
                "name": tool["name"],
                "description": tool["description"],
                "category": tool["category"],
                "parameters": tool["parameters"],
            }
            for name, tool in self.tools.items()
        ]

    def get_categories(self) -> List[str]:
        """Liste les catégories"""
        return list(set(t["category"] for t in self.tools.values()))

    async def execute(self, name: str, **kwargs) -> ToolResult:
        """Exécute un outil"""
        tool = self.get(name)
        if not tool:
            return fail("E_TOOL_NOT_FOUND", f"Outil '{name}' non trouvé")

        try:
            tool["usage_count"] += 1
            func = tool["func"]

            start = time.perf_counter()
            if asyncio.iscoroutinefunction(func):
                result = await func(**kwargs)
            else:
                result = func(**kwargs)
            elapsed_ms = int((time.perf_counter() - start) * 1000)

            # Assurer le format ToolResult
            if isinstance(result, dict) and "success" in result:
                result["meta"]["duration_ms"] = elapsed_ms
                return result
            else:
                # Legacy format - convertir
                return ok(result, duration_ms=elapsed_ms)

        except Exception as e:
            logger.error(f"Tool execution error ({name}): {e}")
            return fail("E_TOOL_EXEC", str(e))


# ===== BUILTIN TOOLS =====


async def execute_command(command: str, timeout: int = 30, role: str = "operator") -> ToolResult:
    """
    Exécute une commande de manière SÉCURISÉE via SecureExecutor v7.

    SÉCURITÉ:
    - JAMAIS de shell=True
    - Parsing argv strict
    - Allowlist de commandes
    - Audit complet

    Args:
        command: Commande à exécuter
        timeout: Timeout en secondes (défaut 30)
        role: Rôle d'exécution (viewer, operator, admin)
    """
    # Convertir le rôle string en enum
    role_map = {
        "viewer": ExecutionRole.VIEWER,
        "operator": ExecutionRole.OPERATOR,
        "admin": ExecutionRole.ADMIN,
    }
    exec_role = role_map.get(role.lower(), ExecutionRole.OPERATOR)

    # Utiliser le SecureExecutor (JAMAIS shell=True)
    result = await secure_executor.execute(
        command=command,
        role=exec_role,
        timeout=timeout,
        cwd=settings.WORKSPACE_DIR
    )

    # Convertir en ToolResult pour compatibilité
    if result.success:
        return ok(
            {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            },
            command=command,
            sandbox=False,
        )
    else:
        return fail(
            result.error_code or "E_CMD_ERROR",
            result.error_message or "Erreur inconnue",
            command=command,
        )


def get_audit_log(last_n: int = 20) -> ToolResult:
    """
    Récupère les dernières entrées d'audit des commandes exécutées.
    
    Args:
        last_n: Nombre d'entrées à récupérer (défaut 20)
    """
    try:
        log = secure_executor.get_audit_log(last_n=last_n)
        return ok({
            "entries": log,
            "count": len(log),
        })
    except Exception as e:
        return fail("E_AUDIT_ERROR", str(e))


def read_file(path: str) -> ToolResult:
    """Lit le contenu d'un fichier"""
    try:
        # Résoudre le chemin (relatif au workspace si pas absolu)
        if not os.path.isabs(path):
            path = os.path.join(settings.WORKSPACE_DIR, path)

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return ok(
            {
                "content": content,
                "path": path,
                "size": len(content),
                "lines": content.count("\n") + 1,
            }
        )
    except FileNotFoundError:
        return fail("E_FILE_NOT_FOUND", f"Fichier non trouvé: {path}")
    except PermissionError:
        return fail("E_PERMISSION", f"Permission refusée: {path}")
    except Exception as e:
        return fail("E_READ_ERROR", str(e))


def write_file(path: str, content: str, append: bool = False) -> ToolResult:
    """
    Écrit dans un fichier.
    SÉCURITÉ: Écriture limitée au WORKSPACE_DIR uniquement.
    """
    # Résoudre le chemin
    if not os.path.isabs(path):
        path = os.path.join(settings.WORKSPACE_DIR, path)

    # Vérifier que le chemin est dans le workspace
    allowed, reason = is_path_in_workspace(path)
    if not allowed:
        return fail("E_PATH_FORBIDDEN", reason)

    if not settings.WORKSPACE_ALLOW_WRITE:
        return fail("E_WRITE_DISABLED", "Écriture désactivée dans la configuration")

    try:
        # Créer les répertoires parents si nécessaire
        os.makedirs(os.path.dirname(path), exist_ok=True)

        mode = "a" if append else "w"
        with open(path, mode, encoding="utf-8") as f:
            f.write(content)

        return ok({"path": path, "size": len(content), "mode": "append" if append else "write"})
    except PermissionError:
        return fail("E_PERMISSION", f"Permission refusée: {path}")
    except Exception as e:
        return fail("E_WRITE_ERROR", str(e))


def list_directory(path: str = ".") -> ToolResult:
    """Liste le contenu d'un répertoire"""
    try:
        if not os.path.isabs(path):
            path = os.path.join(settings.WORKSPACE_DIR, path)

        entries = []
        for entry in os.scandir(path):
            entries.append(
                {
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "size": entry.stat().st_size if entry.is_file() else 0,
                }
            )

        return ok({"path": path, "entries": entries, "count": len(entries)})
    except FileNotFoundError:
        return fail("E_DIR_NOT_FOUND", f"Répertoire non trouvé: {path}")
    except Exception as e:
        return fail("E_LIST_ERROR", str(e))


def get_system_info() -> ToolResult:
    """Informations système"""
    import platform

    try:
        import psutil

        return ok(
            {
                "os": platform.system(),
                "release": platform.release(),
                "hostname": platform.node(),
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "memory_used_percent": psutil.virtual_memory().percent,
                "disk_usage_percent": psutil.disk_usage("/").percent,
                "workspace": settings.WORKSPACE_DIR,
                "execute_mode": settings.EXECUTE_MODE,
            }
        )
    except ImportError:
        return ok(
            {
                "os": platform.system(),
                "release": platform.release(),
                "hostname": platform.node(),
                "workspace": settings.WORKSPACE_DIR,
                "execute_mode": settings.EXECUTE_MODE,
            }
        )


def get_datetime() -> ToolResult:
    """Date et heure actuelles"""
    now = datetime.now()
    return ok(
        {
            "datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "timestamp": int(now.timestamp()),
        }
    )


def calculate(expression: str) -> ToolResult:
    """Évalue une expression mathématique (sécurisé)"""
    try:
        import ast
        import operator

        # Opérateurs autorisés
        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }

        def eval_expr(node):
            if isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.BinOp):
                return ops[type(node.op)](eval_expr(node.left), eval_expr(node.right))
            elif isinstance(node, ast.UnaryOp):
                return ops[type(node.op)](eval_expr(node.operand))
            else:
                raise ValueError(f"Opération non supportée: {type(node)}")

        tree = ast.parse(expression, mode="eval")
        result = eval_expr(tree.body)

        return ok({"expression": expression, "result": result})
    except Exception as e:
        return fail("E_CALC_ERROR", str(e))


async def http_request(url: str, method: str = "GET", data: Optional[Dict] = None) -> ToolResult:
    """Effectue une requête HTTP"""
    try:
        import httpx
    except ImportError:
        return fail("E_IMPORT", "httpx non installé")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(url)
            elif method.upper() == "POST":
                response = await client.post(url, json=data)
            else:
                return fail("E_HTTP_METHOD", f"Méthode non supportée: {method}")

            return ok(
                {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.text[:10000],
                }
            )
    except httpx.TimeoutException:
        return fail("E_HTTP_TIMEOUT", "Timeout HTTP")
    except Exception as e:
        return fail("E_HTTP_ERROR", str(e))


def search_files(pattern: str, path: str = ".") -> ToolResult:
    """Recherche des fichiers par pattern"""
    import glob

    try:
        if not os.path.isabs(path):
            path = os.path.join(settings.WORKSPACE_DIR, path)

        matches = glob.glob(os.path.join(path, "**", pattern), recursive=True)
        return ok(
            {"pattern": pattern, "path": path, "matches": matches[:100], "count": len(matches)}
        )
    except Exception as e:
        return fail("E_SEARCH_ERROR", str(e))


# ===== RECOVERY TOOLS (v6.2) =====

# Bases allowlistées pour la recherche de répertoires
SEARCH_ALLOWED_BASES = [
    "/home",
    "/workspace",
    "/tmp",
    "/var/www",
    "/opt",
    settings.WORKSPACE_DIR,
]

# Profondeur et limite maximales
SEARCH_MAX_DEPTH = 3
SEARCH_MAX_RESULTS = 5


def search_directory(name: str, base: str = None, max_depth: int = SEARCH_MAX_DEPTH) -> ToolResult:
    """
    Recherche sécurisée de répertoires.
    Utilisé automatiquement en cas d'erreur E_DIR_NOT_FOUND pour tenter une récupération.

    SÉCURITÉ:
    - Base allowlistée uniquement
    - Profondeur limitée (défaut: 3)
    - Nombre de résultats limité (5)
    - Pas de scan global illimité

    Args:
        name: Nom du répertoire à chercher (exact ou partiel)
        base: Répertoire de base (défaut: WORKSPACE_DIR, doit être dans l'allowlist)
        max_depth: Profondeur maximale de recherche (max: 3)

    Returns:
        ToolResult avec la liste des répertoires trouvés
    """
    # Valider et définir la base
    if base is None:
        base = settings.WORKSPACE_DIR

    # Résoudre le chemin
    try:
        base_resolved = str(Path(base).resolve())
    except Exception:
        return fail("E_INVALID_PATH", f"Chemin invalide: {base}")

    # Vérifier que la base est dans l'allowlist
    base_allowed = False
    for allowed_base in SEARCH_ALLOWED_BASES:
        try:
            allowed_resolved = str(Path(allowed_base).resolve())
            if base_resolved.startswith(allowed_resolved) or base_resolved == allowed_resolved:
                base_allowed = True
                break
        except Exception:
            continue

    if not base_allowed:
        return fail(
            "E_BASE_NOT_ALLOWED",
            f"Base non autorisée: {base}. Bases autorisées: {', '.join(SEARCH_ALLOWED_BASES[:3])}...",
        )

    # Limiter la profondeur
    max_depth = min(max_depth, SEARCH_MAX_DEPTH)

    # Vérifier que la base existe
    if not os.path.isdir(base_resolved):
        return fail("E_BASE_NOT_FOUND", f"Répertoire de base non trouvé: {base_resolved}")

    # Rechercher les répertoires
    matches = []
    name_lower = name.lower()

    def search_recursive(current_path: str, current_depth: int):
        if current_depth > max_depth or len(matches) >= SEARCH_MAX_RESULTS:
            return

        try:
            for entry in os.scandir(current_path):
                if len(matches) >= SEARCH_MAX_RESULTS:
                    return

                try:
                    if entry.is_dir(follow_symlinks=False):
                        entry_name = entry.name.lower()

                        # Match exact ou partiel
                        if name_lower == entry_name or name_lower in entry_name:
                            matches.append(
                                {
                                    "path": entry.path,
                                    "name": entry.name,
                                    "depth": current_depth,
                                }
                            )

                        # Continuer la recherche dans les sous-répertoires
                        if current_depth < max_depth:
                            search_recursive(entry.path, current_depth + 1)
                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError):
            pass

    search_recursive(base_resolved, 0)

    if matches:
        return ok(
            {
                "query": name,
                "base": base_resolved,
                "max_depth": max_depth,
                "matches": matches,
                "count": len(matches),
                "suggestion": matches[0]["path"] if matches else None,
            }
        )
    else:
        return ok(
            {
                "query": name,
                "base": base_resolved,
                "max_depth": max_depth,
                "matches": [],
                "count": 0,
                "suggestion": None,
            }
        )


# ===== LLM MODELS TOOL =====


async def list_llm_models() -> ToolResult:
    """
    Liste les modèles LLM disponibles via Ollama.
    Retourne une réponse formatée et structurée pour l'affichage.
    """
    try:
        import httpx
        from app.core.config import settings

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")

            if response.status_code != 200:
                return fail("E_OLLAMA_ERROR", f"Erreur Ollama: HTTP {response.status_code}")

            data = response.json()
            models = data.get("models", [])

            # Catégoriser les modèles
            categories = {
                "general": [],
                "code": [],
                "vision": [],
                "embedding": [],
                "safety": [],
                "cloud": [],
            }

            for model in models:
                name = model.get("name", "").lower()
                size = model.get("size", 0)

                model_info = {
                    "name": model.get("name"),
                    "size": size,
                    "modified_at": model.get("modified_at"),
                    "available": True,
                }

                # Classification
                if size < 1000 or "cloud" in name or "gemini" in name or "kimi" in name:
                    categories["cloud"].append(model_info)
                elif "embed" in name or "nomic" in name or "bge" in name or "mxbai" in name:
                    categories["embedding"].append(model_info)
                elif "vision" in name or "-vl" in name or "vl:" in name:
                    categories["vision"].append(model_info)
                elif "coder" in name or "code" in name or "deepseek" in name:
                    categories["code"].append(model_info)
                elif "safeguard" in name or "guard" in name or "safety" in name:
                    categories["safety"].append(model_info)
                else:
                    categories["general"].append(model_info)

            # Statistiques
            total = len(models)
            local_count = sum(1 for m in models if m.get("size", 0) > 1000)
            cloud_count = sum(1 for m in models if m.get("size", 0) < 1000)
            total_size = sum(m.get("size", 0) for m in models)

            return ok(
                {
                    "total": total,
                    "local_count": local_count,
                    "cloud_count": cloud_count,
                    "total_size_gb": round(total_size / (1024**3), 1),
                    "categories": {k: v for k, v in categories.items() if v},
                    "models": models,
                }
            )

    except ImportError:
        return fail("E_IMPORT", "httpx non installé")
    except Exception as e:
        return fail("E_MODELS_ERROR", str(e))


# ===== QA TOOLS (v6.1) =====


async def git_status() -> ToolResult:
    """Affiche le statut Git du workspace"""
    return await execute_command("git status --porcelain", timeout=10)


async def git_diff(staged: bool = False) -> ToolResult:
    """Affiche les différences Git"""
    cmd = "git diff --staged" if staged else "git diff"
    return await execute_command(cmd, timeout=30)


async def run_tests(target: str = "backend") -> ToolResult:
    """
    Exécute les tests.
    target: backend | frontend | all
    """
    commands = {
        "backend": "python3 -m pytest -q --tb=short",
        "frontend": "npm run test --if-present",
        "all": "python3 -m pytest -q --tb=short && npm run test --if-present",
    }

    if target not in commands:
        return fail(
            "E_INVALID_TARGET", f"Target invalide: {target}. Utiliser: backend, frontend, all"
        )

    return await execute_command(commands[target], timeout=120)


async def run_lint(target: str = "backend") -> ToolResult:
    """
    Exécute le linter.
    target: backend | frontend | all
    """
    commands = {
        "backend": "ruff check . --output-format=concise",
        "frontend": "npm run lint --if-present",
        "all": "ruff check . --output-format=concise; npm run lint --if-present",
    }

    if target not in commands:
        return fail("E_INVALID_TARGET", f"Target invalide: {target}")

    return await execute_command(commands[target], timeout=60)


async def run_format(target: str = "backend", check_only: bool = True) -> ToolResult:
    """
    Exécute le formateur de code.
    target: backend | frontend | all
    check_only: si True, vérifie seulement sans modifier
    """
    if check_only:
        commands = {
            "backend": "black . --check --diff",
            "frontend": "npm run format:check --if-present",
            "all": "black . --check --diff; npm run format:check --if-present",
        }
    else:
        commands = {
            "backend": "black .",
            "frontend": "npm run format --if-present",
            "all": "black .; npm run format --if-present",
        }

    if target not in commands:
        return fail("E_INVALID_TARGET", f"Target invalide: {target}")

    return await execute_command(commands[target], timeout=60)


async def run_build(target: str = "frontend") -> ToolResult:
    """
    Build le projet.
    target: backend | frontend | all
    """
    commands = {
        "backend": "python3 -m py_compile *.py",  # Vérification syntaxe
        "frontend": "npm run build",
        "all": "python3 -m py_compile *.py; npm run build",
    }

    if target not in commands:
        return fail("E_INVALID_TARGET", f"Target invalide: {target}")

    return await execute_command(commands[target], timeout=180)


async def run_typecheck(target: str = "backend") -> ToolResult:
    """
    Exécute la vérification de types.
    target: backend | frontend
    """
    commands = {
        "backend": "mypy . --ignore-missing-imports --no-error-summary",
        "frontend": "npm run typecheck --if-present",
    }

    if target not in commands:
        return fail("E_INVALID_TARGET", f"Target invalide: {target}")

    return await execute_command(commands[target], timeout=120)


# ===== REGISTRY INITIALIZATION =====

BUILTIN_TOOLS = ToolRegistry()

# Outils système
BUILTIN_TOOLS.register(
    "execute_command",
    execute_command,
    "Exécute une commande shell (sandbox Docker par défaut, allowlist obligatoire)",
    "system",
    {"command": "string", "timeout": "int (optional, default=30)"},
)

BUILTIN_TOOLS.register(
    "get_system_info", get_system_info, "Obtient les informations système", "system", {}
)

BUILTIN_TOOLS.register(
    "get_datetime", get_datetime, "Obtient la date et l'heure actuelles", "utility", {}
)

# Outils filesystem
BUILTIN_TOOLS.register(
    "read_file", read_file, "Lit le contenu d'un fichier", "filesystem", {"path": "string"}
)

BUILTIN_TOOLS.register(
    "write_file",
    write_file,
    "Écrit dans un fichier (WORKSPACE_DIR uniquement)",
    "filesystem",
    {"path": "string", "content": "string", "append": "bool (optional)"},
)

BUILTIN_TOOLS.register(
    "list_directory",
    list_directory,
    "Liste le contenu d'un répertoire",
    "filesystem",
    {"path": "string (optional)"},
)

BUILTIN_TOOLS.register(
    "search_files",
    search_files,
    "Recherche des fichiers par pattern",
    "filesystem",
    {"pattern": "string", "path": "string (optional)"},
)

BUILTIN_TOOLS.register(
    "search_directory",
    search_directory,
    "Recherche sécurisée de répertoires (allowlist, profondeur limitée)",
    "filesystem",
    {"name": "string", "base": "string (optional)", "max_depth": "int (optional, max=3)"},
)

# Outils utility
BUILTIN_TOOLS.register(
    "calculate",
    calculate,
    "Évalue une expression mathématique",
    "utility",
    {"expression": "string"},
)

BUILTIN_TOOLS.register(
    "http_request",
    http_request,
    "Effectue une requête HTTP",
    "network",
    {"url": "string", "method": "string (optional)", "data": "dict (optional)"},
)

# Outil LLM Models
BUILTIN_TOOLS.register(
    "list_llm_models",
    list_llm_models,
    "Liste les modèles LLM disponibles avec catégorisation (général, code, vision, embedding, cloud)",
    "system",
    {},
)

# Outils QA (v6.1)
BUILTIN_TOOLS.register("git_status", git_status, "Affiche le statut Git du workspace", "qa", {})

BUILTIN_TOOLS.register(
    "git_diff", git_diff, "Affiche les différences Git", "qa", {"staged": "bool (optional)"}
)

BUILTIN_TOOLS.register(
    "run_tests",
    run_tests,
    "Exécute les tests (pytest pour backend, npm test pour frontend)",
    "qa",
    {"target": "string: backend|frontend|all"},
)

BUILTIN_TOOLS.register(
    "run_lint",
    run_lint,
    "Exécute le linter (ruff pour backend, npm lint pour frontend)",
    "qa",
    {"target": "string: backend|frontend|all"},
)

BUILTIN_TOOLS.register(
    "run_format",
    run_format,
    "Vérifie le formatage du code (black pour backend)",
    "qa",
    {"target": "string: backend|frontend|all", "check_only": "bool (optional, default=true)"},
)

BUILTIN_TOOLS.register(
    "run_build", run_build, "Build le projet", "qa", {"target": "string: backend|frontend|all"}
)

BUILTIN_TOOLS.register(
    "run_typecheck",
    run_typecheck,
    "Exécute la vérification de types (mypy pour backend)",
    "qa",
    {"target": "string: backend|frontend"},
)



# ===== AUDIT TOOL (v7 Security) =====
BUILTIN_TOOLS.register(
    "get_audit_log",
    get_audit_log,
    "Récupère les entrées d'audit des commandes exécutées",
    "system",
    {"last_n": "int (optional, default=20): Nombre d'entrées à récupérer"},
)



# ===== GOVERNANCE TOOLS (v7) =====

def get_action_history(last_n: int = 20) -> ToolResult:
    """
    Récupère l'historique des actions exécutées.
    
    Args:
        last_n: Nombre d'entrées à récupérer (défaut 20)
    """
    try:
        history = governance_manager.get_action_history(last_n=last_n)
        return ok({
            "actions": history,
            "count": len(history),
        })
    except Exception as e:
        return fail("E_GOVERNANCE_ERROR", str(e))


def get_pending_verifications() -> ToolResult:
    """
    Récupère les actions en attente de vérification.
    """
    try:
        pending = governance_manager.get_pending_verifications()
        return ok({
            "pending": pending,
            "count": len(pending),
        })
    except Exception as e:
        return fail("E_GOVERNANCE_ERROR", str(e))


async def rollback_action(action_id: str) -> ToolResult:
    """
    Effectue le rollback d'une action précédente.
    
    Args:
        action_id: ID de l'action à annuler
    """
    try:
        success, message = await governance_manager.rollback(action_id)
        if success:
            return ok({
                "rolled_back": action_id,
                "message": message,
            })
        else:
            return fail("E_ROLLBACK_FAILED", message)
    except Exception as e:
        return fail("E_ROLLBACK_ERROR", str(e))


# ===== GOVERNANCE TOOLS REGISTRATION =====
BUILTIN_TOOLS.register(
    "get_action_history",
    get_action_history,
    "Récupère l'historique des actions pour audit",
    "governance",
    {"last_n": "int (optional, default=20): Nombre d'entrées"},
)

BUILTIN_TOOLS.register(
    "get_pending_verifications",
    get_pending_verifications,
    "Liste les actions en attente de vérification",
    "governance",
    {},
)

BUILTIN_TOOLS.register(
    "rollback_action",
    rollback_action,
    "Annule une action précédente (si rollback disponible)",
    "governance",
    {"action_id": "string: ID de l'action à annuler"},
)



# ===== MEMORY TOOLS (v7) =====

def memory_remember(
    category: str,
    key: str,
    value: str,
    description: str,
    tags: str = ""
) -> ToolResult:
    """
    Mémorise une information pour usage futur.
    
    Args:
        category: service|convention|incident|decision|context
        key: Clé unique
        value: Valeur à mémoriser
        description: Description humaine
        tags: Tags séparés par virgule
    """
    try:
        cat_map = {
            "service": MemoryCategory.SERVICE,
            "convention": MemoryCategory.CONVENTION,
            "incident": MemoryCategory.INCIDENT,
            "decision": MemoryCategory.DECISION,
            "context": MemoryCategory.CONTEXT,
        }
        cat = cat_map.get(category.lower())
        if not cat:
            return fail("E_INVALID_CATEGORY", f"Catégorie invalide: {category}")
        
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
        
        entry = durable_memory.remember(
            category=cat,
            key=key,
            value=value,
            description=description,
            tags=tag_list
        )
        
        return ok({
            "id": entry.id,
            "key": entry.key,
            "category": entry.category.value,
            "saved": True
        })
    except Exception as e:
        return fail("E_MEMORY_ERROR", str(e))


def memory_recall(
    category: str = "",
    key: str = "",
    tags: str = "",
    query: str = ""
) -> ToolResult:
    """
    Rappelle des informations de la mémoire.
    
    Args:
        category: Filtrer par catégorie (optionnel)
        key: Filtrer par clé exacte (optionnel)
        tags: Tags à rechercher, séparés par virgule (optionnel)
        query: Recherche textuelle (optionnel)
    """
    try:
        # Si query fourni, faire une recherche textuelle
        if query:
            results = durable_memory.search(query)
        else:
            cat = None
            if category:
                cat_map = {
                    "service": MemoryCategory.SERVICE,
                    "convention": MemoryCategory.CONVENTION,
                    "incident": MemoryCategory.INCIDENT,
                    "decision": MemoryCategory.DECISION,
                    "context": MemoryCategory.CONTEXT,
                }
                cat = cat_map.get(category.lower())
            
            tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
            
            results = durable_memory.recall(
                category=cat,
                key=key if key else None,
                tags=tag_list
            )
        
        return ok({
            "entries": [
                {
                    "id": e.id,
                    "category": e.category.value,
                    "key": e.key,
                    "value": e.value,
                    "description": e.description,
                    "tags": e.tags,
                    "confidence": e.confidence
                }
                for e in results[:20]  # Limiter à 20 résultats
            ],
            "count": len(results)
        })
    except Exception as e:
        return fail("E_MEMORY_ERROR", str(e))


def memory_context() -> ToolResult:
    """
    Récupère un résumé du contexte mémorisé.
    """
    try:
        summary = durable_memory.get_context_summary()
        return ok(summary)
    except Exception as e:
        return fail("E_MEMORY_ERROR", str(e))


# ===== RUNBOOK TOOLS (v7) =====

def list_runbooks(category: str = "") -> ToolResult:
    """
    Liste les runbooks disponibles.
    
    Args:
        category: Filtrer par catégorie (deployment|diagnostic|recovery|maintenance|security)
    """
    try:
        if category:
            cat_map = {
                "deployment": RunbookCategory.DEPLOYMENT,
                "diagnostic": RunbookCategory.DIAGNOSTIC,
                "recovery": RunbookCategory.RECOVERY,
                "maintenance": RunbookCategory.MAINTENANCE,
                "security": RunbookCategory.SECURITY,
            }
            cat = cat_map.get(category.lower())
            if not cat:
                return fail("E_INVALID_CATEGORY", f"Catégorie invalide: {category}")
            
            runbooks = runbook_registry.list_by_category(cat)
            result = [
                {
                    "id": rb.id,
                    "name": rb.name,
                    "description": rb.description[:100],
                    "steps_count": len(rb.steps),
                    "requires_admin": rb.requires_admin
                }
                for rb in runbooks
            ]
        else:
            result = runbook_registry.list_all()
        
        return ok({
            "runbooks": result,
            "count": len(result)
        })
    except Exception as e:
        return fail("E_RUNBOOK_ERROR", str(e))


def get_runbook(runbook_id: str) -> ToolResult:
    """
    Récupère les détails d'un runbook.
    
    Args:
        runbook_id: ID du runbook
    """
    try:
        rb = runbook_registry.get(runbook_id)
        if not rb:
            return fail("E_NOT_FOUND", f"Runbook non trouvé: {runbook_id}")
        
        return ok({
            "id": rb.id,
            "name": rb.name,
            "description": rb.description,
            "category": rb.category.value,
            "requires_admin": rb.requires_admin,
            "estimated_duration": rb.estimated_duration,
            "tags": rb.tags,
            "steps": [
                {
                    "name": s.name,
                    "description": s.description,
                    "command": s.command,
                    "tool": s.tool,
                    "on_failure": s.on_failure
                }
                for s in rb.steps
            ]
        })
    except Exception as e:
        return fail("E_RUNBOOK_ERROR", str(e))


def search_runbooks(query: str) -> ToolResult:
    """
    Recherche dans les runbooks.
    
    Args:
        query: Texte à rechercher
    """
    try:
        results = runbook_registry.search(query)
        return ok({
            "runbooks": [
                {
                    "id": rb.id,
                    "name": rb.name,
                    "description": rb.description[:100],
                    "category": rb.category.value
                }
                for rb in results
            ],
            "count": len(results)
        })
    except Exception as e:
        return fail("E_RUNBOOK_ERROR", str(e))


# ===== MEMORY & RUNBOOK REGISTRATION =====
BUILTIN_TOOLS.register(
    "memory_remember",
    memory_remember,
    "Mémorise une information pour usage futur",
    "memory",
    {
        "category": "string: service|convention|incident|decision|context",
        "key": "string: Clé unique",
        "value": "string: Valeur à mémoriser",
        "description": "string: Description humaine",
        "tags": "string (optional): Tags séparés par virgule"
    },
)

BUILTIN_TOOLS.register(
    "memory_recall",
    memory_recall,
    "Rappelle des informations de la mémoire",
    "memory",
    {
        "category": "string (optional): Filtrer par catégorie",
        "key": "string (optional): Filtrer par clé",
        "tags": "string (optional): Tags à rechercher",
        "query": "string (optional): Recherche textuelle"
    },
)

BUILTIN_TOOLS.register(
    "memory_context",
    memory_context,
    "Récupère un résumé du contexte mémorisé",
    "memory",
    {},
)

BUILTIN_TOOLS.register(
    "list_runbooks",
    list_runbooks,
    "Liste les runbooks (procédures standardisées)",
    "runbook",
    {"category": "string (optional): deployment|diagnostic|recovery|maintenance|security"},
)

BUILTIN_TOOLS.register(
    "get_runbook",
    get_runbook,
    "Récupère les détails d'un runbook",
    "runbook",
    {"runbook_id": "string: ID du runbook"},
)

BUILTIN_TOOLS.register(
    "search_runbooks",
    search_runbooks,
    "Recherche dans les runbooks",
    "runbook",
    {"query": "string: Texte à rechercher"},
)


# Export pour compatibilité
__all__ = [
    "BUILTIN_TOOLS",
    "ToolRegistry",
    "ToolResult",
    "ok",
    "fail",
    "is_recoverable_error",
    "RECOVERABLE_ERRORS",
    "search_directory",
]
