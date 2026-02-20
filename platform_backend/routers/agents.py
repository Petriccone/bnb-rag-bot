"""
CRUD de agentes por tenant.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_current_user
from ..db import get_cursor

# Import do checker de limite (opcional: execution pode não estar no bundle na Vercel)
def _check_agent_limit(tenant_id: str) -> bool:
    try:
        import sys
        import os
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if root not in sys.path:
            sys.path.insert(0, root)
        from execution.plan_limit_checker import check_agent_limit
        return check_agent_limit(tenant_id)
    except Exception:
        return True  # sem checker: permite criar (fallback para deploy sem execution/)

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentCreate(BaseModel):
    name: str
    niche: str | None = None
    prompt_custom: str | None = None
    embedding_namespace: str | None = None


class AgentUpdate(BaseModel):
    name: str | None = None
    niche: str | None = None
    prompt_custom: str | None = None
    active: bool | None = None
    embedding_namespace: str | None = None


class AgentResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    niche: str | None
    prompt_custom: str | None
    active: bool
    embedding_namespace: str | None = None


class ChatRequest(BaseModel):
    message: str


def _ensure_tenant(user: dict):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant")
    return str(tenant_id)


def _row_to_agent(r: dict) -> AgentResponse:
    return AgentResponse(
        id=str(r["id"]),
        tenant_id=str(r["tenant_id"]),
        name=r["name"],
        niche=r.get("niche"),
        prompt_custom=r.get("prompt_custom"),
        active=r["active"],
        embedding_namespace=r.get("embedding_namespace"),
    )


@router.get("", response_model=list[AgentResponse])
def list_agents(user: dict = Depends(get_current_user)):
    tenant_id = _ensure_tenant(user)
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM agents WHERE tenant_id = %s ORDER BY created_at",
            (tenant_id,),
        )
        rows = cur.fetchall()
    return [_row_to_agent(r) for r in rows]


@router.post("", response_model=AgentResponse)
def create_agent(body: AgentCreate, user: dict = Depends(get_current_user)):
    tenant_id = _ensure_tenant(user)
    if not _check_agent_limit(tenant_id):
        raise HTTPException(
            status_code=403,
            detail="Limite de agentes do plano atingido. Faça upgrade.",
        )
    try:
        with get_cursor() as cur:
            cur.execute(
                """INSERT INTO agents (tenant_id, name, niche, prompt_custom, active, embedding_namespace)
                   VALUES (%s, %s, %s, %s, true, %s) RETURNING *""",
                (tenant_id, body.name, body.niche or "", body.prompt_custom or "", body.embedding_namespace or None),
            )
            row = cur.fetchone()
    except Exception as e:
        if "embedding_namespace" in str(e) and "does not exist" in str(e).lower():
            with get_cursor() as cur:
                cur.execute(
                    """INSERT INTO agents (tenant_id, name, niche, prompt_custom, active)
                       VALUES (%s, %s, %s, %s, true) RETURNING *""",
                    (tenant_id, body.name, body.niche or "", body.prompt_custom or ""),
                )
                row = cur.fetchone()
        else:
            raise
    return _row_to_agent(row)


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: UUID, user: dict = Depends(get_current_user)):
    tenant_id = _ensure_tenant(user)
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM agents WHERE id = %s AND tenant_id = %s",
            (str(agent_id), tenant_id),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    return _row_to_agent(row)


@router.patch("/{agent_id}", response_model=AgentResponse)
def update_agent(agent_id: UUID, body: AgentUpdate, user: dict = Depends(get_current_user)):
    tenant_id = _ensure_tenant(user)
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM agents WHERE id = %s AND tenant_id = %s",
            (str(agent_id), tenant_id),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    name = body.name if body.name is not None else row["name"]
    niche = body.niche if body.niche is not None else row["niche"]
    prompt_custom = body.prompt_custom if body.prompt_custom is not None else row["prompt_custom"]
    active = body.active if body.active is not None else row["active"]
    embedding_namespace = body.embedding_namespace if body.embedding_namespace is not None else row.get("embedding_namespace")
    try:
        with get_cursor() as cur:
            cur.execute(
                """UPDATE agents SET name = %s, niche = %s, prompt_custom = %s, active = %s, embedding_namespace = %s, updated_at = NOW()
                   WHERE id = %s AND tenant_id = %s RETURNING *""",
                (name, niche, prompt_custom, active, embedding_namespace, str(agent_id), tenant_id),
            )
            row = cur.fetchone()
    except Exception as e:
        if "embedding_namespace" in str(e) and "does not exist" in str(e).lower():
            with get_cursor() as cur:
                cur.execute(
                    """UPDATE agents SET name = %s, niche = %s, prompt_custom = %s, active = %s, updated_at = NOW()
                       WHERE id = %s AND tenant_id = %s RETURNING *""",
                    (name, niche, prompt_custom, active, str(agent_id), tenant_id),
                )
                row = cur.fetchone()
        else:
            raise
    return _row_to_agent(row)


@router.delete("/{agent_id}")
def delete_agent(agent_id: UUID, user: dict = Depends(get_current_user)):
    tenant_id = _ensure_tenant(user)
    with get_cursor() as cur:
        cur.execute("DELETE FROM agents WHERE id = %s AND tenant_id = %s", (str(agent_id), tenant_id))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Agente não encontrado")
    return {"ok": True}


@router.post("/{agent_id}/pause")
def pause_agent(agent_id: UUID, user: dict = Depends(get_current_user)):
    """Pausa um agente (define active = false)."""
    tenant_id = _ensure_tenant(user)
    with get_cursor() as cur:
        cur.execute(
            "UPDATE agents SET active = false, updated_at = NOW() WHERE id = %s AND tenant_id = %s RETURNING id",
            (str(agent_id), tenant_id),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    return {"ok": True, "status": "paused"}


@router.post("/{agent_id}/resume")
def resume_agent(agent_id: UUID, user: dict = Depends(get_current_user)):
    """Ativa um agente pausado (define active = true)."""
    tenant_id = _ensure_tenant(user)
    with get_cursor() as cur:
        cur.execute(
            "UPDATE agents SET active = true, updated_at = NOW() WHERE id = %s AND tenant_id = %s RETURNING id",
            (str(agent_id), tenant_id),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    return {"ok": True, "status": "active"}


@router.post("/{agent_id}/chat")
def agent_chat(agent_id: UUID, body: ChatRequest, user: dict = Depends(get_current_user)):
    """Envia uma mensagem ao agente e retorna a resposta (chat de teste no dashboard)."""
    tenant_id = _ensure_tenant(user)
    msg = (body.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Mensagem não pode ser vazia")
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM agents WHERE id = %s AND tenant_id = %s",
            (str(agent_id), tenant_id),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    embedding_namespace = row.get("embedding_namespace")
    try:
        import sys
        import os
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if root not in sys.path:
            sys.path.insert(0, root)
        from execution.agent_facade import run_agent_facade
        out = run_agent_facade(
            lead_id="dashboard-test",
            user_text=msg,
            tenant_id=tenant_id,
            agent_id=str(row["id"]),
            embedding_namespace_override=embedding_namespace,
        )
        reply = (out.get("resposta_texto") or "").strip()
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
