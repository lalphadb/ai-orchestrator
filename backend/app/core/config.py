"""
Configuration de l'application AI Orchestrator v6.1
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = False
    WORKERS: int = 1
    
    # App
    APP_NAME: str = "AI Orchestrator"
    APP_VERSION: str = "6.1.0"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Security
    SECRET_KEY: str = "change-me-in-production-use-strong-random-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 jours
    
    # Database
    DATABASE_URL: str = "sqlite:///./ai_orchestrator.db"
    
    # Ollama
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "kimi-k2:1t-cloud"
    OLLAMA_TIMEOUT: int = 300
    
    # Models disponibles
    DEFAULT_MODEL: str = "kimi-k2:1t-cloud"
    AVAILABLE_MODELS: List[str] = [
        "kimi-k2:1t-cloud",
        "qwen2.5-coder:32b-instruct-q4_K_M",
        "deepseek-coder:33b",
        "gemini-3-pro-preview",
        "qwen3-coder:480b-cloud",
    ]
    
    # Workflow Models (v6.1)
    EXECUTOR_MODEL: str = "kimi-k2:1t-cloud"
    VERIFIER_MODEL: str = "deepseek-coder:33b"
    
    # ReAct Engine
    MAX_ITERATIONS: int = 10
    
    # Workflow Settings
    VERIFY_REQUIRED: bool = True
    MAX_REPAIR_CYCLES: int = 3
    
    # Workspace Safety
    WORKSPACE_DIR: str = "/home/lalpha/orchestrator-workspace"
    WORKSPACE_ALLOW_WRITE: bool = True
    
    # Execution Security - MODE DIRECT pour autonomie
    EXECUTE_MODE: str = "direct"
    SANDBOX_IMAGE: str = "ubuntu:24.04"
    SANDBOX_MEMORY: str = "1024m"
    SANDBOX_CPUS: str = "1"
    
    # ==========================================================================
    # ALLOWLIST ÉTENDUE - Commandes autorisées pour l'autonomie du système
    # ==========================================================================
    COMMAND_ALLOWLIST: List[str] = [
        # --- Développement Python ---
        "python", "python3", "pip", "pip3", "pytest", "coverage",
        "ruff", "black", "mypy", "flake8", "pylint", "bandit",
        "uvicorn", "gunicorn", "alembic", "flask", "django-admin",
        
        # --- Développement Node.js ---
        "node", "npm", "npx", "pnpm", "yarn", "bun",
        "tsc", "eslint", "prettier",
        
        # --- Git & Version Control ---
        "git", "gh",
        
        # --- Système - Information ---
        "which", "whereis", "type", "command",
        "uname", "hostname", "hostnamectl",
        "uptime", "w",
        "whoami", "id", "groups",
        "printenv",
        
        # --- Système - Ressources ---
        "free", "vmstat",
        "df", "du",
        "lsblk", "blkid",
        "lscpu", "nproc",
        "lsmem",
        
        # --- Système - Processus ---
        "ps", "pgrep", "pidof",
        "top", "htop",
        "kill", "pkill",
        "nice", "renice",
        "nohup", "timeout",
        
        # --- Fichiers - Navigation ---
        "ls", "tree", "find", "locate",
        "pwd", "cd",
        "realpath", "readlink",
        "dirname", "basename",
        "file", "stat",
        
        # --- Fichiers - Lecture ---
        "cat", "head", "tail", "less", "more",
        "wc", "nl",
        "md5sum", "sha256sum",
        
        # --- Fichiers - Manipulation ---
        "mkdir", "cp", "mv", "touch", "ln",
        "install",
        
        # --- Fichiers - Archives ---
        "tar", "gzip", "gunzip", "bzip2", "bunzip2",
        "zip", "unzip", "xz",
        
        # --- Texte - Traitement ---
        "grep", "egrep", "fgrep", "ripgrep", "rg",
        "sed", "awk", "gawk",
        "cut", "paste", "join",
        "sort", "uniq", "shuf",
        "tr", "rev",
        "diff", "cmp", "comm",
        "patch",
        "tee", "xargs",
        
        # --- Texte - Format ---
        "printf", "echo",
        "fmt", "fold", "column",
        "expand", "unexpand",
        
        # --- JSON/YAML/Data ---
        "jq", "yq",
        "csvtool",
        
        # --- Réseau - Info (lecture seule) ---
        "ip", "ifconfig",
        "netstat", "ss",
        "lsof",
        "ping", "traceroute", "mtr",
        "host", "dig", "nslookup",
        "nc", "netcat",
        
        # --- Docker ---
        "docker", "docker-compose",
        "podman",
        
        # --- Ollama & IA ---
        "ollama",
        
        # --- Utilitaires ---
        "date", "cal",
        "sleep", "watch",
        "env", "export",
        "test", "[", "[[",
        "true", "false",
        "seq", "yes",
        "bc", "expr",
        "base64",
        "strings",
        "od", "xxd", "hexdump",
        
        # --- Shell ---
        "bash", "sh", "zsh",
        "source", ".",
        "alias", "unalias",
        "set", "unset",
        "history",
    ]
    
    # ==========================================================================
    # BLOCKLIST - Commandes INTERDITES
    # ==========================================================================
    COMMAND_BLOCKLIST: List[str] = [
        # --- Destruction de données ---
        "rm", "rmdir", "shred", "wipe",
        "mkfs", "mkswap", "fdisk", "parted", "gdisk",
        "dd",
        
        # --- Permissions & Propriété ---
        "chmod", "chown", "chgrp",
        "chattr", "setfacl",
        
        # --- Téléchargement externe ---
        "wget", "curl",
        "scp", "rsync", "sftp",
        "ftp", "tftp",
        
        # --- Accès distant ---
        "ssh", "telnet", "rsh", "rlogin",
        
        # --- Escalade de privilèges ---
        "sudo", "su", "doas",
        "pkexec", "gksudo", "kdesudo",
        "passwd", "chpasswd",
        "useradd", "userdel", "usermod",
        "groupadd", "groupdel", "groupmod",
        "visudo",
        
        # --- Services système ---
        "systemctl", "service", "init",
        "shutdown", "reboot", "poweroff", "halt",
        "telinit", "runlevel",
        
        # --- Montage & Périphériques ---
        "mount", "umount",
        "losetup", "cryptsetup",
        
        # --- Réseau - Configuration ---
        "iptables", "ip6tables", "nftables",
        "ufw", "route",
        "ifup", "ifdown", "brctl",
        
        # --- Kernel & Modules ---
        "insmod", "rmmod", "modprobe",
        "sysctl", "dmesg",
        
        # --- Cron & Tâches planifiées ---
        "crontab", "at", "batch",
        
        # --- Autres dangereux ---
        "chroot", "pivot_root",
        "unshare", "nsenter",
        "strace", "ltrace", "ptrace",
        "gdb", "lldb",
    ]


settings = Settings()
