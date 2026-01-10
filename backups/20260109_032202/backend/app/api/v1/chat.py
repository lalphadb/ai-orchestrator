"""
Chat routes - Endpoint principal pour les conversations IA
AI Orchestrator v6.1 - Avec pipeline Spec/Plan/Execute/Verify/Repair
"""
import json
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db, Conversation, Message
from app.core.security import get_current_user_optional, generate_uuid
from app.services.react_engine.workflow_engine import workflow_engine
from app.models import ChatRequest, ChatResponse
from app.models.workflow import WorkflowResponse

router = APIRouter(prefix="/chat")


@router.post("", response_model=WorkflowResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional)
):
    """
    Endpoint de chat principal v6.1
    Utilise le WorkflowEngine avec pipeline Spec→Plan→Execute→Verify→Repair
    
    Retourne:
    - response: Réponse générée
    - verification: Rapport de vérification QA (si applicable)
    - verdict: Verdict du Verifier PASS/FAIL (si applicable)
    - tools_used: Outils utilisés
    - repair_cycles: Nombre de cycles de réparation effectués
    """
    
    # Gestion de la conversation
    conversation_id = request.conversation_id
    
    if not conversation_id:
        # Créer nouvelle conversation
        conversation = Conversation(
            id=generate_uuid(),
            user_id=current_user["sub"] if current_user else None,
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
            model=request.model,
        )
        db.add(conversation)
        db.commit()
        conversation_id = conversation.id
    else:
        # Vérifier que la conversation existe
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation non trouvée")
    
    # Sauvegarder le message utilisateur
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.message,
    )
    db.add(user_message)
    db.commit()
    
    # Récupérer l'historique
    history = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()
    
    history_list = [
        {"role": m.role, "content": m.content}
        for m in history
    ]
    
    # Exécuter via WorkflowEngine
    result = await workflow_engine.run(
        user_message=request.message,
        conversation_id=conversation_id,
        model=request.model,
        history=history_list,
    )
    
    # Sauvegarder la réponse avec métadonnées enrichies
    tools_names = [t["tool"] for t in result.tools_used] if result.tools_used else []
    
    # Metadata pour la vérification
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
        # Note: Ajouter ces colonnes à la DB si nécessaire
        # verification=verification_json,
        # verdict=verdict_json,
    )
    db.add(assistant_message)
    db.commit()
    
    # Retourner la réponse enrichie
    result.conversation_id = conversation_id
    return result


@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket pour chat en temps réel avec streaming
    
    Messages envoyés:
    - thinking: Phase en cours (spec, plan, execute, verify, repair)
    - token: Token de streaming
    - tool: Exécution d'outil
    - complete: Réponse finale avec verification et verdict
    - error: Erreur
    """
    await websocket.accept()
    
    try:
        while True:
            # Recevoir message
            data = await websocket.receive_json()
            
            message = data.get("message", "")
            conversation_id = data.get("conversation_id")
            model = data.get("model")
            skip_spec = data.get("skip_spec", False)  # Nouveau: permet de skip spec/plan
            
            if not message:
                await websocket.send_json({"type": "error", "data": "Message vide"})
                continue
            
            # Gestion conversation
            if not conversation_id:
                conversation = Conversation(
                    id=generate_uuid(),
                    title=message[:50],
                    model=model,
                )
                db.add(conversation)
                db.commit()
                conversation_id = conversation.id
                
                await websocket.send_json({
                    "type": "conversation_created",
                    "data": {"id": conversation_id}
                })
            
            # Sauvegarder message user
            user_msg = Message(
                conversation_id=conversation_id,
                role="user",
                content=message,
            )
            db.add(user_msg)
            db.commit()
            
            # Historique
            history = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at).all()
            
            history_list = [{"role": m.role, "content": m.content} for m in history]
            
            # Exécuter via WorkflowEngine avec WebSocket
            result = await workflow_engine.run(
                user_message=message,
                conversation_id=conversation_id,
                model=model,
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
            
            # Note: Le message "complete" est déjà envoyé par workflow_engine
            # avec verification et verdict inclus
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "data": str(e)})
        except Exception:
            pass


# Endpoint de compatibilité (legacy)
@router.post("/simple", response_model=ChatResponse)
async def chat_simple(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional)
):
    """
    Endpoint de chat simplifié (sans spec/plan/verify)
    Pour compatibilité avec l'ancienne API
    """
    
    # Gestion de la conversation
    conversation_id = request.conversation_id
    
    if not conversation_id:
        conversation = Conversation(
            id=generate_uuid(),
            user_id=current_user["sub"] if current_user else None,
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
            model=request.model,
        )
        db.add(conversation)
        db.commit()
        conversation_id = conversation.id
    
    # Sauvegarder le message utilisateur
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.message,
    )
    db.add(user_message)
    db.commit()
    
    # Historique
    history = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()
    
    history_list = [{"role": m.role, "content": m.content} for m in history]
    
    # Exécuter en mode simplifié (skip spec)
    result = await workflow_engine.run(
        user_message=request.message,
        conversation_id=conversation_id,
        model=request.model,
        history=history_list,
        skip_spec=True,  # Toujours skip pour ce endpoint
    )
    
    # Sauvegarder réponse
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
    
    # Retourner format legacy
    return ChatResponse(
        response=result.response,
        conversation_id=conversation_id,
        model_used=result.model_used,
        tools_used=result.tools_used,
        iterations=result.iterations,
        thinking=result.thinking,
        duration_ms=result.duration_ms,
    )
