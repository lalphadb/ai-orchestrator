"""
Security module - JWT, hashing, authentication
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import settings

# JWT Bearer
security = HTTPBearer(auto_error=False)


def get_password_hash(password: str) -> str:
    """Hash un mot de passe avec bcrypt"""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe"""
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crée un token JWT"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    """Vérifie et décode un token JWT"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user_optional(
    request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """Récupère l'utilisateur courant (optionnel) - Support cookies HttpOnly (CRQ-P0-4)"""
    token = extract_token_from_request(request, credentials)
    if not token:
        return None

    payload = verify_token(token)
    if not payload:
        return None

    return payload


async def get_current_user(
    request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """Récupère l'utilisateur courant (requis) - Support cookies HttpOnly (CRQ-P0-4)"""
    token = extract_token_from_request(request, credentials)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Vérifie que l'utilisateur est admin"""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Accès administrateur requis"
        )
    return current_user


def generate_uuid() -> str:
    """Génère un UUID"""
    return str(uuid.uuid4())


def create_refresh_token(data: dict) -> str:
    """Crée un refresh token JWT (7 jours)"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": str(uuid.uuid4()),
            "type": "refresh",
        }
    )
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_refresh_token(token: str) -> Optional[dict]:
    """Vérifie un refresh token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None


def extract_token_from_request(
    request: Request, credentials: Optional[HTTPAuthorizationCredentials] = None
) -> Optional[str]:
    """
    Extrait le token d'accès depuis les cookies (si USE_HTTPONLY_COOKIES=true)
    ou depuis le header Authorization (méthode legacy).

    CRQ-P0-4: Support cookies HttpOnly pour protection XSS
    """
    # Priorité 1: Cookie HttpOnly (si activé)
    if settings.USE_HTTPONLY_COOKIES:
        token = request.cookies.get("access_token")
        if token:
            return token

    # Priorité 2: Header Authorization (legacy/backward compat)
    if credentials:
        return credentials.credentials

    return None
