"""
Service d'audit - Persistance des logs d'actions
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from app.core.database import AuditLog, get_db_session

logger = logging.getLogger(__name__)


def log_action(
    action: str,
    resource: Optional[str] = None,
    allowed: bool = True,
    role: Optional[str] = None,
    command: Optional[str] = None,
    parameters: Optional[dict] = None,
    result: Optional[str] = None,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> bool:
    """
    Enregistre une action dans les logs d'audit.

    Args:
        action: Type d'action (tool_execute, login, file_access, etc.)
        resource: Ressource concernee
        allowed: Action autorisee ou refusee
        role: Role de l'utilisateur (VIEWER, OPERATOR, ADMIN)
        command: Commande executee (si applicable)
        parameters: Parametres de l'action (dict converti en JSON)
        result: Resultat ou message d'erreur
        user_id: ID utilisateur
        ip_address: Adresse IP
        user_agent: User-Agent du client

    Returns:
        True si succes, False sinon
    """
    try:
        db = get_db_session()

        # Merge command, parameters, result into details JSONB
        details = {}
        if command:
            details["command"] = command
        if parameters:
            details["parameters"] = parameters
        if result:
            details["result"] = result[:1000]

        audit_entry = AuditLog(
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            action=action,
            resource=resource,
            allowed=allowed,
            role=role,
            details=json.dumps(details) if details else None,
            ip_address=ip_address,
            user_agent=user_agent[:255] if user_agent else None,
        )

        db.add(audit_entry)
        db.commit()
        db.close()

        logger.debug(f"Audit log: {action} on {resource} - {'allowed' if allowed else 'denied'}")
        return True

    except Exception as e:
        logger.error(f"Failed to log audit: {e}")
        return False


def get_audit_logs(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    allowed: Optional[bool] = None,
    limit: int = 100,
) -> list:
    """
    Recupere les logs d'audit avec filtres optionnels.
    """
    try:
        db = get_db_session()
        query = db.query(AuditLog)

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if allowed is not None:
            query = query.filter(AuditLog.allowed == allowed)

        logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
        db.close()

        return [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "user_id": log.user_id,
                "action": log.action,
                "resource": log.resource,
                "allowed": log.allowed,
                "role": log.role,
                "details": json.loads(log.details) if log.details else {},
            }
            for log in logs
        ]

    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        return []
