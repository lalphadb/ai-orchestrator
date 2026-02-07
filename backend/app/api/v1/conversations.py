"""
Conversations routes - CRUD pour les conversations
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import Conversation, Message, get_db
from app.core.security import generate_uuid, get_current_user_optional
from app.models import (ConversationCreate, ConversationResponse,
                        MessageResponse)

router = APIRouter(prefix="/conversations")


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Liste les conversations de l'utilisateur"""
    query = db.query(Conversation).order_by(Conversation.updated_at.desc())

    if current_user:
        query = query.filter(Conversation.user_id == current_user["sub"])

    conversations = query.offset(offset).limit(limit).all()
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional),
):
    """Crée une nouvelle conversation"""
    conversation = Conversation(
        id=generate_uuid(),
        user_id=current_user["sub"] if current_user else None,
        title=data.title or "Nouvelle conversation",
        model=data.model,
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return ConversationResponse.model_validate(conversation)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional),
):
    """Récupère une conversation avec ses messages"""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")

    # AuthZ: Vérifier que l'utilisateur est le propriétaire
    # Refuser si: pas d'utilisateur, conversation orpheline, ou mismatch user_id
    if not current_user or (conversation.user_id and conversation.user_id != current_user["sub"]):
        raise HTTPException(status_code=403, detail="Accès non autorisé à cette conversation")

    # Charger les messages
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all()
    )

    result = ConversationResponse.model_validate(conversation)
    result.messages = [MessageResponse.model_validate(m) for m in messages]

    return result


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional),
):
    """Supprime une conversation"""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")

    # AuthZ: Vérifier que l'utilisateur est le propriétaire
    if not current_user or (conversation.user_id and conversation.user_id != current_user["sub"]):
        raise HTTPException(status_code=403, detail="Accès non autorisé à cette conversation")

    db.delete(conversation)
    db.commit()

    return {"message": "Conversation supprimée"}
