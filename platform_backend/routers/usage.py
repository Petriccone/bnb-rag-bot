"""
Roteador de Usage Tracking: tokens, mensagens, storage.
Gerencia o tracking de uso por tenant e verifica limites de plano.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies import get_current_user, CurrentUser, CurrentTenant
from ..db import get_cursor

router = APIRouter(prefix="/usage", tags=["usage"])


# Plan limits configuration
PLAN_LIMITS = {
    "free": {
        "messages_limit": 2000,
        "tokens_limit": 100000,
        "storage_limit_mb": 50,
        "documents_limit": 10,
        "agents_limit": 3,
    },
    "pro": {
        "messages_limit": 10000,
        "tokens_limit": 500000,
        "storage_limit_mb": 500,
        "documents_limit": 50,
        "agents_limit": 10,
    },
    "enterprise": {
        "messages_limit": 0,  # 0 = unlimited
        "tokens_limit": 0,
        "storage_limit_mb": 0,
        "documents_limit": 0,
        "agents_limit": 0,
    },
}


def _get_current_month() -> str:
    return datetime.utcnow().strftime("%Y-%m")


def _ensure_usage_record(tenant_id: str, cursor) -> dict:
    """Garante que existe registro de uso para o mês atual."""
    month = _get_current_month()
    
    cursor.execute(
        """SELECT id, messages_limit, tokens_limit, storage_limit_mb, documents_limit, agents_limit
           FROM tenant_usage WHERE tenant_id = %s AND year_month = %s""",
        (tenant_id, month)
    )
    record = cursor.fetchone()
    
    if not record:
        # Buscar plano do tenant
        cursor.execute("SELECT plan FROM tenants WHERE id = %s", (tenant_id,))
        tenant = cursor.fetchone()
        plan = tenant["plan"] if tenant else "free"
        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
        
        cursor.execute(
            """INSERT INTO tenant_usage (tenant_id, year_month, messages_limit, tokens_limit, 
               storage_limit_mb, documents_limit, agents_limit)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               RETURNING id, messages_limit, tokens_limit, storage_limit_mb, documents_limit, agents_limit""",
            (tenant_id, month, limits["messages_limit"], limits["tokens_limit"],
             limits["storage_limit_mb"], limits["documents_limit"], limits["agents_limit"])
        )
        record = cursor.fetchone()
    
    return {
        "id": str(record["id"]),
        "messages_limit": record["messages_limit"],
        "tokens_limit": record["tokens_limit"],
        "storage_limit_mb": record["storage_limit_mb"],
        "documents_limit": record["documents_limit"],
        "agents_limit": record["agents_limit"],
    }


class UsageResponse(BaseModel):
    year_month: str
    messages_used: int
    messages_limit: int
    tokens_used: int
    tokens_limit: int
    storage_mb: float
    storage_limit_mb: float
    documents_count: int
    documents_limit: int
    agents_count: int
    agents_limit: int
    plan: str


class UsageLogResponse(BaseModel):
    id: str
    event_type: str
    tokens: int
    storage_bytes: int
    created_at: datetime


@router.get("", response_model=UsageResponse)
def get_usage(
    user: CurrentUser,
    tenant_id: CurrentTenant,
):
    """Retorna o uso atual do tenant no mês corrente."""
    month = _get_current_month()
    
    with get_cursor() as cur:
        # Buscar plano do tenant
        cur.execute("SELECT plan FROM tenants WHERE id = %s", (tenant_id,))
        tenant = cur.fetchone()
        plan = tenant["plan"] if tenant else "free"
        
        cur.execute(
            """SELECT id, messages_used, messages_limit, tokens_used, tokens_limit, 
                      storage_mb, storage_limit_mb, documents_count, documents_limit,
                      agents_count, agents_limit
               FROM tenant_usage WHERE tenant_id = %s AND year_month = %s""",
            (tenant_id, month)
        )
        record = cur.fetchone()
        
        if not record:
            limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
            return UsageResponse(
                year_month=month,
                messages_used=0,
                messages_limit=limits["messages_limit"],
                tokens_used=0,
                tokens_limit=limits["tokens_limit"],
                storage_mb=0,
                storage_limit_mb=limits["storage_limit_mb"],
                documents_count=0,
                documents_limit=limits["documents_limit"],
                agents_count=0,
                agents_limit=limits["agents_limit"],
                plan=plan,
            )
        
        return UsageResponse(
            year_month=month,
            messages_used=record["messages_used"],
            messages_limit=record["messages_limit"],
            tokens_used=record["tokens_used"],
            tokens_limit=record["tokens_limit"],
            storage_mb=float(record["storage_mb"]),
            storage_limit_mb=float(record["storage_limit_mb"]),
            documents_count=record["documents_count"],
            documents_limit=record["documents_limit"],
            agents_count=record["agents_count"],
            agents_limit=record["agents_limit"],
            plan=plan,
        )


@router.post("/track/message")
def track_message(
    tokens_used: int = 0,
    user: CurrentUser = None,
    tenant_id: CurrentTenant = None,
):
    """Registra uma mensagem enviada (para uso interno/automático)."""
    month = _get_current_month()
    
    with get_cursor() as cur:
        usage = _ensure_usage_record(tenant_id, cur)
        
        # Verifica limite de mensagens
        if usage["messages_limit"] > 0:
            cur.execute(
                """SELECT messages_used FROM tenant_usage WHERE tenant_id = %s AND year_month = %s""",
                (tenant_id, month)
            )
            current = cur.fetchone()
            if current and current["messages_used"] >= usage["messages_limit"]:
                raise HTTPException(
                    status_code=403,
                    detail="Limite de mensagens do plano atingido"
                )
        
        # Atualiza contadores
        cur.execute(
            """UPDATE tenant_usage 
               SET messages_sent = messages_sent + 1, 
                   tokens_used = tokens_used + %s,
                   updated_at = NOW()
               WHERE tenant_id = %s AND year_month = %s""",
            (tokens_used, tenant_id, month)
        )
        
        # Log
        cur.execute(
            """INSERT INTO tenant_usage_log (tenant_id, event_type, tokens)
               VALUES (%s, 'message_sent', %s)""",
            (tenant_id, tokens_used)
        )
    
    return {"ok": True, "tokens_used": tokens_used}


@router.post("/track/tokens")
def track_tokens(
    tokens: int,
    user: CurrentUser = None,
    tenant_id: CurrentTenant = None,
):
    """Registra tokens usados (para uso interno/automático)."""
    month = _get_current_month()
    
    with get_cursor() as cur:
        usage = _ensure_usage_record(tenant_id, cur)
        
        # Verifica limite de tokens
        if usage["tokens_limit"] > 0:
            cur.execute(
                """SELECT tokens_used FROM tenant_usage WHERE tenant_id = %s AND year_month = %s""",
                (tenant_id, month)
            )
            current = cur.fetchone()
            if current and current["tokens_used"] + tokens > usage["tokens_limit"]:
                raise HTTPException(
                    status_code=403,
                    detail="Limite de tokens do plano atingido"
                )
        
        cur.execute(
            """UPDATE tenant_usage 
               SET tokens_used = tokens_used + %s,
                   updated_at = NOW()
               WHERE tenant_id = %s AND year_month = %s""",
            (tokens, tenant_id, month)
        )
        
        cur.execute(
            """INSERT INTO tenant_usage_log (tenant_id, event_type, tokens)
               VALUES (%s, 'token_used', %s)""",
            (tenant_id, tokens)
        )
    
    return {"ok": True, "tokens_added": tokens}


@router.post("/track/storage")
def track_storage(
    bytes_delta: int,
    event_type: str = "document_uploaded",  # or document_deleted
    user: CurrentUser = None,
    tenant_id: CurrentTenant = None,
):
    """Registra uso de storage (para uso interno/automático)."""
    month = _get_current_month()
    mb_delta = bytes_delta / (1024 * 1024)
    
    with get_cursor() as cur:
        usage = _ensure_usage_record(tenant_id, cur)
        
        # Verifica limite de storage
        if usage["storage_limit_mb"] > 0:
            cur.execute(
                """SELECT storage_mb FROM tenant_usage WHERE tenant_id = %s AND year_month = %s""",
                (tenant_id, month)
            )
            current = cur.fetchone()
            new_storage = (current["storage_mb"] if current else 0) + mb_delta
            if new_storage > usage["storage_limit_mb"]:
                raise HTTPException(
                    status_code=403,
                    detail="Limite de storage do plano atingido"
                )
        
        storage_change = mb_delta if event_type == "document_uploaded" else -mb_delta
        cur.execute(
            """UPDATE tenant_usage 
               SET storage_mb = storage_mb + %s,
                   updated_at = NOW()
               WHERE tenant_id = %s AND year_month = %s""",
            (storage_change, tenant_id, month)
        )
        
        cur.execute(
            """INSERT INTO tenant_usage_log (tenant_id, event_type, storage_bytes)
               VALUES (%s, %s, %s)""",
            (tenant_id, event_type, bytes_delta)
        )
    
    return {"ok": True, "storage_delta_mb": mb_delta}


@router.get("/logs", response_model=list[UsageLogResponse])
def get_usage_logs(
    limit: int = 50,
    event_type: Optional[str] = None,
    user: CurrentUser = None,
    tenant_id: CurrentTenant = None,
):
    """Retorna logs de uso do tenant."""
    with get_cursor() as cur:
        if event_type:
            cur.execute(
                """SELECT id, event_type, tokens, storage_bytes, created_at
                   FROM tenant_usage_log 
                   WHERE tenant_id = %s AND event_type = %s
                   ORDER BY created_at DESC LIMIT %s""",
                (tenant_id, event_type, limit)
            )
        else:
            cur.execute(
                """SELECT id, event_type, tokens, storage_bytes, created_at
                   FROM tenant_usage_log 
                   WHERE tenant_id = %s
                   ORDER BY created_at DESC LIMIT %s""",
                (tenant_id, limit)
            )
        
        rows = cur.fetchall()
    
    return [
        UsageLogResponse(
            id=str(r["id"]),
            event_type=r["event_type"],
            tokens=r["tokens"],
            storage_bytes=r["storage_bytes"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.get("/limits")
def get_plan_limits(
    plan: str = "free",
):
    """Retorna os limites de um plano específico."""
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    return {
        "plan": plan,
        **limits,
    }
