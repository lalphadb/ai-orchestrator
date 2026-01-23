"""
Chat routes - Endpoint principal pour les conversations IA
AI Orchestrator v6.2 - Avec pipeline Spec/Plan/Execute/Verify/Repair
+ Handlers WebSocket pour Re-verify et Force Repair
"""

import json

from app.core.database import Conversation, Message, get_db
from app.core.security import generate_uuid, get_current_user_optional
from app.models import ChatRequest, ChatResponse
from app.models.workflow import WorkflowResponse
from app.services.react_engine.workflow_engine import workflow_engine
from fastapi import (APIRouter, Depends, HTTPException, Query, WebSocket,
                     WebSocketDisconnect)
from sqlalchemy.orm import Session

router = APIRouter(prefix="/chat")


def normalize_model(model):
    """Normalise le model pour s'assurer que c'est une string"""
    if model is None:
        return "kimi-k2:1t-cloud"  # Modèle par défaut
    if isinstance(model, dict):
        # Si c'est un dict, extraire le nom
        return model.get("name", "kimi-k2:1t-cloud")
    if isinstance(model, str):
        return model
    # Sinon, convertir en string
    return str(model)


@router.post("", response_model=WorkflowResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional),
):
    """
    Endpoint de chat principal v6.2
    Utilise le WorkflowEngine avec pipeline Spec→Plan→Execute→Verify→Repair
    """

    conversation_id = request.conversation_id

    if not conversation_id:
        conversation = Conversation(
            id=generate_uuid(),
            user_id=current_user["sub"] if current_user else None,
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
            model=normalize_model(request.model),
        )
        db.add(conversation)
        db.commit()
        conversation_id = conversation.id
    else:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation non trouvée")

    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.message,
    )
    db.add(user_message)
    db.commit()

    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all()
    )

    history_list = [{"role": m.role, "content": m.content} for m in history]

    result = await workflow_engine.run(
        user_message=request.message,
        conversation_id=conversation_id,
        model=normalize_model(request.model),
        history=history_list,
    )

    tools_names = [t["tool"] for t in result.tools_used] if result.tools_used else []

    if result.verification:
        json.dumps(result.verification.model_dump())

    if result.verdict:
        json.dumps(result.verdict.model_dump())

    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=result.response,
        model=result.model_used,
        tools_used=json.dumps(tools_names),
        thinking=result.thinking,
    )
    db.add(assistant_message)
    db.commit()

    result.conversation_id = conversation_id
    return result


@router.websocket("/ws")
async def websocket_chat(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
    db: Session = Depends(get_db),
):
    """
    WebSocket pour chat en temps réel avec streaming

    Authentication: Requiert un token JWT valide passé en query parameter
    Example: ws://localhost:8001/api/v1/chat/ws?token=eyJ...

    Messages supportés:
    - {message: "...", conversation_id: "...", model: "..."} - Chat normal
    - {action: "rerun_verify", conversation_id: "..."} - Relancer vérification
    - {action: "force_repair", conversation_id: "...", model: "..."} - Forcer réparation
    - {action: "get_models"} - Liste des modèles

    Messages envoyés:
    - thinking: Phase en cours
    - token: Token de streaming
    - tool: Exécution d'outil
    - phase: Changement de phase workflow
    - verification_item: Item de vérification QA
    - verification_complete: Vérification terminée (pour rerun_verify)
    - complete: Réponse finale
    - error: Erreur
    """
    # Valider le token JWT avant d'accepter la connexion
    from app.core.security import verify_token

    payload = verify_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Invalid or expired token")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=1008, reason="Invalid token payload")
        return

    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            # === Gérer les actions spéciales ===
            action = data.get("action")

            if action == "rerun_verify":
                await handle_rerun_verify(data, websocket, db)
                continue
            elif action == "force_repair":
                await handle_force_repair(data, websocket, db)
                continue
            elif action == "get_models":
                await handle_get_models(websocket)
                continue

            # === Flux standard: message chat ===
            message = data.get("message", "")
            conversation_id = data.get("conversation_id")
            model = data.get("model")
            skip_spec = data.get("skip_spec", False)

            if not message:
                await websocket.send_json({"type": "error", "data": "Message vide"})
                continue

            # Gestion conversation
            if not conversation_id:
                conversation = Conversation(
                    id=generate_uuid(),
                    title=message[:50],
                    model=normalize_model(model),
                )
                db.add(conversation)
                db.commit()
                conversation_id = conversation.id

                await websocket.send_json(
                    {"type": "conversation_created", "data": {"id": conversation_id}}
                )

            # Sauvegarder message user
            user_msg = Message(
                conversation_id=conversation_id,
                role="user",
                content=message,
            )
            db.add(user_msg)
            db.commit()

            # Historique
            history = (
                db.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
                .all()
            )

            history_list = [{"role": m.role, "content": m.content} for m in history]

            # Exécuter via WorkflowEngine avec WebSocket
            result = await workflow_engine.run(
                user_message=message,
                conversation_id=conversation_id,
                model=normalize_model(model),
                history=history_list,
                websocket=websocket,
                skip_spec=skip_spec,
            )

            # Sauvegarder réponse
            tools_names = [t["tool"] for t in result.tools_used] if result.tools_used else []

            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=result.response,
                model=result.model_used,
                tools_used=json.dumps(tools_names),
                thinking=result.thinking,
            )
            db.add(assistant_msg)
            db.commit()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "data": str(e)})
        except Exception:
            pass


async def handle_rerun_verify(data: dict, ws: WebSocket, db: Session):
    """
    Relance uniquement la phase VERIFY sur le dernier run.
    Exécute les checks QA basiques (git_status, lint).
    """
    conversation_id = data.get("conversation_id")
    checks = data.get("checks")  # Optionnel: ["tests", "lint", "format", "git"]

    if not conversation_id:
        await ws.send_json({"type": "error", "data": "conversation_id requis"})
        return

    # Vérifier qu'il y a une conversation
    last_response = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id, Message.role == "assistant")
        .order_by(Message.created_at.desc())
        .first()
    )

    if not last_response:
        await ws.send_json({"type": "error", "data": "Aucun run à re-vérifier"})
        return

    # Notifier le début
    await ws.send_json(
        {
            "type": "phase",
            "data": {
                "phase": "verify",
                "status": "running",
                "message": "Re-vérification en cours...",
            },
        }
    )

    try:
        # Utiliser la nouvelle méthode run_qa_checks
        verification = await workflow_engine.run_qa_checks(
            websocket=ws, run_id=conversation_id[:8], checks=checks
        )

        # Déterminer le verdict
        verdict_status = "PASS" if verification.passed else "FAIL"

        # Envoyer le résultat complet
        await ws.send_json(
            {
                "type": "verification_complete",
                "data": {
                    "verification": verification.model_dump(),
                    "verdict": {
                        "status": verdict_status,
                        "confidence": 1.0 if verification.passed else 0.5,
                        "issues": verification.failures,
                    },
                    "action": "rerun_verify",
                    "message": f"Re-vérification terminée: {verdict_status}",
                },
            }
        )

        # Phase complete
        await ws.send_json({"type": "phase", "data": {"phase": "complete", "status": "completed"}})

    except Exception as e:
        await ws.send_json(
            {"type": "error", "data": f"Erreur lors de la re-vérification: {str(e)}"}
        )


async def handle_force_repair(data: dict, ws: WebSocket, db: Session):
    """
    Force un cycle de réparation même si le verdict était PASS.
    Demande au LLM d'améliorer la réponse précédente.
    """
    conversation_id = data.get("conversation_id")
    model = data.get("model", "kimi-k2:1t-cloud")

    if not conversation_id:
        await ws.send_json({"type": "error", "data": "conversation_id requis"})
        return

    # Récupérer la dernière conversation
    last_user = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id, Message.role == "user")
        .order_by(Message.created_at.desc())
        .first()
    )

    last_assistant = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id, Message.role == "assistant")
        .order_by(Message.created_at.desc())
        .first()
    )

    if not last_user or not last_assistant:
        await ws.send_json({"type": "error", "data": "Historique insuffisant pour repair"})
        return

    # Notifier le début
    await ws.send_json(
        {
            "type": "phase",
            "data": {
                "phase": "repair",
                "status": "running",
                "message": "Réparation forcée en cours...",
            },
        }
    )

    try:
        # Construire le contexte de réparation
        repair_prompt = f"""[REPAIR MODE] Tu dois améliorer/réparer la réponse précédente.

QUESTION ORIGINALE:
{last_user.content}

RÉPONSE À AMÉLIORER:
{last_assistant.content}

INSTRUCTIONS:
1. Analyse les problèmes potentiels de la réponse
2. Corrige les erreurs ou inexactitudes
3. Améliore la clarté et la complétude
4. Génère une meilleure réponse

Réponds directement avec la version améliorée."""

        # Historique (sans inclure le repair prompt)
        history = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .all()
        )
        history_list = [{"role": m.role, "content": m.content} for m in history]

        # Relancer avec le prompt de repair
        result = await workflow_engine.run(
            user_message=repair_prompt,
            conversation_id=conversation_id,
            model=normalize_model(model),
            history=history_list,
            websocket=ws,
            skip_spec=True,
        )

        # Sauvegarder la nouvelle réponse
        tools_names = [t["tool"] for t in result.tools_used] if result.tools_used else []

        repair_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=result.response,
            model=result.model_used,
            tools_used=json.dumps(tools_names),
            thinking=result.thinking,
        )
        db.add(repair_msg)
        db.commit()

    except Exception as e:
        await ws.send_json({"type": "error", "data": f"Erreur lors de la réparation: {str(e)}"})


async def handle_get_models(ws: WebSocket):
    """
    Retourne la liste des modèles disponibles depuis Ollama.
    Utilisé pour rafraîchir la liste dans l'UI.
    """
    import httpx
    from app.core.config import settings

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=10)

            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])

                await ws.send_json(
                    {"type": "models", "data": {"models": models, "count": len(models)}}
                )
            else:
                await ws.send_json(
                    {"type": "error", "data": f"Erreur Ollama: HTTP {response.status_code}"}
                )

    except Exception as e:
        await ws.send_json({"type": "error", "data": f"Erreur: {str(e)}"})


# === ENDPOINTS LEGACY (compatibilité) ===


@router.post("/simple", response_model=ChatResponse)
async def chat_simple(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional),
):
    """
    Endpoint de chat simplifié (sans spec/plan/verify)
    Pour compatibilité avec l'ancienne API
    """

    conversation_id = request.conversation_id

    if not conversation_id:
        conversation = Conversation(
            id=generate_uuid(),
            user_id=current_user["sub"] if current_user else None,
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
            model=normalize_model(request.model),
        )
        db.add(conversation)
        db.commit()
        conversation_id = conversation.id

    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.message,
    )
    db.add(user_message)
    db.commit()

    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all()
    )

    history_list = [{"role": m.role, "content": m.content} for m in history]

    result = await workflow_engine.run(
        user_message=request.message,
        conversation_id=conversation_id,
        model=normalize_model(request.model),
        history=history_list,
        skip_spec=True,
    )

    tools_names = [t["tool"] for t in result.tools_used] if result.tools_used else []

    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=result.response,
        model=result.model_used,
        tools_used=json.dumps(tools_names),
    )
    db.add(assistant_msg)
    db.commit()

    return ChatResponse(
        response=result.response,
        conversation_id=conversation_id,
        model_used=result.model_used,
        tools_used=result.tools_used,
        iterations=result.iterations,
        thinking=result.thinking,
        duration_ms=result.duration_ms,
    )
