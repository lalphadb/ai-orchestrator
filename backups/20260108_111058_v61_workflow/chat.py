"""
Chat routes - Endpoint principal pour les conversations IA
"""
import json
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db, Conversation, Message
from app.core.security import get_current_user_optional, generate_uuid
from app.services.react_engine.engine import react_engine
from app.models import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat")


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional)
):
    """
    Endpoint de chat principal
    Utilise le moteur ReAct pour traiter les requêtes
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
    
    # Exécuter ReAct Engine
    result = await react_engine.run(
        user_message=request.message,
        conversation_id=conversation_id,
        model=request.model,
        history=history_list,
    )
    
    # Sauvegarder la réponse
    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=result["response"],
        model=result.get("model"),
        tools_used=json.dumps([t["tool"] for t in result.get("tools_used", [])]),
        thinking=result.get("thinking"),
    )
    db.add(assistant_message)
    db.commit()
    
    return ChatResponse(
        response=result["response"],
        conversation_id=conversation_id,
        model_used=result.get("model", "unknown"),
        tools_used=result.get("tools_used", []),
        iterations=result.get("iterations", 0),
        thinking=result.get("thinking"),
        duration_ms=result.get("duration_ms", 0),
    )


@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket pour chat en temps réel avec streaming
    """
    await websocket.accept()
    
    try:
        while True:
            # Recevoir message
            data = await websocket.receive_json()
            
            message = data.get("message", "")
            conversation_id = data.get("conversation_id")
            model = data.get("model")
            
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
            
            # Exécuter avec WebSocket
            result = await react_engine.run(
                user_message=message,
                conversation_id=conversation_id,
                model=model,
                history=history_list,
                websocket=websocket,
            )
            
            # Sauvegarder réponse
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=result["response"],
                model=result.get("model"),
                tools_used=json.dumps([t["tool"] for t in result.get("tools_used", [])]),
            )
            db.add(assistant_msg)
            db.commit()
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "data": str(e)})
        except:
            pass
