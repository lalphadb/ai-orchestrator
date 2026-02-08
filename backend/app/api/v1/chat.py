"""
Chat routes - Endpoint principal pour les conversations IA
AI Orchestrator v6.2 - Avec pipeline Spec/Plan/Execute/Verify/Repair
+ Handlers WebSocket pour Re-verify et Force Repair
"""

import json
import os
import time
from collections import defaultdict

from app.core.config import settings
from app.core.database import Conversation, Message, get_db
from app.core.security import generate_uuid, get_current_user_optional
from app.models import ChatRequest, ChatResponse
from app.models.workflow import WorkflowResponse
from app.services.react_engine.workflow_engine import workflow_engine
from app.services.websocket.event_emitter import event_emitter
from fastapi import (APIRouter, Depends, HTTPException, Query, Request,
                     WebSocket, WebSocketDisconnect)
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

router = APIRouter(prefix="/chat")

# Rate limiter instance (désactivé en mode test)
TESTING = os.getenv("TESTING", "0") == "1"
limiter = Limiter(key_func=get_remote_address, enabled=not TESTING)


# === WebSocket Rate Limiter ===
class WSRateLimiter:
    """Rate limiter pour WebSocket (30 messages/minute par client)"""

    def __init__(self, max_messages: int = 30, window_seconds: int = 60):
        self.max_messages = max_messages
        self.window = window_seconds
        self.clients: dict = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        """Vérifie si le client peut envoyer un message"""
        now = time.time()

        # Nettoyer les anciens timestamps
        self.clients[client_id] = [ts for ts in self.clients[client_id] if now - ts < self.window]

        if len(self.clients[client_id]) >= self.max_messages:
            return False

        self.clients[client_id].append(now)
        return True

    def get_remaining(self, client_id: str) -> int:
        """Retourne le nombre de messages restants"""
        now = time.time()
        self.clients[client_id] = [ts for ts in self.clients[client_id] if now - ts < self.window]
        return max(0, self.max_messages - len(self.clients[client_id]))


ws_rate_limiter = WSRateLimiter(max_messages=30, window_seconds=60)


def normalize_model(model):
    """Normalise le model pour s'assurer que c'est une string"""
    if model is None:
        return settings.DEFAULT_MODEL
    if isinstance(model, dict):
        # Si c'est un dict, extraire le nom
        return model.get("name", settings.DEFAULT_MODEL)
    if isinstance(model, str):
        return model
    # Sinon, convertir en string
    return str(model)


@router.post("", response_model=WorkflowResponse)
@limiter.limit("5/minute")
async def chat(
    request: Request,  # This is the HTTP request for slowapi
    chat_request: ChatRequest,  # This is the actual chat request body
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional),
):
    """
    Endpoint de chat principal v6.2
    Utilise le WorkflowEngine avec pipeline Spec→Plan→Execute→Verify→Repair
    """

    conversation_id = chat_request.conversation_id

    if not conversation_id:
        conversation = Conversation(
            id=generate_uuid(),
            user_id=current_user["sub"] if current_user else None,
            title=(
                chat_request.message[:50] + "..."
                if len(chat_request.message) > 50
                else chat_request.message
            ),
            model=normalize_model(chat_request.model),
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
        content=chat_request.message,
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
        user_message=chat_request.message,
        conversation_id=conversation_id,
        model=normalize_model(chat_request.model),
        history=history_list,
    )

    tools_names = [t["tool"] for t in result.tools_used] if result.tools_used else []

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
    db: Session = Depends(get_db),
):
    """
    WebSocket pour chat en temps réel avec streaming

    SECURITY: Authentication via Sec-WebSocket-Protocol header
    Example: new WebSocket(url, ['Bearer.eyJ...'])

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
    from app.core.security import verify_token

    # SECURITY: Extract JWT from Sec-WebSocket-Protocol header
    token = None
    protocol_header = websocket.headers.get("sec-websocket-protocol", "")

    if protocol_header.startswith("Bearer."):
        token = protocol_header.split("Bearer.", 1)[1]
        # Accept the subprotocol
        await websocket.accept(subprotocol=f"Bearer.{token}")
    else:
        await websocket.close(code=1008, reason="Missing authentication token in protocol header")
        return

    # Validate token
    payload = verify_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Invalid or expired token")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=1008, reason="Invalid token payload")
        return

    try:
        while True:
            data = await websocket.receive_json()

            # === Rate Limiting WebSocket ===
            if not ws_rate_limiter.is_allowed(user_id):
                await websocket.send_json(
                    {
                        "type": "error",
                        "data": {
                            "message": "Rate limit dépassé (30 messages/minute)",
                            "code": "RATE_LIMIT_EXCEEDED",
                            "remaining": 0,
                        },
                    }
                )
                continue

            # === Gérer les actions spéciales ===
            action = data.get("action")

            if action == "rerun_verify":
                await handle_rerun_verify(data, websocket, db, user_id)
                continue
            elif action == "force_repair":
                await handle_force_repair(data, websocket, db, user_id)
                continue
            elif action == "get_models":
                await handle_get_models(websocket)
                continue

            # === Flux standard: message chat ===
            message = data.get("message", "")
            conversation_id = data.get("conversation_id")
            model = data.get("model")
            skip_spec = data.get("skip_spec", False)

            # Generate run_id for this run (WebSocket v8)
            import uuid

            run_id = str(uuid.uuid4())[:8]
            await event_emitter.lifecycle_tracker.start_run(run_id)

            if not message:
                await event_emitter.emit_terminal(
                    websocket, "error", run_id, {"message": "Message vide"}
                )
                continue

            # Gestion conversation
            if not conversation_id:
                conversation = Conversation(
                    id=generate_uuid(),
                    user_id=user_id,
                    title=message[:50],
                    model=normalize_model(model),
                )
                db.add(conversation)
                db.commit()
                conversation_id = conversation.id

                await event_emitter.emit(
                    websocket, "conversation_created", run_id, {"conversation_id": conversation_id}
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
            # NOTE: workflow_engine.run() handles terminal events internally
            import logging as _logging
            _chat_logger = _logging.getLogger("app.api.v1.chat")
            _chat_logger.info(f"[DEBUG Chat] Starting workflow for run {run_id}, message: {message[:80]}...")
            _chat_logger.info(f"[DEBUG Chat] Model: {normalize_model(model)}, conv_id: {conversation_id}")
            result = await workflow_engine.run(
                user_message=message,
                conversation_id=conversation_id,
                model=normalize_model(model),
                history=history_list,
                websocket=websocket,
                skip_spec=skip_spec,
                run_id=run_id,
            )

            _chat_logger.info(f"[DEBUG Chat] Workflow completed for run {run_id}, response length: {len(result.response) if result.response else 0}")
            
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
        import logging as _logging
        _logging.getLogger("app.api.v1.chat").info("[DEBUG Chat] WebSocket disconnected")
    except Exception as e:
        import logging as _logging
        import traceback
        _chat_logger = _logging.getLogger("app.api.v1.chat")
        _chat_logger.error(f"[CRITICAL Chat] Unhandled exception in websocket_chat: {e}")
        _chat_logger.error(f"[CRITICAL Chat] Traceback: {traceback.format_exc()}")
        try:
            # Try to send proper v8 error terminal event
            if 'run_id' in dir():
                await event_emitter.emit_terminal(
                    websocket, "error", run_id,
                    {"message": f"Erreur interne: {str(e)}"}
                )
            else:
                await websocket.send_json({"type": "error", "data": {"message": str(e)}})
        except Exception as send_err:
            _chat_logger.error(f"[CRITICAL Chat] Failed to send error: {send_err}")


async def handle_rerun_verify(data: dict, ws: WebSocket, db: Session, user_id: str):
    """
    Relance uniquement la phase VERIFY sur le dernier run.
    Exécute les checks QA basiques (git_status, lint).

    SECURITY: Vérifie que la conversation appartient à l'utilisateur (CRIT-003)
    """
    import uuid

    conversation_id = data.get("conversation_id")
    checks = data.get("checks")  # Optionnel: ["tests", "lint", "format", "git"]

    # Generate run_id for this rerun_verify action
    run_id = str(uuid.uuid4())[:8]
    await event_emitter.lifecycle_tracker.start_run(run_id)

    try:
        if not conversation_id:
            await event_emitter.emit_terminal(
                ws, "error", run_id, {"message": "conversation_id requis"}
            )
            return

        # SECURITY: Vérifier que la conversation appartient à l'utilisateur
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            await event_emitter.emit_terminal(
                ws, "error", run_id, {"message": "Conversation non trouvée"}
            )
            return

        if conversation.user_id != user_id:
            await event_emitter.emit_terminal(
                ws, "error", run_id, {"message": "Accès non autorisé à cette conversation"}
            )
            return

        # Vérifier qu'il y a une conversation
        last_response = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id, Message.role == "assistant")
            .order_by(Message.created_at.desc())
            .first()
        )

        if not last_response:
            await event_emitter.emit_terminal(
                ws, "error", run_id, {"message": "Aucun run à re-vérifier"}
            )
            return

        # Notifier le début
        await event_emitter.emit(
            ws,
            "phase",
            run_id,
            {
                "phase": "verify",
                "status": "starting",
                "message": "Re-vérification en cours...",
            },
        )

        # Utiliser la nouvelle méthode run_qa_checks
        verification = await workflow_engine.run_qa_checks(
            websocket=ws, run_id=run_id, checks=checks
        )

        # Déterminer le verdict
        verdict_status = "PASS" if verification.passed else "FAIL"

        # Envoyer le résultat complet (terminal event)
        await event_emitter.emit_terminal(
            ws,
            "complete",
            run_id,
            {
                "message": f"Re-vérification terminée: {verdict_status}",
                "verification": verification.model_dump(),
                "verdict": {
                    "status": verdict_status,
                    "confidence": 1.0 if verification.passed else 0.5,
                    "issues": verification.failures,
                },
                "action": "rerun_verify",
            },
        )

    except Exception as e:
        await event_emitter.emit_terminal(
            ws, "error", run_id, {"message": f"Erreur lors de la re-vérification: {str(e)}"}
        )


async def handle_force_repair(data: dict, ws: WebSocket, db: Session, user_id: str):
    """
    Force un cycle de réparation même si le verdict était PASS.
    Demande au LLM d'améliorer la réponse précédente.

    SECURITY: Vérifie que la conversation appartient à l'utilisateur (CRIT-003)
    """
    import uuid

    conversation_id = data.get("conversation_id")
    model = data.get("model", settings.DEFAULT_MODEL)

    # Generate run_id for this force_repair action
    run_id = str(uuid.uuid4())[:8]
    await event_emitter.lifecycle_tracker.start_run(run_id)

    try:
        if not conversation_id:
            await event_emitter.emit_terminal(
                ws, "error", run_id, {"message": "conversation_id requis"}
            )
            return

        # SECURITY: Vérifier que la conversation appartient à l'utilisateur
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            await event_emitter.emit_terminal(
                ws, "error", run_id, {"message": "Conversation non trouvée"}
            )
            return

        if conversation.user_id != user_id:
            await event_emitter.emit_terminal(
                ws, "error", run_id, {"message": "Accès non autorisé à cette conversation"}
            )
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
            await event_emitter.emit_terminal(
                ws, "error", run_id, {"message": "Historique insuffisant pour repair"}
            )
            return

        # Notifier le début
        await event_emitter.emit(
            ws,
            "phase",
            run_id,
            {
                "phase": "repair",
                "status": "starting",
                "message": "Réparation forcée en cours...",
            },
        )
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
        # NOTE: workflow_engine.run() handles terminal events internally
        result = await workflow_engine.run(
            user_message=repair_prompt,
            conversation_id=conversation_id,
            model=normalize_model(model),
            history=history_list,
            websocket=ws,
            skip_spec=True,
            run_id=run_id,
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

        # NOTE: Terminal event is already sent by workflow_engine.run()

    except Exception as e:
        # If workflow_engine.run() threw exception before sending terminal, send error terminal
        await event_emitter.emit_terminal(
            ws, "error", run_id, {"message": f"Erreur lors de la réparation: {str(e)}"}
        )


async def handle_get_models(ws: WebSocket):
    """
    Retourne la liste des modèles disponibles depuis Ollama.
    Utilisé pour rafraîchir la liste dans l'UI.
    """
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=settings.TIMEOUT_HEALTH_CHECK
            )

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
