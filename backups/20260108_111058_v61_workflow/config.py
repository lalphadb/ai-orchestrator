"""
Configuration centralisée avec validation Pydantic
AI Orchestrator v6.1 - Pipeline Spec/Plan/Execute/Verify/Repair
"""
import os
from functools import lru_cache
from typing import List, Optional, Literal
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration de l'application"""
    
    # Application
    APP_NAME: str = "AI Orchestrator"
    APP_VERSION: str = "6.1.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    WORKERS: int = 1
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 heures
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/orchestrator.db"
    
    # ====== AGENT ROLES (Nouveau v6.1) ======
    # Modèle principal pour l'exécution des tâches
    EXECUTOR_MODEL: str = "qwen2.5-coder:32b-instruct-q4_K_M"
    # Modèle secondaire pour la vérification critique
    VERIFIER_MODEL: str = "deepseek-coder:33b"
    
    # Ollama (legacy - utilisé comme fallback)
    OLLAMA_URL: str = "http://localhost:11434"
    DEFAULT_MODEL: str = "qwen2.5-coder:32b-instruct-q4_K_M"
    FALLBACK_MODEL: str = "llama3.2:latest"
    
    # Models disponibles
    AVAILABLE_MODELS: List[str] = [
        "qwen2.5-coder:32b-instruct-q4_K_M",
        "deepseek-coder:33b",
        "qwen3-vl:32b",
        "llama3.2-vision:11b",
        "gemini-3-pro-preview",
        "kimi-k2:1t-cloud",
        "qwen3-coder:480b-cloud",
    ]
    
    # ====== WORKFLOW (Nouveau v6.1) ======
    # Vérification obligatoire avant de conclure
    VERIFY_REQUIRED: bool = True
    # Nombre max de cycles de réparation
    MAX_REPAIR_CYCLES: int = 3
    
    # ====== WORKSPACE SAFETY (Nouveau v6.1) ======
    # Répertoire de travail isolé
    WORKSPACE_DIR: str = "/home/lalpha/orchestrator-workspace"
    # Autoriser l'écriture dans le workspace
    WORKSPACE_ALLOW_WRITE: bool = True
    
    # ====== COMMAND EXECUTION HARDENING (Nouveau v6.1) ======
    # Mode d'exécution: sandbox (Docker) ou host (direct)
    EXECUTE_MODE: Literal["sandbox", "host"] = "sandbox"
    # Image Docker pour le sandbox
    SANDBOX_IMAGE: str = "ubuntu:24.04"
    # Limite mémoire sandbox
    SANDBOX_MEMORY: str = "1024m"
    # Limite CPU sandbox
    SANDBOX_CPUS: str = "1"
    
    # Commandes autorisées (allowlist) - binaires uniquement
    COMMAND_ALLOWLIST: List[str] = [
        "git", "python", "python3", "pip", "pip3",
        "pytest", "node", "npm", "pnpm", "npx",
        "ruff", "black", "mypy", "flake8",
        "uvicorn", "alembic",
        "ls", "cat", "head", "tail", "grep", "find", "wc",
        "echo", "date", "pwd", "env",
        "mkdir", "cp", "mv", "touch",
    ]
    
    # Commandes interdites (blocklist) - sécurité supplémentaire
    COMMAND_BLOCKLIST: List[str] = [
        "rm", "rmdir", "mkfs", "dd", "chmod", "chown",
        "wget", "curl", "ssh", "scp", "rsync",
        "sudo", "su", "passwd", "useradd", "userdel",
        "systemctl", "service", "init", "shutdown", "reboot",
        "mount", "umount", "fdisk", "parted",
        "iptables", "ufw", "firewall-cmd",
    ]
    
    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION: str = "orchestrator_memory"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # secondes
    
    # ReAct Engine
    MAX_ITERATIONS: int = 10
    THINKING_TIMEOUT: int = 120  # secondes
    TOOL_TIMEOUT: int = 30  # secondes par outil
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Singleton pour les settings"""
    return Settings()


settings = get_settings()
