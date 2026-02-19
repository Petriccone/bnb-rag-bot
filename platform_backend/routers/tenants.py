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
    with get_cursor() as cur:
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


class TenantPlanUpdate(BaseModel):
    plan: str


@router.patch("/me")
def update_tenant_settings(body: TenantSettingsUpdate, user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=404, detail="Usuário sem tenant")
    import json
    with get_cursor() as cur:
        cur.execute(
            "UPDATE tenants SET settings = settings || %s::jsonb, updated_at = NOW() WHERE id = %s",
            (json.dumps(body.settings), tenant_id),
        )
    return {"ok": True}


@router.patch("/me/plan")
def update_tenant_plan(body: TenantPlanUpdate, user: dict = Depends(get_current_user)):
    """Atualiza o plano do tenant (para uso admin/billing)."""
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=404, detail="Usuário sem tenant")
    
    valid_plans = ["free", "pro", "enterprise"]
    if body.plan not in valid_plans:
        raise HTTPException(status_code=400, detail=f"Plano inválido. Use: {', '.join(valid_plans)}")
    
    with get_cursor() as cur:
        cur.execute(
            "UPDATE tenants SET plan = %s, updated_at = NOW() WHERE id = %s RETURNING id",
            (body.plan, tenant_id),
        )
        row = cur.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    
    return {"ok": True, "plan": body.plan}
