"""
Configuration du logging structuré pour AI Orchestrator v7.1

Support:
- Logs texte (development)
- Logs JSON (production, parsing automatisé)
- Request tracing avec request_id
"""

import logging
import sys
from datetime import datetime, timezone
from typing import Any

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Formatter JSON personnalisé pour logs structurés.

    Ajoute automatiquement:
    - timestamp (ISO8601 UTC)
    - level (INFO, ERROR, etc.)
    - logger (nom du logger)
    - request_id (si disponible)
    """

    def add_fields(
        self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]
    ) -> None:
        """Ajoute des champs personnalisés aux logs JSON"""
        super().add_fields(log_record, record, message_dict)

        # Timestamp ISO8601 UTC
        log_record["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Niveau de log
        log_record["level"] = record.levelname

        # Nom du logger (module source)
        log_record["logger"] = record.name

        # Request ID si disponible (ajouté par middleware)
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id

        # User ID si disponible
        if hasattr(record, "user_id"):
            log_record["user_id"] = record.user_id

        # Tool name si disponible
        if hasattr(record, "tool_name"):
            log_record["tool_name"] = record.tool_name

        # Duration si disponible
        if hasattr(record, "duration_ms"):
            log_record["duration_ms"] = record.duration_ms


def setup_logging(level: str = "INFO", format_type: str = "text") -> None:
    """
    Configure le logging global de l'application.

    Args:
        level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format des logs ("text" ou "json")

    Example:
        setup_logging(level="INFO", format_type="json")
    """
    handler = logging.StreamHandler(sys.stdout)

    if format_type == "json":
        # Format JSON pour production (parsable par Loki, ELK, etc.)
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s",
            rename_fields={
                "levelname": "level",
                "name": "logger",
                "asctime": "timestamp",
            },
        )
    else:
        # Format texte pour development (human-readable)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Supprimer les handlers existants
    root_logger.handlers = []
    root_logger.addHandler(handler)

    # Configuration pour loggers spécifiques (éviter verbosité)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger_with_context(name: str, **context: Any) -> logging.LoggerAdapter:
    """
    Crée un logger avec contexte permanent (request_id, user_id, etc.)

    Args:
        name: Nom du logger
        **context: Contexte à ajouter à tous les logs

    Returns:
        LoggerAdapter avec contexte

    Example:
        logger = get_logger_with_context(__name__, request_id="abc123", user_id="user_1")
        logger.info("Processing request")  # Inclut automatiquement request_id et user_id
    """
    logger = logging.getLogger(name)
    return logging.LoggerAdapter(logger, context)
