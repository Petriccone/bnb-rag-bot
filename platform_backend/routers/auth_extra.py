"""Extra auth endpoints for Milestone 1.

We keep this separate to reduce risk of breaking existing imports.
Later we can merge into routers/auth.py.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from ..auth import create_access_token, get_current_user, hash_password
from ..config import get_settings
from ..db import get_cursor
from ..security_tokens import new_token_urlsafe, token_hash

router = APIRouter(prefix="/auth", tags=["auth"])


def _now_utc() -> datetime:
    return datetime.utcnow()


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/refresh", response_model=RefreshResponse)
def refresh(req: RefreshRequest):
    settings = get_settings()
    h = token_hash(req.refresh_token)

    with get_cursor() as cur:
        cur.execute(
            """SELECT id, tenant_id, user_id, expires_at, revoked_at
               FROM refresh_tokens
               WHERE token_hash = %s""",
            (h,),
        )
        rt = cur.fetchone()

    if not rt:
        raise HTTPException(status_code=401, detail="Refresh token inválido")
    if rt.get("revoked_at"):
        raise HTTPException(status_code=401, detail="Refresh token revogado")
    if rt.get("expires_at") and rt["expires_at"] < _now_utc():
        raise HTTPException(status_code=401, detail="Refresh token expirado")

    tenant_id = str(rt["tenant_id"])
    user_id = str(rt["user_id"])

    # Load user role / status
    with get_cursor(tenant_id=tenant_id, user_id=user_id) as cur:
        cur.execute(
            "SELECT role, disabled_at FROM platform_users WHERE id = %s AND tenant_id = %s",
            (user_id, tenant_id),
        )
        u = cur.fetchone()
    if not u or u.get("disabled_at"):
        raise HTTPException(status_code=403, detail="Usuário inválido/desativado")

    # Rotate refresh token
    new_raw = new_token_urlsafe(48)
    new_h = token_hash(new_raw)
    expires_at = _now_utc() + timedelta(days=int(getattr(settings, "refresh_token_days", 30) or 30))

    with get_cursor(tenant_id=tenant_id, user_id=user_id) as cur:
        cur.execute(
            """UPDATE refresh_tokens
               SET revoked_at = NOW(), replaced_by = %s
               WHERE id = %s AND revoked_at IS NULL""",
            (None, str(rt["id"])),
        )
        # Create replacement
        cur.execute(
            """INSERT INTO refresh_tokens (tenant_id, user_id, token_hash, expires_at, replaced_by)
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (tenant_id, user_id, new_h, expires_at, str(rt["id"])),
        )

    access = create_access_token(
        data={"sub": user_id, "tenant_id": tenant_id, "role": u.get("role")}
    )

    return RefreshResponse(access_token=access, refresh_token=new_raw)


@router.post("/logout")
def logout(user: dict = Depends(get_current_user)):
    # Invalidate all active refresh tokens for the user.
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    if not tenant_id or not user_id:
        raise HTTPException(status_code=401, detail="Sem contexto")
    with get_cursor(tenant_id=str(tenant_id), user_id=str(user_id)) as cur:
        cur.execute(
            "UPDATE refresh_tokens SET revoked_at = NOW() WHERE tenant_id = %s AND user_id = %s AND revoked_at IS NULL",
            (str(tenant_id), str(user_id)),
        )
    return {"ok": True}


class RequestEmailVerification(BaseModel):
    email: EmailStr


@router.post("/request-email-verification")
def request_email_verification(body: RequestEmailVerification):
    settings = get_settings()
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, tenant_id, email_verified_at FROM platform_users WHERE email = %s",
            (body.email,),
        )
        u = cur.fetchone()

    if not u:
        # Don't leak account existence
        return {"ok": True}

    if u.get("email_verified_at"):
        return {"ok": True}

    raw = new_token_urlsafe(32)
    h = token_hash(raw)
    expires_at = _now_utc() + timedelta(minutes=int(getattr(settings, "verify_token_minutes", 60) or 60))

    with get_cursor(tenant_id=str(u["tenant_id"]), user_id=str(u["id"])) as cur:
        cur.execute(
            """INSERT INTO email_verification_tokens (tenant_id, user_id, token_hash, expires_at)
               VALUES (%s, %s, %s, %s)""",
            (str(u["tenant_id"]), str(u["id"]), h, expires_at),
        )

    # DEV MODE: return token (in prod, email it)
    return {"ok": True, "dev_token": raw}


class VerifyEmail(BaseModel):
    token: str


@router.post("/verify-email")
def verify_email(body: VerifyEmail):
    h = token_hash(body.token)
    with get_cursor() as cur:
        cur.execute(
            """SELECT id, tenant_id, user_id, expires_at, used_at
               FROM email_verification_tokens WHERE token_hash = %s""",
            (h,),
        )
        t = cur.fetchone()
    if not t:
        raise HTTPException(status_code=400, detail="Token inválido")
    if t.get("used_at"):
        return {"ok": True}
    if t.get("expires_at") and t["expires_at"] < _now_utc():
        raise HTTPException(status_code=400, detail="Token expirado")

    tenant_id = str(t["tenant_id"])
    user_id = str(t["user_id"])
    with get_cursor(tenant_id=tenant_id, user_id=user_id) as cur:
        cur.execute("UPDATE email_verification_tokens SET used_at = NOW() WHERE id = %s", (str(t["id"]),))
        cur.execute("UPDATE platform_users SET email_verified_at = NOW() WHERE id = %s AND tenant_id = %s", (user_id, tenant_id))
    return {"ok": True}


class RequestPasswordReset(BaseModel):
    email: EmailStr


@router.post("/request-password-reset")
def request_password_reset(body: RequestPasswordReset):
    settings = get_settings()
    with get_cursor() as cur:
        cur.execute("SELECT id, tenant_id FROM platform_users WHERE email = %s", (body.email,))
        u = cur.fetchone()
    if not u:
        return {"ok": True}

    raw = new_token_urlsafe(32)
    h = token_hash(raw)
    expires_at = _now_utc() + timedelta(minutes=int(getattr(settings, "reset_token_minutes", 30) or 30))

    with get_cursor(tenant_id=str(u["tenant_id"]), user_id=str(u["id"])) as cur:
        cur.execute(
            """INSERT INTO password_reset_tokens (tenant_id, user_id, token_hash, expires_at)
               VALUES (%s, %s, %s, %s)""",
            (str(u["tenant_id"]), str(u["id"]), h, expires_at),
        )

    return {"ok": True, "dev_token": raw}


class ResetPassword(BaseModel):
    token: str
    new_password: str


@router.post("/reset-password")
def reset_password(body: ResetPassword):
    h = token_hash(body.token)
    with get_cursor() as cur:
        cur.execute(
            """SELECT id, tenant_id, user_id, expires_at, used_at
               FROM password_reset_tokens WHERE token_hash = %s""",
            (h,),
        )
        t = cur.fetchone()
    if not t:
        raise HTTPException(status_code=400, detail="Token inválido")
    if t.get("used_at"):
        raise HTTPException(status_code=400, detail="Token já usado")
    if t.get("expires_at") and t["expires_at"] < _now_utc():
        raise HTTPException(status_code=400, detail="Token expirado")

    tenant_id = str(t["tenant_id"])
    user_id = str(t["user_id"])

    with get_cursor(tenant_id=tenant_id, user_id=user_id) as cur:
        cur.execute("UPDATE password_reset_tokens SET used_at = NOW() WHERE id = %s", (str(t["id"]),))
        cur.execute(
            "UPDATE platform_users SET password_hash = %s, updated_at = NOW() WHERE id = %s AND tenant_id = %s",
            (hash_password(body.new_password), user_id, tenant_id),
        )
        # Revoke all refresh tokens
        cur.execute(
            "UPDATE refresh_tokens SET revoked_at = NOW() WHERE tenant_id = %s AND user_id = %s AND revoked_at IS NULL",
            (tenant_id, user_id),
        )

    return {"ok": True}
