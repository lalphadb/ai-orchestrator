"""
Tools routes - Liste et gestion des outils
"""

from app.core.security import get_current_user_optional
from app.models import ToolInfo, ToolListResponse
from app.services.react_engine.tools import BUILTIN_TOOLS
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/tools")


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
    tool_id: str, params: dict = {}, current_user: dict = Depends(get_current_user_optional)
):
    """Exécute un outil manuellement (avec gestion d'erreur robuste)"""
    import logging

    logger = logging.getLogger(__name__)

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
