"""
Login e cadastro (empresa + primeiro usuário).
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr

from ..auth import hash_password, verify_password, create_access_token, get_current_user
from ..config import get_settings
from ..db import get_cursor
from ..security_tokens import new_token_urlsafe, token_hash

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    company_name: str
    email: EmailStr
    password: str
    plan: str = "free"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


def _now_utc() -> datetime:
    return datetime.utcnow()


def _issue_refresh_token(*, tenant_id: str, user_id: str, user_agent: str | None = None, ip: str | None = None) -> str:
    """Create refresh token, store hash in DB, return raw token."""
    settings = get_settings()
    raw = new_token_urlsafe(48)
    h = token_hash(raw)
    expires_at = _now_utc() + timedelta(days=int(getattr(settings, "refresh_token_days", 30) or 30))
    with get_cursor(tenant_id=tenant_id, user_id=user_id) as cur:
        cur.execute(
            """INSERT INTO refresh_tokens (tenant_id, user_id, token_hash, expires_at, user_agent, ip)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (tenant_id, user_id, h, expires_at, user_agent, ip),
        )
    return raw


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, tenant_id, password_hash, role, email_verified_at, disabled_at FROM platform_users WHERE email = %s",
            (req.email,),
        )
        row = cur.fetchone()
    if not row or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")
    if row.get("disabled_at"):
        raise HTTPException(status_code=403, detail="Usuário desativado")

    tenant_id = str(row["tenant_id"]) if row.get("tenant_id") else None
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant")

    token = create_access_token(
        data={
            "sub": str(row["id"]),
            "tenant_id": tenant_id,
            "role": row.get("role") or "company_user",
        }
    )

    refresh = _issue_refresh_token(
        tenant_id=tenant_id,
        user_id=str(row["id"]),
    )

    return TokenResponse(access_token=token, refresh_token=refresh)


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    if req.plan not in ("free", "pro", "enterprise"):
        req.plan = "free"
    try:
        with get_cursor() as cur:
            cur.execute("SELECT id FROM platform_users WHERE email = %s", (req.email,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Email já cadastrado")
            cur.execute(
                """INSERT INTO tenants (company_name, plan) VALUES (%s, %s) RETURNING id""",
                (req.company_name, req.plan),
            )
            tenant_row = cur.fetchone()
            tenant_id = tenant_row["id"]
            cur.execute(
                """INSERT INTO platform_users (tenant_id, email, password_hash, role)
                   VALUES (%s, %s, %s, 'company_admin') RETURNING id""",
                (tenant_id, req.email, hash_password(req.password)),
            )
            user_row = cur.fetchone()

        token = create_access_token(
            data={"sub": str(user_row["id"]), "tenant_id": str(tenant_id), "role": "company_admin"}
        )
        refresh = _issue_refresh_token(tenant_id=str(tenant_id), user_id=str(user_row["id"]))
        return TokenResponse(access_token=token, refresh_token=refresh)
    except HTTPException:
        raise
    except Exception as e:
        msg = str(e).lower()
        if "72 bytes" in msg or "password" in msg:
            detail = "Erro na senha. Use uma senha com no máximo 72 caracteres."
        else:
            detail = f"Erro ao cadastrar. Verifique as tabelas (database/schema.sql). Detalhe: {e!s}"
        raise HTTPException(status_code=500, detail=detail)


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user
