"""
Autenticação JWT para o platform backend.
Senha: SHA-256 + bcrypt para aceitar qualquer tamanho (bcrypt sozinho limita a 72 bytes).
Imports de bcrypt e jose são lazy para o módulo carregar na Vercel (evita crash por binário no cold start).
"""
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)


def _to_bcrypt_input(password: str) -> bytes:
    """SHA-256 da senha (32 bytes) → bcrypt aceita sem limite de 72 bytes."""
    return hashlib.sha256(password.encode("utf-8")).digest()


def hash_password(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(_to_bcrypt_input(password), bcrypt.gensalt()).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    import bcrypt
    return bcrypt.checkpw(_to_bcrypt_input(plain), hashed.encode("ascii"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    from jose import jwt
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict]:
    from jose import JWTError, jwt
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    return {
        "user_id": payload["sub"],
        "tenant_id": payload.get("tenant_id"),
        "role": payload.get("role"),
    }
