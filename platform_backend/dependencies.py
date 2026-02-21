from typing import Optional, Annotated
from pydantic import BaseModel
from fastapi import Header, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import get_settings
from .auth import decode_token, create_access_token, hash_password, verify_password


# Security scheme
bearer_scheme = HTTPBearer(auto_error=False)


# Funções de hash e token movidas para .auth para evitar duplicidade


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
        "role": payload.get("role", "company_user"),
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
        "role": payload.get("role", "company_user"),
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
    
def require_role(allowed_roles: list[str]) -> str:
    """Dependency factory: verifica se o usuário tem uma das roles permitidas."""
    def checker(user: dict = Depends(get_current_user)) -> str:
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão insuficiente"
            )
        return user["role"]
    return checker


# Type aliases para uso nos routers
CurrentUser = Annotated[dict, Depends(get_current_user)]
CurrentTenant = Annotated[str, Depends(require_tenant_id)]
OptionalUser = Annotated[Optional[dict], Depends(get_current_user_optional)]