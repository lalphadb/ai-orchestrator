"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db, User
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    generate_uuid,
)
from app.core.config import settings
from app.models import UserCreate, UserLogin, UserResponse, Token

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Inscription d'un nouvel utilisateur"""
    
    # Vérifier si l'utilisateur existe
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce nom d'utilisateur existe déjà"
        )
    
    # Créer l'utilisateur
    user = User(
        id=generate_uuid(),
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        is_admin=False,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Générer le token
    token = create_access_token({
        "sub": user.id,
        "username": user.username,
        "is_admin": user.is_admin,
    })
    
    return Token(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Connexion utilisateur"""
    
    user = db.query(User).filter(User.username == credentials.username).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé"
        )
    
    token = create_access_token({
        "sub": user.id,
        "username": user.username,
        "is_admin": user.is_admin,
    })
    
    return Token(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère l'utilisateur courant"""
    user = db.query(User).filter(User.id == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return UserResponse.model_validate(user)


@router.post("/logout")
async def logout():
    """Déconnexion (côté client seulement)"""
    return {"message": "Déconnexion réussie"}
