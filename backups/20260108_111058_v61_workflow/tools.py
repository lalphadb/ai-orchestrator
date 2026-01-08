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
import subprocess
import shlex
import os
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Callable, Optional, List, TypedDict
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


# ===== TOOL RESULT CONTRACT =====

class ToolError(TypedDict):
    code: str
    message: str


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
    return {
        "success": True,
        "data": data,
        "error": None,
        "meta": {"duration_ms": 0, **meta_extra}
    }


def fail(code: str, message: str, **meta_extra) -> ToolResult:
    """Retourne un résultat d'erreur standardisé"""
    return {
        "success": False,
        "data": None,
        "error": {"code": code, "message": message},
        "meta": {"duration_ms": 0, **meta_extra}
    }


def with_timing(func):
    """Decorator pour mesurer le temps d'exécution"""
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
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
            return False, f"Commande non autorisée: {binary}. Allowlist: {', '.join(settings.COMMAND_ALLOWLIST[:10])}..."
        
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
        parameters: Optional[Dict[str, Any]] = None
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

async def execute_command(command: str, timeout: int = 30) -> ToolResult:
    """
    Exécute une commande shell de manière sécurisée.
    
    - Mode sandbox (défaut): Docker isolé, réseau désactivé
    - Mode host: exécution directe (dangereux)
    - Allowlist obligatoire pour les commandes
    """
    # 1. Vérifier allowlist
    allowed, reason = is_command_allowed(command)
    if not allowed:
        return fail("E_CMD_NOT_ALLOWED", reason, command=command)
    
    # 2. Construire la commande selon le mode
    use_sandbox = settings.EXECUTE_MODE == "sandbox"
    
    if use_sandbox:
        # S'assurer que le workspace existe
        os.makedirs(settings.WORKSPACE_DIR, exist_ok=True)
        
        docker_cmd = [
            "docker", "run", "--rm",
            "--network=none",
            f"--memory={settings.SANDBOX_MEMORY}",
            f"--cpus={settings.SANDBOX_CPUS}",
            "--read-only",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=100m",
            "-v", f"{settings.WORKSPACE_DIR}:/workspace:rw",
            "-w", "/workspace",
            settings.SANDBOX_IMAGE,
            "bash", "-lc", command
        ]
        exec_command = docker_cmd
        shell = False
    else:
        exec_command = command
        shell = True
    
    # 3. Exécuter
    try:
        if shell:
            process = await asyncio.create_subprocess_shell(
                exec_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=settings.WORKSPACE_DIR
            )
        else:
            process = await asyncio.create_subprocess_exec(
                *exec_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )
        
        stdout_str = stdout.decode("utf-8", errors="replace")
        stderr_str = stderr.decode("utf-8", errors="replace")
        returncode = process.returncode
        
        # Succès si returncode == 0
        if returncode == 0:
            return ok(
                {
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                    "returncode": returncode
                },
                command=command,
                sandbox=use_sandbox
            )
        else:
            return fail(
                "E_CMD_FAILED",
                f"Commande échouée (code {returncode}): {stderr_str[:500]}",
                command=command,
                sandbox=use_sandbox
            )
            
    except asyncio.TimeoutError:
        return fail("E_TIMEOUT", f"Timeout après {timeout}s", command=command, sandbox=use_sandbox)
    except FileNotFoundError:
        if use_sandbox:
            return fail("E_DOCKER_NOT_FOUND", "Docker non disponible. Installez Docker ou passez EXECUTE_MODE=host", command=command)
        return fail("E_CMD_NOT_FOUND", "Commande non trouvée", command=command)
    except Exception as e:
        return fail("E_CMD_ERROR", str(e), command=command, sandbox=use_sandbox)


def read_file(path: str) -> ToolResult:
    """Lit le contenu d'un fichier"""
    try:
        # Résoudre le chemin (relatif au workspace si pas absolu)
        if not os.path.isabs(path):
            path = os.path.join(settings.WORKSPACE_DIR, path)
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return ok({
            "content": content,
            "path": path,
            "size": len(content),
            "lines": content.count("\n") + 1
        })
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
        
        return ok({
            "path": path,
            "size": len(content),
            "mode": "append" if append else "write"
        })
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
            entries.append({
                "name": entry.name,
                "is_dir": entry.is_dir(),
                "size": entry.stat().st_size if entry.is_file() else 0,
            })
        
        return ok({
            "path": path,
            "entries": entries,
            "count": len(entries)
        })
    except FileNotFoundError:
        return fail("E_DIR_NOT_FOUND", f"Répertoire non trouvé: {path}")
    except Exception as e:
        return fail("E_LIST_ERROR", str(e))


def get_system_info() -> ToolResult:
    """Informations système"""
    import platform
    try:
        import psutil
        return ok({
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
        })
    except ImportError:
        return ok({
            "os": platform.system(),
            "release": platform.release(),
            "hostname": platform.node(),
            "workspace": settings.WORKSPACE_DIR,
            "execute_mode": settings.EXECUTE_MODE,
        })


def get_datetime() -> ToolResult:
    """Date et heure actuelles"""
    now = datetime.now()
    return ok({
        "datetime": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "timestamp": int(now.timestamp()),
    })


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
        
        tree = ast.parse(expression, mode='eval')
        result = eval_expr(tree.body)
        
        return ok({
            "expression": expression,
            "result": result
        })
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
            
            return ok({
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text[:10000],
            })
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
        return ok({
            "pattern": pattern,
            "path": path,
            "matches": matches[:100],
            "count": len(matches)
        })
    except Exception as e:
        return fail("E_SEARCH_ERROR", str(e))


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
        "all": "python3 -m pytest -q --tb=short && npm run test --if-present"
    }
    
    if target not in commands:
        return fail("E_INVALID_TARGET", f"Target invalide: {target}. Utiliser: backend, frontend, all")
    
    return await execute_command(commands[target], timeout=120)


async def run_lint(target: str = "backend") -> ToolResult:
    """
    Exécute le linter.
    target: backend | frontend | all
    """
    commands = {
        "backend": "ruff check . --output-format=concise",
        "frontend": "npm run lint --if-present",
        "all": "ruff check . --output-format=concise; npm run lint --if-present"
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
            "all": "black . --check --diff; npm run format:check --if-present"
        }
    else:
        commands = {
            "backend": "black .",
            "frontend": "npm run format --if-present",
            "all": "black .; npm run format --if-present"
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
        "all": "python3 -m py_compile *.py; npm run build"
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
        "frontend": "npm run typecheck --if-present"
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
    {"command": "string", "timeout": "int (optional, default=30)"}
)

BUILTIN_TOOLS.register(
    "get_system_info",
    get_system_info,
    "Obtient les informations système",
    "system",
    {}
)

BUILTIN_TOOLS.register(
    "get_datetime",
    get_datetime,
    "Obtient la date et l'heure actuelles",
    "utility",
    {}
)

# Outils filesystem
BUILTIN_TOOLS.register(
    "read_file",
    read_file,
    "Lit le contenu d'un fichier",
    "filesystem",
    {"path": "string"}
)

BUILTIN_TOOLS.register(
    "write_file",
    write_file,
    "Écrit dans un fichier (WORKSPACE_DIR uniquement)",
    "filesystem",
    {"path": "string", "content": "string", "append": "bool (optional)"}
)

BUILTIN_TOOLS.register(
    "list_directory",
    list_directory,
    "Liste le contenu d'un répertoire",
    "filesystem",
    {"path": "string (optional)"}
)

BUILTIN_TOOLS.register(
    "search_files",
    search_files,
    "Recherche des fichiers par pattern",
    "filesystem",
    {"pattern": "string", "path": "string (optional)"}
)

# Outils utility
BUILTIN_TOOLS.register(
    "calculate",
    calculate,
    "Évalue une expression mathématique",
    "utility",
    {"expression": "string"}
)

BUILTIN_TOOLS.register(
    "http_request",
    http_request,
    "Effectue une requête HTTP",
    "network",
    {"url": "string", "method": "string (optional)", "data": "dict (optional)"}
)

# Outils QA (v6.1)
BUILTIN_TOOLS.register(
    "git_status",
    git_status,
    "Affiche le statut Git du workspace",
    "qa",
    {}
)

BUILTIN_TOOLS.register(
    "git_diff",
    git_diff,
    "Affiche les différences Git",
    "qa",
    {"staged": "bool (optional)"}
)

BUILTIN_TOOLS.register(
    "run_tests",
    run_tests,
    "Exécute les tests (pytest pour backend, npm test pour frontend)",
    "qa",
    {"target": "string: backend|frontend|all"}
)

BUILTIN_TOOLS.register(
    "run_lint",
    run_lint,
    "Exécute le linter (ruff pour backend, npm lint pour frontend)",
    "qa",
    {"target": "string: backend|frontend|all"}
)

BUILTIN_TOOLS.register(
    "run_format",
    run_format,
    "Vérifie le formatage du code (black pour backend)",
    "qa",
    {"target": "string: backend|frontend|all", "check_only": "bool (optional, default=true)"}
)

BUILTIN_TOOLS.register(
    "run_build",
    run_build,
    "Build le projet",
    "qa",
    {"target": "string: backend|frontend|all"}
)

BUILTIN_TOOLS.register(
    "run_typecheck",
    run_typecheck,
    "Exécute la vérification de types (mypy pour backend)",
    "qa",
    {"target": "string: backend|frontend"}
)


# Export pour compatibilité
__all__ = ["BUILTIN_TOOLS", "ToolRegistry", "ToolResult", "ok", "fail"]
