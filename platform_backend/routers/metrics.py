"""
Métricas por tenant (mensagens, leads, conversas).
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..dependencies import get_current_user
from ..db import get_cursor

router = APIRouter(prefix="/metrics", tags=["metrics"])


class MetricsResponse(BaseModel):
    agents_count: int
    conversations_count: int
    leads_count: int
    messages_this_month: int
    plan: str


@router.get("", response_model=MetricsResponse)
def get_metrics(user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        return MetricsResponse(
            agents_count=0,
            conversations_count=0,
            leads_count=0,
            messages_this_month=0,
            plan="free",
        )
    with get_cursor() as cur:
        cur.execute("SELECT plan FROM tenants WHERE id = %s", (tenant_id,))
        t = cur.fetchone()
        plan = t["plan"] if t else "free"
        cur.execute("SELECT COUNT(*) AS c FROM agents WHERE tenant_id = %s", (tenant_id,))
        agents_count = cur.fetchone()["c"] or 0
        cur.execute("SELECT COUNT(*) AS c FROM conversations WHERE tenant_id = %s", (tenant_id,))
        conversations_count = cur.fetchone()["c"] or 0
        cur.execute("SELECT COUNT(*) AS c FROM leads WHERE tenant_id = %s", (tenant_id,))
        leads_count = cur.fetchone()["c"] or 0
        cur.execute(
            """SELECT COUNT(*) AS c FROM tenant_conversation_log
               WHERE tenant_id = %s AND timestamp >= date_trunc('month', CURRENT_DATE)""",
            (tenant_id,),
        )
        messages_this_month = cur.fetchone()["c"] or 0
    return MetricsResponse(
        agents_count=agents_count,
        conversations_count=conversations_count,
        leads_count=leads_count,
        messages_this_month=messages_this_month,
        plan=plan,
    )
