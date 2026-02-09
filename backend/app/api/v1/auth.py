"""
Authentication routes
"""

import logging
import os

from app.core.config import settings

logger = logging.getLogger(__name__)
from app.core.database import User, get_db
from app.core.security import (create_access_token, create_refresh_token,
                               generate_uuid, get_current_user,
                               get_password_hash, verify_password,
                               verify_refresh_token)
from app.models import Token, UserCreate, UserLogin, UserResponse
from fastapi import (APIRouter, Depends, HTTPException, Request, Response,
                     status)
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth")

# Rate limiter instance (désactivé en mode test)
TESTING = os.getenv("TESTING", "0") == "1"
limiter = Limiter(key_func=get_remote_address, enabled=not TESTING)


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """
    Définit les cookies HttpOnly pour les tokens (CRQ-P0-4).

    Seulement si USE_HTTPONLY_COOKIES=true, sinon ne fait rien.
    """
    if not settings.USE_HTTPONLY_COOKIES:
        return

    # Cookie access_token
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,  # Protection XSS
        secure=settings.COOKIE_SECURE,  # HTTPS only
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
    )

    # Cookie refresh_token
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        httponly=True,  # Protection XSS
        secure=settings.COOKIE_SECURE,  # HTTPS only
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
    )


@router.post("/register", response_model=Token)
@limiter.limit("5/minute")
async def register(
    request: Request, response: Response, user_data: UserCreate, db: Session = Depends(get_db)
):
    """Inscription d'un nouvel utilisateur"""

    if not settings.ALLOW_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="L'inscription est désactivée",
        )

    # Vérifier si l'utilisateur existe
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Ce nom d'utilisateur existe déjà"
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
    token = create_access_token(
        {
            "sub": str(user.id),
            "username": user.username,
            "is_admin": user.is_admin,
        }
    )

    # Créer aussi le refresh token
    refresh_token = create_refresh_token(
        {
            "sub": str(user.id),
            "username": user.username,
        }
    )

    # Set cookies HttpOnly si activé (CRQ-P0-4)
    set_auth_cookies(response, token, refresh_token)

    return Token(
        access_token=token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request, response: Response, credentials: UserLogin, db: Session = Depends(get_db)
):
    """Connexion utilisateur"""

    user = db.query(User).filter(User.username == credentials.username).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(
            "Login failed for username=%s from ip=%s",
            credentials.username,
            client_ip,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants incorrects"
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé")

    token = create_access_token(
        {
            "sub": str(user.id),
            "username": user.username,
            "is_admin": user.is_admin,
        }
    )

    # Créer aussi le refresh token
    refresh_token = create_refresh_token(
        {
            "sub": str(user.id),
            "username": user.username,
        }
    )

    # Set cookies HttpOnly si activé (CRQ-P0-4)
    set_auth_cookies(response, token, refresh_token)

    return Token(
        access_token=token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Récupère l'utilisateur courant"""
    user = db.query(User).filter(User.id == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return UserResponse.model_validate(user)


@router.post("/refresh", response_model=Token)
@limiter.limit("30/minute")
async def refresh_access_token(
    request: Request, response: Response, refresh_token: str, db: Session = Depends(get_db)
):
    """Rafraîchit le token d'accès avec un refresh token valide"""

    payload = verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalide ou expiré"
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur non trouvé"
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé")

    # Nouveau access token
    new_access_token = create_access_token(
        {
            "sub": str(user.id),
            "username": user.username,
            "is_admin": user.is_admin,
        }
    )

    # Nouveau refresh token (rotation)
    new_refresh_token = create_refresh_token(
        {
            "sub": str(user.id),
            "username": user.username,
        }
    )

    # Set cookies HttpOnly si activé (CRQ-P0-4)
    set_auth_cookies(response, new_access_token, new_refresh_token)

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
async def logout():
    """Déconnexion (côté client seulement)"""
    return {"message": "Déconnexion réussie"}
