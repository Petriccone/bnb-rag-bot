"""
Middleware de autenticação e injeção de tenant_id.
Executa antes de cada request para validar token e adicionar contexto ao request.state.
"""
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import status

from .dependencies import decode_token
from .config import get_settings


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware que:
    1. Extrai token JWT do header Authorization
    2. Valida e decodifica o token
    3. Adiciona tenant_id ao request.state para acesso rápido nas rotas
    """
    
    # Routes que não requerem autenticação
    PUBLIC_PATHS = {
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/auth/login",
        "/api/auth/register",
        "/api/webhook/telegram",
        "/api/webhook/whatsapp",
    }
    
    # Prefixos de rotas públicas
    PUBLIC_PREFIXES = (
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/auth/",  # Auth endpoints
    }
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Skip auth para rotas públicas
        if path in self.PUBLIC_PATHS or any(path.startswith(p) for p in self.PUBLIC_PREFIXES):
            return await call_next(request)
        
        # Extrai token do header
        auth_header = request.headers.get("authorization", "")
        token = None
        
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        
        # Se não há token em rotas protected, retorna 401
        if not token:
            # Allow GET requests to /api/public/* sem auth (se implementado)
            if not path.startswith("/api/public"):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token ausente"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return await call_next(request)
        
        # Decodifica token
        payload = decode_token(token)
        
        if not payload or "sub" not in payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token inválido ou expirado"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        tenant_id = payload.get("tenant_id")
        
        # Valida tenant_id (obrigatório para maioria das rotas)
        if not tenant_id and not path.startswith("/api/tenants"):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Usuário sem tenant associado"},
            )
        
        # Injeta contexto no request.state
        request.state.user_id = payload.get("sub")
        request.state.tenant_id = tenant_id
        request.state.plan = payload.get("plan", "free")
        request.state.email = payload.get("email")
        request.state.token_payload = payload
        
        response = await call_next(request)
        return response


def get_tenant_from_request(request: Request) -> Optional[str]:
    """Utility para extrair tenant_id do request.state em qualquer lugar."""
    return getattr(request.state, "tenant_id", None)


def get_user_from_request(request: Request) -> Optional[dict]:
    """Utility para extrair dados do usuário do request.state."""
    return {
        "user_id": getattr(request.state, "user_id", None),
        "tenant_id": getattr(request.state, "tenant_id", None),
        "plan": getattr(request.state, "plan", "free"),
        "email": getattr(request.state, "email", None),
    }