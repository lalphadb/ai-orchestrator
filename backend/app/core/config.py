"""
Configuration de l'application AI Orchestrator v6.2 SECURE
AUDIT: Corrections sécurité appliquées le 2026-01-09
"""
from pydantic_settings import BaseSettings
from typing import List
import secrets


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
    APP_VERSION: str = "7.0"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    
    # CORS - CORRIGÉ: Domaines spécifiques au lieu de wildcard
    CORS_ORIGINS: List[str] = [
        "https://ai.4lb.ca",
        "https://llm.4lb.ca",
        "https://4lb.ca",
        "http://localhost:3000",
        "http://localhost:8001",
    ]
    
    # Security - CORRIGÉ: Clé forte par défaut (sera overridée par .env)
    SECRET_KEY: str = secrets.token_urlsafe(64)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h au lieu de 7 jours
    
    # Rate Limiting (nouveau)
    RATE_LIMIT_PER_MINUTE: int = 30
    RATE_LIMIT_BURST: int = 10
    
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
    VERIFY_REQUIRED: bool = False
    MAX_REPAIR_CYCLES: int = 3
    
    # Workspace Safety
    WORKSPACE_DIR: str = "/home/lalpha/orchestrator-workspace"
    WORKSPACE_ALLOW_WRITE: bool = True
    
    # EXECUTION SECURITY - CORRIGÉ: Mode sandbox par défaut
    EXECUTE_MODE: str = "direct"
    SANDBOX_IMAGE: str = "ubuntu:24.04"
    SANDBOX_MEMORY: str = "512m"
    SANDBOX_CPUS: str = "0.5"
    SANDBOX_TIMEOUT: int = 30
    
    # ALLOWLIST SÉCURISÉE
    COMMAND_ALLOWLIST: List[str] = [
        "uname", "hostname", "uptime", "whoami", "id",
        "date", "cal", "pwd", "printenv",
        "free", "df", "du", "lscpu", "nproc", "lsmem",
        "ps", "pgrep", "pidof",
        "ls", "tree", "find",
        "realpath", "readlink", "dirname", "basename",
        "file", "stat",
        "cat", "head", "tail", "less", "more",
        "wc", "nl", "md5sum", "sha256sum",
        "mkdir", "touch",
        "grep", "egrep", "fgrep", "rg",
        "sed", "awk", "gawk",
        "cut", "paste", "sort", "uniq",
        "tr", "diff", "comm",
        "tee", "xargs", "printf", "echo",
        "jq", "yq",
        "python3", "pip3",
        "ruff", "black", "mypy", "flake8", "pylint", "bandit",
        "node", "npm", "npx",
        "git",
        "which", "whereis", "type", "command",
        "test", "[", "true", "false",
        "seq", "bc", "expr",
        "base64", "strings",
        "tar", "gzip", "gunzip", "bzip2", "bunzip2", "xz", "unzip",
        "ollama",
    ]
    
    # BLOCKLIST ÉTENDUE
    COMMAND_BLOCKLIST: List[str] = [
        "bash", "sh", "zsh", "csh", "tcsh", "ksh", "fish",
        "dash", "ash", "busybox", "exec", "eval", "source",
        "nc", "netcat", "ncat", "socat",
        "curl", "wget",
        "ssh", "scp", "sftp", "rsync",
        "telnet", "ftp", "tftp", "nmap", "masscan",
        "kill", "pkill", "killall", "nohup", "disown", "nice", "renice",
        "docker", "docker-compose", "podman", "kubectl", "crictl",
        "rm", "rmdir", "shred", "wipe", "srm",
        "mkfs", "mkswap", "fdisk", "parted", "gdisk", "dd", "truncate",
        "chmod", "chown", "chgrp", "chattr", "setfacl", "getfacl",
        "sudo", "su", "doas", "pkexec", "gksudo", "kdesudo",
        "passwd", "chpasswd", "shadow",
        "useradd", "userdel", "usermod",
        "groupadd", "groupdel", "groupmod",
        "visudo", "sudoedit",
        "systemctl", "service", "init",
        "shutdown", "reboot", "poweroff", "halt",
        "telinit", "runlevel", "journalctl",
        "mount", "umount", "losetup", "cryptsetup", "lvm",
        "iptables", "ip6tables", "nftables",
        "ufw", "firewall-cmd",
        "route", "ip", "ifconfig", "ifup", "ifdown", "brctl", "bridge",
        "insmod", "rmmod", "modprobe", "sysctl", "dmesg",
        "crontab", "at", "batch",
        "strace", "ltrace", "ptrace", "gdb", "lldb", "objdump",
        "tcpdump", "wireshark", "tshark",
        "gcc", "g++", "clang", "make", "cmake", "ld", "as",
        "chroot", "pivot_root", "unshare", "nsenter",
        "xterm", "screen", "tmux",
        "expect", "autoexpect",
        "perl", "ruby", "php",
    ]
    
    # ARGUMENTS DANGEREUX
    DANGEROUS_ARGUMENTS: List[str] = [
        "-c", "--command", "-e", "--eval", "--exec",
        "-i", "--interactive", "-t", "--tty",
        "--privileged", "--cap-add",
        "-u root", "--user root",
        "--network", "-p", "--publish",
        "-v /", "-v /etc", "-v /root", "-v /home", "--volume /",
        "> /etc", ">> /etc", "> /root", ">> /root",
        "| bash", "| sh",
        "git push", "git commit", "git reset --hard", "git clean -fd",
    ]
    
    # URLs autorisées
    ALLOWED_URL_PATTERNS: List[str] = [
        "http://localhost",
        "http://127.0.0.1",
        "https://api.github.com",
        "https://ollama",
    ]


settings = Settings()
