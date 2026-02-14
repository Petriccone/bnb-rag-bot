"""
Verificação de limites por plano (free/pro/enterprise).
Usado pelo platform_backend ao criar agente e pelo core antes de executar (opcional).
"""

from typing import Optional

# Limites por plano
PLAN_LIMITS = {
    "free": {"agents": 1, "messages_per_month": 500},
    "pro": {"agents": 5, "messages_per_month": 10_000},
    "enterprise": {"agents": None, "messages_per_month": None},  # ilimitado
}


def _get_tenant_plan(tenant_id: str) -> str:
    """Retorna o plano do tenant (free/pro/enterprise). Default free."""
    from . import db_sessions as db
    if not db._use_postgres():
        return "free"
    conn = db._get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT plan FROM tenants WHERE id = %s", (tenant_id,))
            row = cur.fetchone()
        return (row["plan"] or "free") if row else "free"
    finally:
        conn.close()


def check_agent_limit(tenant_id: str) -> bool:
    """
    Retorna True se o tenant pode criar mais um agente (dentro do limite do plano).
    """
    plan = _get_tenant_plan(tenant_id)
    limit = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])["agents"]
    if limit is None:
        return True
    from . import db_sessions as db
    conn = db._get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM agents WHERE tenant_id = %s", (tenant_id,))
            row = cur.fetchone()
        count = row["c"] if row else 0
        return count < limit
    finally:
        conn.close()


def check_message_limit(tenant_id: str, period: str = "month") -> bool:
    """
    Retorna True se o tenant pode enviar mais mensagens no período (dentro do limite do plano).
    period: "month" (mensagens no mês atual).
    """
    plan = _get_tenant_plan(tenant_id)
    limit = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])["messages_per_month"]
    if limit is None:
        return True
    from . import db_sessions as db
    conn = db._get_pg_connection()
    try:
        with conn.cursor() as cur:
            if period == "month":
                cur.execute(
                    """SELECT COUNT(*) AS c FROM tenant_conversation_log
                       WHERE tenant_id = %s AND timestamp >= date_trunc('month', CURRENT_DATE)""",
                    (tenant_id,),
                )
            else:
                cur.execute("SELECT COUNT(*) AS c FROM tenant_conversation_log WHERE tenant_id = %s", (tenant_id,))
            row = cur.fetchone()
        count = row["c"] if row else 0
        return count < limit
    finally:
        conn.close()


def get_plan_limits(plan: str) -> dict:
    """Retorna os limites do plano (agents, messages_per_month)."""
    return dict(PLAN_LIMITS.get(plan, PLAN_LIMITS["free"]))
