"""
Tools routes - Liste et gestion des outils
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import User, get_db
from app.core.security import get_current_user, get_current_user_optional
from app.models import ToolInfo, ToolListResponse
from app.services.react_engine.tools import BUILTIN_TOOLS

router = APIRouter(prefix="/tools")
logger = logging.getLogger(__name__)

# SECURITY: Liste des outils nécessitant des permissions admin
ADMIN_REQUIRED_TOOLS = {
    "execute_command",
    "write_file",
    "run_build",
    "git_commit",
    "git_push",
}


@router.get("", response_model=ToolListResponse)
async def list_tools(current_user: dict = Depends(get_current_user_optional)):
    """Liste tous les outils disponibles"""

    tools_list = BUILTIN_TOOLS.list_tools()

    tools = [
        ToolInfo(
            id=t["id"],
            name=t["name"],
            description=t.get("description"),
            category=t.get("category", "general"),
            enabled=True,
            usage_count=0,
            parameters=t.get("parameters"),
        )
        for t in tools_list
    ]

    categories = list(set(t.category for t in tools))

    return ToolListResponse(tools=tools, total=len(tools), categories=categories)


@router.get("/{tool_id}", response_model=ToolInfo)
async def get_tool(tool_id: str, current_user: dict = Depends(get_current_user_optional)):
    """Récupère les détails d'un outil"""

    tool = BUILTIN_TOOLS.get(tool_id)

    if not tool:
        raise HTTPException(status_code=404, detail="Outil non trouvé")

    return ToolInfo(
        id=tool_id,
        name=tool["name"],
        description=tool.get("description"),
        category=tool.get("category", "general"),
        enabled=True,
        usage_count=tool.get("usage_count", 0),
        parameters=tool.get("parameters"),
    )


@router.post("/{tool_id}/execute")
async def execute_tool(
    tool_id: str,
    params: dict = {},
    current_user: dict = Depends(get_current_user),  # SECURITY: Authentication REQUIRED
    db: Session = Depends(get_db),  # SECURITY: For DB admin check
):
    """
    Exécute un outil manuellement (avec gestion d'erreur robuste).

    SECURITY:
    - Authentication requise (get_current_user)
    - Outils sensibles nécessitent admin
    - Role downgrade automatique pour execute_command si non-admin
    """

    try:
        # Vérifier que l'outil existe
        tool = BUILTIN_TOOLS.get(tool_id)
        if not tool:
            return {
                "success": False,
                "tool": tool_id,
                "params": params,
                "result": None,
                "error": {
                    "code": "E_TOOL_NOT_FOUND",
                    "message": f"Tool '{tool_id}' does not exist",
                    "recoverable": False,
                },
            }

        # SECURITY: Vérifier les permissions pour les outils sensibles
        if tool_id in ADMIN_REQUIRED_TOOLS:
            # SECURITY SCEN-10: Double-check admin status in database (not just JWT)
            user = db.query(User).filter(User.id == current_user["sub"]).first()

            # Detect JWT/DB mismatch (privilege escalation attempt)
            jwt_admin = current_user.get("is_admin", False)
            db_admin = user.is_admin if user else False

            if jwt_admin != db_admin:
                logger.critical(
                    f"⚠️ PRIVILEGE ESCALATION ATTEMPT: User {current_user['sub']} "
                    f"JWT says admin={jwt_admin} but DB says admin={db_admin}"
                )

            if not db_admin:
                logger.warning(
                    f"🔒 Non-admin user {current_user.get('username')} "
                    f"attempted to execute admin tool: {tool_id}"
                )
                return {
                    "success": False,
                    "tool": tool_id,
                    "params": params,
                    "result": None,
                    "error": {
                        "code": "E_FORBIDDEN",
                        "message": f"Tool '{tool_id}' requires admin privileges",
                        "recoverable": False,
                    },
                }

        # SECURITY: Forcer role="operator" pour execute_command si pas admin
        if tool_id == "execute_command" and not current_user.get("is_admin", False):
            original_role = params.get("role", "operator")
            if original_role == "admin":
                logger.warning(
                    f"🔒 Downgrading role from 'admin' to 'operator' for user {current_user.get('username')}"
                )
                params["role"] = "operator"

        # Exécuter l'outil
        result = await BUILTIN_TOOLS.execute(tool_id, **params)

        # Vérifier si le résultat indique une erreur
        if hasattr(result, "success") and not result.success:
            return {
                "success": False,
                "tool": tool_id,
                "params": params,
                "result": result.dict() if hasattr(result, "dict") else result,
                "error": result.error if hasattr(result, "error") else None,
            }

        return {
            "success": True,
            "tool": tool_id,
            "params": params,
            "result": result.dict() if hasattr(result, "dict") else result,
            "error": None,
        }

    except Exception as e:
        logger.exception(f"Tool execution failed: {tool_id}")
        return {
            "success": False,
            "tool": tool_id,
            "params": params,
            "result": None,
            "error": {"code": "E_TOOL_EXECUTION", "message": str(e), "recoverable": False},
        }
