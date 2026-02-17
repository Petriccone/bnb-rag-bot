"""
Dados do tenant (empresa) do usuário logado.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_current_user
from ..db import get_cursor

router = APIRouter(prefix="/tenants", tags=["tenants"])


class TenantResponse(BaseModel):
    id: str
    company_name: str
    plan: str
    settings: dict


@router.get("/me", response_model=TenantResponse)
def get_my_tenant(user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=404, detail="Usuário sem tenant")
    with get_cursor(tenant_id=str(tenant_id), user_id=user.get("user_id"), role=user.get("role")) as cur:
        cur.execute(
            "SELECT id, company_name, plan, settings FROM tenants WHERE id = %s",
            (tenant_id,),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    settings = row["settings"] if isinstance(row["settings"], dict) else {}
    return TenantResponse(
        id=str(row["id"]),
        company_name=row["company_name"],
        plan=row["plan"],
        settings=settings,
    )


class TenantSettingsUpdate(BaseModel):
    settings: dict = {}


@router.patch("/me")
def update_tenant_settings(body: TenantSettingsUpdate, user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=404, detail="Usuário sem tenant")
    import json
    with get_cursor(tenant_id=str(tenant_id), user_id=user.get("user_id"), role=user.get("role")) as cur:
        cur.execute(
            "UPDATE tenants SET settings = settings || %s::jsonb, updated_at = NOW() WHERE id = %s",
            (json.dumps(body.settings), tenant_id),
        )
    return {"ok": True}
