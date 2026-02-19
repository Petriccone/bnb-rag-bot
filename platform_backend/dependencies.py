"""
Dependências FastAPI para injeção de tenant_id e autenticação.
Este módulo fornece dependências para isolar dados por tenant.
"""
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import hashlib
from datetime import datetime, timedelta

from .config import get_settings


# Security scheme
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


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    secret: Optional[str] = None,
    algorithm: str = "HS256"
) -> str:
    """Cria token JWT com dados personalizados."""
    from jose import jwt
    if secret is None:
        settings = get_settings()
        secret = settings.jwt_secret
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=get_settings().jwt_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret, algorithm=algorithm)


def decode_token(token: str, secret: Optional[str] = None, algorithm: str = "HS256") -> Optional[dict]:
    """Decodifica e valida token JWT."""
    from jose import JWTError, jwt
    if secret is None:
        settings = get_settings()
        secret = settings.jwt_secret
    try:
        return jwt.decode(token, secret, algorithms=[algorithm])
    except JWTError:
        return None


class TenantContext(BaseModel):
    """Contexto do tenant atual extraído do token JWT."""
    tenant_id: str
    user_id: str
    plan: str = "free"
    email: Optional[str] = None
    
    class Config:
        from_attributes = True


async def get_current_user_optional(
    authorization: Optional[str] = Header(None)
) -> Optional[dict]:
    """Retorna dados do usuário se token presente, ou None se匿名."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        return None
    
    return {
        "user_id": payload["sub"],
        "tenant_id": payload.get("tenant_id"),
        "plan": payload.get("plan", "free"),
        "email": payload.get("email"),
    }


async def get_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> dict:
    """Dependência obrigatória: retorna dados do usuário logado."""
    # Aceita tanto Authorization header quanto HTTPBearer
    token = None
    
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif credentials:
        token = credentials.credentials
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Valida tenant_id obrigatório
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário sem tenant associado",
        )
    
    return {
        "user_id": payload["sub"],
        "tenant_id": tenant_id,
        "plan": payload.get("plan", "free"),
        "email": payload.get("email"),
    }


def require_tenant_id(user: dict = Depends(get_current_user)) -> str:
    """Retorna o tenant_id do usuário atual."""
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário sem tenant",
        )
    return str(tenant_id)


def require_plan(minimum_plan: str = "free") -> str:
    """Dependency factory: verifica se o plano do tenant atende ao mínimo necessário.
    
    Usage:
        @router.get("/premium-feature")
        def premium_feature(user: dict = Depends(require_plan("pro"))):
            ...
    """
    def checker(user: dict = Depends(get_current_user)) -> str:
        plan_hierarchy = {"free": 0, "pro": 1, "enterprise": 2}
        user_plan = user.get("plan", "free")
        
        if plan_hierarchy.get(user_plan, 0) < plan_hierarchy.get(minimum_plan, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Plano '{minimum_plan}' ou superior necessário"
            )
        return user_plan
    
    return checker


# Type aliases para uso nos routers
CurrentUser = Annotated[dict, Depends(get_current_user)]
CurrentTenant = Annotated[str, Depends(require_tenant_id)]
OptionalUser = Annotated[Optional[dict], Depends(get_current_user_optional)]