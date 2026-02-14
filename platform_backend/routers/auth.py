"""
Login e cadastro (empresa + primeiro usuário).
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr

from ..auth import hash_password, verify_password, create_access_token, get_current_user
from ..db import get_cursor

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
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, tenant_id, password_hash FROM platform_users WHERE email = %s",
            (req.email,),
        )
        row = cur.fetchone()
    if not row or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")
    token = create_access_token(
        data={"sub": str(row["id"]), "tenant_id": str(row["tenant_id"]) if row["tenant_id"] else None}
    )
    return TokenResponse(access_token=token)


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
                """INSERT INTO platform_users (tenant_id, email, password_hash)
                   VALUES (%s, %s, %s) RETURNING id""",
                (tenant_id, req.email, hash_password(req.password)),
            )
            user_row = cur.fetchone()
        token = create_access_token(
            data={"sub": str(user_row["id"]), "tenant_id": str(tenant_id)}
        )
        return TokenResponse(access_token=token)
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
