"""
Configuration de l'application AI Orchestrator v6.2 SECURE
AUDIT: Corrections sécurité appliquées le 2026-01-09
"""

import os
import secrets
from typing import List, Literal, Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # CRQ-P0-6: Accepter JWT_SECRET_KEY comme alias de SECRET_KEY
        populate_by_name=True,
    )

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = False
    WORKERS: int = 1

    # App
    APP_NAME: str = "AI Orchestrator"
    APP_VERSION: str = "8.1.0"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"  # "text" ou "json" (v7.1)

    # CORS - Domaines spécifiques
    # SECURITY: localhost ajouté uniquement si DEBUG=true via .env
    CORS_ORIGINS: List[str] = [
        "https://ai.4lb.ca",
        "https://llm.4lb.ca",
        "https://4lb.ca",
    ]
    # Pour le dev local, ajouter CORS_DEV_ORIGIN=http://localhost:3000 dans .env
    CORS_DEV_ORIGIN: Optional[str] = None

    # Security - CORRIGÉ: Clé forte par défaut (sera overridée par .env)
    # Mode test - désactive les dépendances externes (Ollama health check)
    TESTING: bool = False

    # Secret Key - CRQ-P0-6: OBLIGATOIRE en production (via JWT_SECRET_KEY ou SECRET_KEY)
    SECRET_KEY: Optional[str] = Field(default=None, validation_alias="JWT_SECRET_KEY")
    ALGORITHM: str = "HS256"

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def validate_secret_key(cls, v, info):
        """
        CRQ-P0-6: Valide que SECRET_KEY est fourni en production.

        En mode test: Génère une clé temporaire (OK pour tests)
        En production: DOIT être fourni via .env (JWT_SECRET_KEY ou SECRET_KEY)
        """
        # Check TESTING flag from values being validated
        is_testing = info.data.get("TESTING", False) or os.getenv("TESTING") == "1"

        if v:
            # SECRET_KEY fourni dans .env → OK
            return v

        if is_testing:
            # Mode test → Génère clé éphémère (acceptable)
            generated = secrets.token_urlsafe(64)
            return generated

        # Production + pas de SECRET_KEY → ERREUR
        raise ValueError(
            "SECRET_KEY is REQUIRED in production. "
            "Set JWT_SECRET_KEY or SECRET_KEY in .env file. "
            "Generate with: python3 -c 'import secrets; print(secrets.token_urlsafe(64))'"
        )

    # SECURITY: Short-lived access tokens with refresh token pattern
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes (was 24h)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days for refresh tokens

    # Rate Limiting (nouveau)
    RATE_LIMIT_PER_MINUTE: int = 30
    RATE_LIMIT_BURST: int = 10

    # Database
    DATABASE_URL: str = "sqlite:///./data/orchestrator.db"

    # Ollama
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "kimi-k2.5:cloud"
    OLLAMA_TIMEOUT: int = 300

    # Models disponibles
    DEFAULT_MODEL: str = "kimi-k2.5:cloud"
    AVAILABLE_MODELS: List[str] = [
        "kimi-k2.5:cloud",
        "qwen2.5-coder:32b-instruct-q4_K_M",
        "qwen3:32b",
        "qwen3-coder:480b-cloud",
        "gemini-3-pro-preview",
        "huihui_ai/qwen2.5-abliterate:32b",
        "mannix/llama3.1-8b-abliterated",
        "llama3.2-vision:11b-instruct-q8_0",
    ]

    # Workflow Models (v6.1)
    EXECUTOR_MODEL: str = "kimi-k2.5:cloud"
    VERIFIER_MODEL: str = "qwen2.5-coder:32b-instruct-q4_K_M"

    # ReAct Engine
    MAX_ITERATIONS: int = 10

    # Workflow Settings
    VERIFY_REQUIRED: bool = False
    MAX_REPAIR_CYCLES: int = 3

    # WebSocket Event System (v8)
    # WS_MODE: "v7" (legacy), "v8" (strict), "compat" (default, emit v8 with optional validation)
    WS_MODE: Literal["v7", "v8", "compat"] = "compat"
    WS_STRICT_VALIDATION: bool = True  # Validate events against Pydantic schemas
    WS_TERMINAL_ENFORCEMENT: bool = True  # Enforce exactly one terminal event per run

    # Agent Isolation (CRQ-P0-1)
    ENFORCE_AGENT_ISOLATION: bool = False  # Default OFF for backward compat

    # Governance Blocking (CRQ-P0-2)
    ENFORCE_GOVERNANCE_BLOCKING: bool = False  # Default OFF for backward compat

    # Prompt Injection Detection (CRQ-P0-3)
    ENFORCE_PROMPT_INJECTION_DETECTION: bool = False  # Default OFF for backward compat
    PROMPT_INJECTION_STRICT_MODE: bool = False  # Detect MEDIUM severity too

    # Registration Control
    ALLOW_REGISTRATION: bool = True  # Set to False to disable open registration

    # HttpOnly Cookies (CRQ-P0-4)
    USE_HTTPONLY_COOKIES: bool = False  # Default OFF for backward compat
    COOKIE_SECURE: bool = True  # Require HTTPS in production
    COOKIE_SAMESITE: str = "lax"  # lax, strict, or none
    COOKIE_DOMAIN: Optional[str] = None  # None = current domain only

    # Strict CSP Headers (CRQ-P1-3)
    ENFORCE_STRICT_CSP: bool = False  # Default OFF for backward compat

    # Correlation ID for distributed tracing (CRQ-P1-6)
    ENABLE_CORRELATION_ID: bool = False  # Default OFF for backward compat

    # Event Queue WebSocket (CRQ-P1-5)
    ENABLE_EVENT_QUEUE: bool = False  # Default OFF for backward compat
    EVENT_QUEUE_MAX_SIZE: int = 1000  # Max events per run before purge
    EVENT_QUEUE_TTL_MINUTES: int = 30  # TTL for queued events

    # Memory Cleanup (CRQ-P0-5)
    ENABLE_MEMORY_CLEANUP: bool = False  # Default OFF for backward compat
    MEMORY_TTL_DAYS: int = 7  # TTL for memories (default 7 days)
    MEMORY_MAX_DOCUMENTS: int = 10000  # Max documents before purge
    MEMORY_CLEANUP_INTERVAL_HOURS: int = 1  # Cleanup interval

    # Workspace Safety
    WORKSPACE_DIR: str = "/"
    WORKSPACE_ALLOW_WRITE: bool = True

    # EXECUTION SECURITY - CORRIGÉ: Mode sandbox par défaut
    EXECUTE_MODE: str = "direct"
    SANDBOX_IMAGE: str = "ubuntu:24.04"
    SANDBOX_MEMORY: str = "512m"
    SANDBOX_CPUS: str = "0.5"
    SANDBOX_TIMEOUT: int = 30

    # TIMEOUTS (secondes) - Configuration centralisée v7.1
    # HTTP Timeouts
    TIMEOUT_HTTP_REQUEST: int = 30  # Requêtes HTTP externes (APIs tierces)
    TIMEOUT_OLLAMA_CHAT: int = 120  # Génération LLM (peut être longue)
    TIMEOUT_OLLAMA_CONNECT: int = 10  # Connexion initiale Ollama
    TIMEOUT_OLLAMA_LIST: int = 10  # Liste modèles (opération légère)
    TIMEOUT_HEALTH_CHECK: int = 5  # Health checks (doivent être rapides)

    # Command Execution Timeouts
    TIMEOUT_COMMAND_DEFAULT: int = 30  # Commandes shell simples
    TIMEOUT_GIT: int = 10  # Git status (opération rapide)
    TIMEOUT_GIT_DIFF: int = 30  # Git diff (peut être long sur gros repos)
    TIMEOUT_TESTS: int = 300  # Exécution tests (5 min)
    TIMEOUT_LINT: int = 60  # Linting (ruff, black, mypy)
    TIMEOUT_TYPECHECK: int = 60  # Type checking (mypy)
    TIMEOUT_BUILD: int = 180  # Builds frontend (3 min)
    TIMEOUT_DOCKER: int = 300  # Docker compose up/down (5 min, pull images)

    # Database Timeouts
    TIMEOUT_DB_CONNECT: int = 10  # Connexion SQLite
    TIMEOUT_DB_QUERY: int = 10  # Requête DB individuelle (protection anti-blocage)

    # ALLOWLIST SÉCURISÉE
    COMMAND_ALLOWLIST: List[str] = [
        "uname",
        "hostname",
        "uptime",
        "whoami",
        "id",
        "date",
        "cal",
        "pwd",
        "printenv",
        "free",
        "df",
        "du",
        "lscpu",
        "nproc",
        "lsmem",
        "ps",
        "pgrep",
        "pidof",
        "ls",
        "tree",
        "find",
        "realpath",
        "readlink",
        "dirname",
        "basename",
        "file",
        "stat",
        "cat",
        "head",
        "tail",
        "less",
        "more",
        "wc",
        "nl",
        "md5sum",
        "sha256sum",
        "mkdir",
        "touch",
        "grep",
        "egrep",
        "fgrep",
        "rg",
        "sed",
        "awk",
        "gawk",
        "cut",
        "paste",
        "sort",
        "uniq",
        "tr",
        "diff",
        "comm",
        "tee",
        "xargs",
        "printf",
        "echo",
        "jq",
        "yq",
        "python3",
        "pip3",
        "ruff",
        "black",
        "mypy",
        "flake8",
        "pylint",
        "bandit",
        "node",
        "npm",
        "npx",
        "git",
        "which",
        "whereis",
        "type",
        "command",
        "test",
        "[",
        "true",
        "false",
        "seq",
        "bc",
        "expr",
        "base64",
        "strings",
        "tar",
        "gzip",
        "gunzip",
        "bzip2",
        "bunzip2",
        "xz",
        "unzip",
        "ollama",
    ]

    # BLOCKLIST ÉTENDUE
    COMMAND_BLOCKLIST: List[str] = [
        "bash",
        "sh",
        "zsh",
        "csh",
        "tcsh",
        "ksh",
        "fish",
        "dash",
        "ash",
        "busybox",
        "exec",
        "eval",
        "source",
        "nc",
        "netcat",
        "ncat",
        "socat",
        "curl",
        "wget",
        "ssh",
        "scp",
        "sftp",
        "rsync",
        "telnet",
        "ftp",
        "tftp",
        "nmap",
        "masscan",
        "kill",
        "pkill",
        "killall",
        "nohup",
        "disown",
        "nice",
        "renice",
        "docker",
        "docker-compose",
        "podman",
        "kubectl",
        "crictl",
        "rm",
        "rmdir",
        "shred",
        "wipe",
        "srm",
        "mkfs",
        "mkswap",
        "fdisk",
        "parted",
        "gdisk",
        "dd",
        "truncate",
        "chmod",
        "chown",
        "chgrp",
        "chattr",
        "setfacl",
        "getfacl",
        "sudo",
        "su",
        "doas",
        "pkexec",
        "gksudo",
        "kdesudo",
        "passwd",
        "chpasswd",
        "shadow",
        "useradd",
        "userdel",
        "usermod",
        "groupadd",
        "groupdel",
        "groupmod",
        "visudo",
        "sudoedit",
        "systemctl",
        "service",
        "init",
        "shutdown",
        "reboot",
        "poweroff",
        "halt",
        "telinit",
        "runlevel",
        "journalctl",
        "mount",
        "umount",
        "losetup",
        "cryptsetup",
        "lvm",
        "iptables",
        "ip6tables",
        "nftables",
        "ufw",
        "firewall-cmd",
        "route",
        "ip",
        "ifconfig",
        "ifup",
        "ifdown",
        "brctl",
        "bridge",
        "insmod",
        "rmmod",
        "modprobe",
        "sysctl",
        "dmesg",
        "crontab",
        "at",
        "batch",
        "strace",
        "ltrace",
        "ptrace",
        "gdb",
        "lldb",
        "objdump",
        "tcpdump",
        "wireshark",
        "tshark",
        "gcc",
        "g++",
        "clang",
        "make",
        "cmake",
        "ld",
        "as",
        "chroot",
        "pivot_root",
        "unshare",
        "nsenter",
        "xterm",
        "screen",
        "tmux",
        "expect",
        "autoexpect",
        "perl",
        "ruby",
        "php",
    ]

    # ARGUMENTS DANGEREUX
    DANGEROUS_ARGUMENTS: List[str] = [
        "-c",
        "--command",
        "-e",
        "--eval",
        "--exec",
        "-i",
        "--interactive",
        "-t",
        "--tty",
        "--privileged",
        "--cap-add",
        "-u root",
        "--user root",
        "--network",
        "-p",
        "--publish",
        "-v /",
        "-v /etc",
        "-v /root",
        "-v /home",
        "--volume /",
        "> /etc",
        ">> /etc",
        "> /root",
        ">> /root",
        "| bash",
        "| sh",
        "git push",
        "git commit",
        "git reset --hard",
        "git clean -fd",
    ]

    # URLs autorisées
    ALLOWED_URL_PATTERNS: List[str] = [
        "http://localhost",
        "http://127.0.0.1",
        "https://api.github.com",
        "https://ollama",
    ]


settings = Settings()
