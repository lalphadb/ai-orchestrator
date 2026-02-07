"""
Logging filters to prevent secrets from being logged
AI Orchestrator v7.0 - Security Enhancement
"""

import logging
import re
from typing import Pattern


class SecretFilter(logging.Filter):
    """
    Filtre de logging qui masque les secrets sensibles avant l'écriture.

    Patterns détectés:
    - JWT tokens (Bearer xxx)
    - Passwords dans les logs
    - API keys
    - Secret keys
    - Hashes bcrypt
    """

    # Patterns de secrets à masquer
    PATTERNS = [
        # JWT tokens (Bearer authentication)
        (re.compile(r"Bearer\s+([A-Za-z0-9_-]+\.){2}[A-Za-z0-9_-]+"), "Bearer ***JWT_TOKEN***"),
        # Authorization headers
        (
            re.compile(r"Authorization:\s*Bearer\s+[^\s]+", re.IGNORECASE),
            "Authorization: Bearer ***TOKEN***",
        ),
        (re.compile(r"Authorization:\s*[^\s]+", re.IGNORECASE), "Authorization: ***TOKEN***"),
        # Passwords in various formats
        (re.compile(r'"password"\s*:\s*"[^"]*"', re.IGNORECASE), '"password": "***"'),
        (re.compile(r"'password'\s*:\s*'[^']*'", re.IGNORECASE), "'password': '***'"),
        (re.compile(r"password=[^\s&]+", re.IGNORECASE), "password=***"),
        (re.compile(r"passwd=[^\s&]+", re.IGNORECASE), "passwd=***"),
        (re.compile(r"pwd=[^\s&]+", re.IGNORECASE), "pwd=***"),
        # Hashed passwords (bcrypt, argon2, etc.)
        (re.compile(r"\$2[aby]\$\d+\$[./A-Za-z0-9]{53}"), "***BCRYPT_HASH***"),
        (re.compile(r"\$argon2[id]{0,2}\$[^\s]+"), "***ARGON2_HASH***"),
        # Secret keys / API keys
        (re.compile(r'"secret_key"\s*:\s*"[^"]*"', re.IGNORECASE), '"secret_key": "***"'),
        (re.compile(r'"api_key"\s*:\s*"[^"]*"', re.IGNORECASE), '"api_key": "***"'),
        (re.compile(r'"apikey"\s*:\s*"[^"]*"', re.IGNORECASE), '"apikey": "***"'),
        (re.compile(r"api_key=[^\s&]+", re.IGNORECASE), "api_key=***"),
        (re.compile(r"apikey=[^\s&]+", re.IGNORECASE), "apikey=***"),
        # JWT_SECRET_KEY
        (re.compile(r"JWT_SECRET_KEY=[^\s]+", re.IGNORECASE), "JWT_SECRET_KEY=***"),
        (re.compile(r'"JWT_SECRET_KEY"\s*:\s*"[^"]*"', re.IGNORECASE), '"JWT_SECRET_KEY": "***"'),
        # GROQ API keys (format: gsk_xxx)
        (re.compile(r"gsk_[A-Za-z0-9]{48,}"), "gsk_***GROQ_API_KEY***"),
        # OpenAI API keys (format: sk-xxx)
        (re.compile(r"sk-[A-Za-z0-9]{48,}"), "sk-***OPENAI_API_KEY***"),
        # Generic tokens/keys (long alphanumeric strings)
        (re.compile(r'"token"\s*:\s*"[A-Za-z0-9_-]{32,}"', re.IGNORECASE), '"token": "***"'),
        (re.compile(r"token=[A-Za-z0-9_-]{32,}", re.IGNORECASE), "token=***"),
        # Access tokens
        (re.compile(r'"access_token"\s*:\s*"[^"]*"', re.IGNORECASE), '"access_token": "***"'),
        (re.compile(r"access_token=[^\s&]+", re.IGNORECASE), "access_token=***"),
        # Database URLs avec credentials
        (re.compile(r"postgresql://[^:]+:[^@]+@", re.IGNORECASE), "postgresql://***:***@"),
        (re.compile(r"mysql://[^:]+:[^@]+@", re.IGNORECASE), "mysql://***:***@"),
        (re.compile(r"mongodb://[^:]+:[^@]+@", re.IGNORECASE), "mongodb://***:***@"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filtre l'enregistrement de log pour masquer les secrets.

        Args:
            record: Enregistrement de log

        Returns:
            True pour permettre le log (après filtrage)
        """
        # Filtrer le message principal
        if hasattr(record, "msg") and isinstance(record.msg, str):
            record.msg = self._mask_secrets(record.msg)

        # Filtrer les arguments
        if hasattr(record, "args") and record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._mask_secrets(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(
                    self._mask_secrets(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )

        # Toujours retourner True pour permettre le log
        return True

    def _mask_secrets(self, text: str) -> str:
        """
        Masque les secrets dans le texte.

        Args:
            text: Texte à filtrer

        Returns:
            Texte avec les secrets masqués
        """
        for pattern, replacement in self.PATTERNS:
            text = pattern.sub(replacement, text)

        return text


# Instance globale du filtre
secret_filter = SecretFilter()


def add_secret_filter_to_logger(logger_name: str = None):
    """
    Ajoute le filtre de secrets à un logger.

    Args:
        logger_name: Nom du logger (None = root logger)
    """
    logger = logging.getLogger(logger_name)

    # Vérifier si le filtre n'est pas déjà présent
    if not any(isinstance(f, SecretFilter) for f in logger.filters):
        logger.addFilter(secret_filter)


def add_secret_filter_to_all_loggers():
    """
    Ajoute le filtre de secrets à tous les loggers actifs.
    """
    # Root logger
    add_secret_filter_to_logger(None)

    # Loggers applicatifs
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi", "app"]:
        add_secret_filter_to_logger(logger_name)


# Tests unitaires (pour validation)
if __name__ == "__main__":
    # Test des patterns
    test_cases = [
        (
            "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature",
            "Authorization: Bearer ***TOKEN***",
        ),
        ('"password": "super_secret_123"', '"password": "***"'),
        ("JWT_SECRET_KEY=abcd1234efgh5678", "JWT_SECRET_KEY=***"),
        ("gsk_1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQ", "gsk_***GROQ_API_KEY***"),
        ("postgresql://user:pass123@localhost/db", "postgresql://***:***@localhost/db"),
        ('"access_token": "abc123def456"', '"access_token": "***"'),
    ]

    filter_instance = SecretFilter()

    print("🧪 Test du filtre de secrets:\n")
    for original, expected in test_cases:
        masked = filter_instance._mask_secrets(original)
        status = "✅" if expected in masked else "❌"
        print(f"{status} {original[:50]}...")
        print(f"   → {masked}\n")
