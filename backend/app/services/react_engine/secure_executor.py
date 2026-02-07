"""
Secure Command Executor - AI Orchestrator v7
Exécution sécurisée de commandes avec argv explicite (JAMAIS shell=True)

Principes de sécurité:
1. Parsing strict en argv (pas de shell interpretation)
2. Allowlist de commandes autorisées
3. Blocage des caractères dangereux
4. Audit complet de toutes les exécutions
"""

import asyncio
import logging
import os
import re
import shlex
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ExecutionRole(Enum):
    """Rôles d'exécution avec permissions croissantes"""

    VIEWER = "viewer"  # Lecture seule
    OPERATOR = "operator"  # Actions sûres
    ADMIN = "admin"  # Actions sensibles


@dataclass
class AuditEntry:
    """Entrée d'audit pour traçabilité"""

    timestamp: datetime
    role: ExecutionRole
    command: List[str]
    allowed: bool
    reason: str
    result: Optional[Dict] = None
    duration_ms: int = 0


@dataclass
class ExecutionResult:
    """Résultat d'exécution standardisé"""

    success: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = -1
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    audit: Optional[AuditEntry] = None


# ============== CONFIGURATION SÉCURITÉ ==============

# Caractères INTERDITS dans les arguments (injection shell)
FORBIDDEN_CHARS = [
    ";",
    "&&",
    "||",
    "|",
    "`",
    "$(",  # Chaînage/substitution
    ">",
    ">>",
    "<",
    "<<",  # Redirections
    "\n",
    "\r",  # Newlines
    "\x00",  # Null byte
]

FORBIDDEN_PATTERNS = [
    r"\$\{",  # ${var}
    r"\$\(",  # $(cmd)
    r"`[^`]+`",  # `cmd`
    r">\s*/etc",  # Écriture /etc
    r">\s*/root",  # Écriture /root
    r"rm\s+-rf\s+/",  # rm -rf /
]

# Commandes autorisées par rôle
ALLOWED_COMMANDS = {
    ExecutionRole.VIEWER: {
        # Informations système
        "cat",
        "head",
        "tail",
        "less",
        "more",
        "ls",
        "pwd",
        "whoami",
        "hostname",
        "uname",
        "df",
        "du",
        "free",
        "uptime",
        "date",
        "ps",
        "top",
        "htop",
        "ip",
        "ifconfig",
        "netstat",
        "ss",
        "ollama",  # list, ps
        # SECURITY: curl/wget removed to prevent SSRF attacks
        "grep",
        "find",
        "wc",
        "sort",
        "uniq",
        "which",
        "whereis",
        "file",
        "stat",
    },
    ExecutionRole.OPERATOR: {
        # Inclut VIEWER +
        "docker",  # inspect, logs, ps, restart
        "systemctl",  # status, restart, reload
        "git",  # status, log, diff, pull, fetch
        "npm",
        # SECURITY: python3/pip3 removed to prevent arbitrary code execution
        "service",
        "journalctl",
    },
    ExecutionRole.ADMIN: {
        # Inclut OPERATOR +
        "apt",
        "apt-get",
        "mkdir",
        "touch",
        "cp",
        "mv",
        "chmod",
        "chown",
        "tee",
        "git",  # push, commit
        "docker",  # build, run
    },
}

# Sous-commandes interdites même pour ADMIN
FORBIDDEN_SUBCOMMANDS = {
    "rm": ["-rf /", "-rf /*", "-rf /home", "-rf /etc"],
    "dd": ["of=/dev/"],
    "mkfs": ["*"],
    "fdisk": ["*"],
    "parted": ["*"],
}


class SecureExecutor:
    """Exécuteur de commandes sécurisé"""

    def __init__(self, workspace_dir: str = "/home/lalpha/orchestrator-workspace"):
        self.workspace_dir = workspace_dir
        self.audit_log: List[AuditEntry] = []
        self._ensure_workspace()

    def _ensure_workspace(self):
        """Crée le workspace s'il n'existe pas"""
        os.makedirs(self.workspace_dir, exist_ok=True)

    def _contains_forbidden_chars(self, arg: str) -> Tuple[bool, str]:
        """Vérifie si un argument contient des caractères interdits"""
        for char in FORBIDDEN_CHARS:
            if char in arg:
                return True, f"Caractère interdit: {repr(char)}"

        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, arg, re.IGNORECASE):
                return True, f"Pattern interdit détecté"

        return False, ""

    def _parse_command_safe(self, command: str) -> Tuple[bool, List[str], str]:
        """
        Parse une commande en argv de manière SÉCURISÉE
        Retourne: (success, argv, error_message)
        """
        # Vérifier les caractères interdits AVANT le parsing
        has_forbidden, reason = self._contains_forbidden_chars(command)
        if has_forbidden:
            return False, [], reason

        try:
            # Utiliser shlex pour parser correctement les quotes
            argv = shlex.split(command)

            if not argv:
                return False, [], "Commande vide"

            # Vérifier chaque argument individuellement
            for arg in argv:
                has_forbidden, reason = self._contains_forbidden_chars(arg)
                if has_forbidden:
                    return False, [], f"Argument interdit: {reason}"

            return True, argv, ""

        except ValueError as e:
            return False, [], f"Erreur de parsing: {e}"

    def _is_command_allowed(self, argv: List[str], role: ExecutionRole) -> Tuple[bool, str]:
        """Vérifie si la commande est autorisée pour le rôle donné"""
        if not argv:
            return False, "Commande vide"

        base_cmd = os.path.basename(argv[0])

        # Construire la liste des commandes autorisées pour ce rôle
        allowed = set()
        if role == ExecutionRole.ADMIN:
            allowed = (
                ALLOWED_COMMANDS[ExecutionRole.VIEWER]
                | ALLOWED_COMMANDS[ExecutionRole.OPERATOR]
                | ALLOWED_COMMANDS[ExecutionRole.ADMIN]
            )
        elif role == ExecutionRole.OPERATOR:
            allowed = (
                ALLOWED_COMMANDS[ExecutionRole.VIEWER] | ALLOWED_COMMANDS[ExecutionRole.OPERATOR]
            )
        else:
            allowed = ALLOWED_COMMANDS[ExecutionRole.VIEWER]

        if base_cmd not in allowed:
            return False, f"Commande '{base_cmd}' non autorisée pour le rôle {role.value}"

        # Vérifier les sous-commandes interdites
        if base_cmd in FORBIDDEN_SUBCOMMANDS:
            full_cmd = " ".join(argv)
            for forbidden in FORBIDDEN_SUBCOMMANDS[base_cmd]:
                if forbidden == "*" or forbidden in full_cmd:
                    return False, f"Sous-commande interdite: {base_cmd} {forbidden}"

        return True, ""

    def _create_audit_entry(
        self, role: ExecutionRole, argv: List[str], allowed: bool, reason: str
    ) -> AuditEntry:
        """Crée une entrée d'audit"""
        return AuditEntry(
            timestamp=datetime.now(), role=role, command=argv, allowed=allowed, reason=reason
        )

    async def execute(
        self,
        command: str,
        role: ExecutionRole = ExecutionRole.VIEWER,
        timeout: int | None = None,
        cwd: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Exécute une commande de manière SÉCURISÉE

        Args:
            command: Commande à exécuter (sera parsée en argv)
            role: Rôle d'exécution (détermine les permissions)
            timeout: Timeout en secondes (défaut: settings.TIMEOUT_COMMAND_DEFAULT)
            cwd: Répertoire de travail (défaut: workspace)

        Returns:
            ExecutionResult avec résultat et audit
        """
        # Timeout configurable (v7.1) — borné pour éviter les abus
        from app.core.config import settings

        if timeout is None:
            timeout = settings.TIMEOUT_COMMAND_DEFAULT
        else:
            timeout = max(1, min(timeout, settings.TIMEOUT_COMMAND_DEFAULT * 2))

        start_time = time.time()
        work_dir = cwd or self.workspace_dir

        # 1. Parser la commande en argv
        parse_ok, argv, parse_error = self._parse_command_safe(command)

        if not parse_ok:
            audit = self._create_audit_entry(role, [command], False, parse_error)
            self.audit_log.append(audit)
            logger.warning(f"[AUDIT] BLOCKED: {command} - {parse_error}")

            return ExecutionResult(
                success=False, error_code="E_PARSE_ERROR", error_message=parse_error, audit=audit
            )

        # 2. Vérifier les permissions
        allowed, allow_reason = self._is_command_allowed(argv, role)

        if not allowed:
            audit = self._create_audit_entry(role, argv, False, allow_reason)
            self.audit_log.append(audit)
            logger.warning(f"[AUDIT] DENIED: {' '.join(argv)} - {allow_reason}")

            return ExecutionResult(
                success=False, error_code="E_NOT_ALLOWED", error_message=allow_reason, audit=audit
            )

        # 3. Exécuter avec subprocess_exec (JAMAIS shell=True)
        audit = self._create_audit_entry(role, argv, True, "Exécution autorisée")

        try:
            logger.info(f"[AUDIT] EXEC: {' '.join(argv)} (role={role.value})")

            process = await asyncio.create_subprocess_exec(
                *argv, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=work_dir
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

            duration_ms = int((time.time() - start_time) * 1000)
            audit.duration_ms = duration_ms

            result = ExecutionResult(
                success=(process.returncode == 0),
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                returncode=process.returncode,
                audit=audit,
            )

            if process.returncode != 0:
                result.error_code = "E_CMD_FAILED"
                result.error_message = f"Code retour: {process.returncode}"

            audit.result = {
                "success": result.success,
                "returncode": result.returncode,
                "stdout_len": len(result.stdout),
                "stderr_len": len(result.stderr),
            }

            self.audit_log.append(audit)
            logger.info(f"[AUDIT] DONE: {' '.join(argv)} -> {result.returncode} ({duration_ms}ms)")

            return result

        except asyncio.TimeoutError:
            audit.result = {"error": "timeout"}
            self.audit_log.append(audit)
            logger.error(f"[AUDIT] TIMEOUT: {' '.join(argv)}")

            return ExecutionResult(
                success=False,
                error_code="E_TIMEOUT",
                error_message=f"Timeout après {timeout}s",
                audit=audit,
            )

        except FileNotFoundError:
            audit.result = {"error": "not_found"}
            self.audit_log.append(audit)

            return ExecutionResult(
                success=False,
                error_code="E_CMD_NOT_FOUND",
                error_message=f"Commande non trouvée: {argv[0]}",
                audit=audit,
            )

        except Exception as e:
            audit.result = {"error": str(e)}
            self.audit_log.append(audit)
            logger.error(f"[AUDIT] ERROR: {' '.join(argv)} - {e}")

            return ExecutionResult(
                success=False, error_code="E_EXEC_ERROR", error_message=str(e), audit=audit
            )

    def get_audit_log(self, last_n: int = 50) -> List[Dict]:
        """Récupère les dernières entrées d'audit"""
        entries = self.audit_log[-last_n:]
        return [
            {
                "timestamp": e.timestamp.isoformat(),
                "role": e.role.value,
                "command": e.command,
                "allowed": e.allowed,
                "reason": e.reason,
                "result": e.result,
                "duration_ms": e.duration_ms,
            }
            for e in entries
        ]

    def clear_audit_log(self):
        """Vide le log d'audit (garder les 100 derniers)"""
        if len(self.audit_log) > 100:
            self.audit_log = self.audit_log[-100:]


# Instance globale
secure_executor = SecureExecutor()
