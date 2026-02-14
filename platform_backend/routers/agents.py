"""
CRUD de agentes por tenant.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_current_user
from ..db import get_cursor

# Import do checker de limite (execution no parent)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from execution.plan_limit_checker import check_agent_limit

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentCreate(BaseModel):
    name: str
    niche: str | None = None
    prompt_custom: str | None = None


class AgentUpdate(BaseModel):
    name: str | None = None
    niche: str | None = None
    prompt_custom: str | None = None
    active: bool | None = None


class AgentResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    niche: str | None
    prompt_custom: str | None
    active: bool


def _ensure_tenant(user: dict):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant")
    return str(tenant_id)


@router.get("", response_model=list[AgentResponse])
def list_agents(user: dict = Depends(get_current_user)):
    tenant_id = _ensure_tenant(user)
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, tenant_id, name, niche, prompt_custom, active FROM agents WHERE tenant_id = %s ORDER BY created_at",
            (tenant_id,),
        )
        rows = cur.fetchall()
    return [
        AgentResponse(
            id=str(r["id"]),
            tenant_id=str(r["tenant_id"]),
            name=r["name"],
            niche=r["niche"],
            prompt_custom=r["prompt_custom"],
            active=r["active"],
        )
        for r in rows
    ]


@router.post("", response_model=AgentResponse)
def create_agent(body: AgentCreate, user: dict = Depends(get_current_user)):
    tenant_id = _ensure_tenant(user)
    if not check_agent_limit(tenant_id):
        raise HTTPException(
            status_code=403,
            detail="Limite de agentes do plano atingido. Faça upgrade.",
        )
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO agents (tenant_id, name, niche, prompt_custom, active)
               VALUES (%s, %s, %s, %s, true) RETURNING id, tenant_id, name, niche, prompt_custom, active""",
            (tenant_id, body.name, body.niche or "", body.prompt_custom or ""),
        )
        row = cur.fetchone()
    return AgentResponse(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        name=row["name"],
        niche=row["niche"],
        prompt_custom=row["prompt_custom"],
        active=row["active"],
    )


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: UUID, user: dict = Depends(get_current_user)):
    tenant_id = _ensure_tenant(user)
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, tenant_id, name, niche, prompt_custom, active FROM agents WHERE id = %s AND tenant_id = %s",
            (str(agent_id), tenant_id),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    return AgentResponse(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        name=row["name"],
        niche=row["niche"],
        prompt_custom=row["prompt_custom"],
        active=row["active"],
    )


@router.patch("/{agent_id}", response_model=AgentResponse)
def update_agent(agent_id: UUID, body: AgentUpdate, user: dict = Depends(get_current_user)):
    tenant_id = _ensure_tenant(user)
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, tenant_id, name, niche, prompt_custom, active FROM agents WHERE id = %s AND tenant_id = %s",
            (str(agent_id), tenant_id),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    name = body.name if body.name is not None else row["name"]
    niche = body.niche if body.niche is not None else row["niche"]
    prompt_custom = body.prompt_custom if body.prompt_custom is not None else row["prompt_custom"]
    active = body.active if body.active is not None else row["active"]
    with get_cursor() as cur:
        cur.execute(
            """UPDATE agents SET name = %s, niche = %s, prompt_custom = %s, active = %s, updated_at = NOW()
               WHERE id = %s AND tenant_id = %s RETURNING id, tenant_id, name, niche, prompt_custom, active""",
            (name, niche, prompt_custom, active, str(agent_id), tenant_id),
        )
        row = cur.fetchone()
    return AgentResponse(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        name=row["name"],
        niche=row["niche"],
        prompt_custom=row["prompt_custom"],
        active=row["active"],
    )


@router.delete("/{agent_id}")
def delete_agent(agent_id: UUID, user: dict = Depends(get_current_user)):
    tenant_id = _ensure_tenant(user)
    with get_cursor() as cur:
        cur.execute("DELETE FROM agents WHERE id = %s AND tenant_id = %s", (str(agent_id), tenant_id))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Agente não encontrado")
    return {"ok": True}
