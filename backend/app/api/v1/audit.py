"""
Audit routes - Logs de sécurité et audit des actions
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, BeforeValidator, ConfigDict
from typing_extensions import Annotated

StrUUID = Annotated[str, BeforeValidator(lambda v: str(v) if v is not None else v)]
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import AuditLog, get_db
from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit")


class AuditLogResponse(BaseModel):
    """Réponse pour un log d'audit"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    user_id: StrUUID | None = None
    action: str
    resource: str | None = None
    allowed: bool
    role: str | None = None
    details: str | None = None


class AuditStatsResponse(BaseModel):
    """Statistiques d'audit agrégées"""

    total_actions: int = 0
    blocked_actions: int = 0
    tools_executed: int = 0
    security_score: int = 100


@router.get("/logs")
async def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Liste des logs d'audit avec pagination"""

    query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())

    total = query.count()
    logs = query.offset(offset).limit(limit).all()

    return {
        "logs": [AuditLogResponse.model_validate(log) for log in logs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/stats")
async def get_audit_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Statistiques d'audit agrégées"""

    total_actions = db.query(func.count(AuditLog.id)).scalar() or 0
    blocked_actions = (
        db.query(func.count(AuditLog.id)).filter(AuditLog.allowed == False).scalar()  # noqa: E712
        or 0
    )
    tools_executed = (
        db.query(func.count(AuditLog.id))
        .filter(AuditLog.action.like("tool.%"))
        .filter(AuditLog.allowed == True)  # noqa: E712
        .scalar()
        or 0
    )

    # Security score: 100 - (blocked_ratio * 50) capped at 0
    if total_actions > 0:
        blocked_ratio = blocked_actions / total_actions
        security_score = max(0, int(100 - blocked_ratio * 50))
    else:
        security_score = 100

    return AuditStatsResponse(
        total_actions=total_actions,
        blocked_actions=blocked_actions,
        tools_executed=tools_executed,
        security_score=security_score,
    )
