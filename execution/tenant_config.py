"""
Configuração multi-tenant: busca tenant e agente ativo no Postgres.
Usado pelo core/agent_runner. Só funciona quando DATABASE_URL está configurado (Postgres).
"""

from typing import Any, Optional

from . import db_sessions as db


def get_tenant(tenant_id: str) -> Optional[dict[str, Any]]:
    """Retorna o tenant por id (UUID) ou None se não existir."""
    if not db._use_postgres():
        return None
    conn = db._get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, company_name, plan, settings, created_at FROM tenants WHERE id = %s",
                (tenant_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return {
            "id": str(row["id"]),
            "company_name": row["company_name"],
            "plan": row["plan"],
            "settings": row["settings"] if isinstance(row["settings"], dict) else {},
            "created_at": str(row["created_at"]) if row.get("created_at") else "",
        }
    finally:
        conn.close()


def get_active_agent_for_tenant(tenant_id: str) -> Optional[dict[str, Any]]:
    """Retorna o primeiro agente ativo do tenant ou None."""
    if not db._use_postgres():
        return None
    conn = db._get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, tenant_id, name, niche, prompt_custom, active, created_at
                   FROM agents WHERE tenant_id = %s AND active = true ORDER BY created_at LIMIT 1""",
                (tenant_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return {
            "id": str(row["id"]),
            "tenant_id": str(row["tenant_id"]),
            "name": row["name"],
            "niche": row["niche"],
            "prompt_custom": row["prompt_custom"],
            "active": row["active"],
            "created_at": str(row["created_at"]) if row.get("created_at") else "",
        }
    finally:
        conn.close()


def get_agent_by_id(agent_id: str) -> Optional[dict[str, Any]]:
    """Retorna o agente por id ou None."""
    if not db._use_postgres():
        return None
    conn = db._get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, tenant_id, name, niche, prompt_custom, active FROM agents WHERE id = %s",
                (agent_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return {
            "id": str(row["id"]),
            "tenant_id": str(row["tenant_id"]),
            "name": row["name"],
            "niche": row["niche"],
            "prompt_custom": row["prompt_custom"],
            "active": row["active"],
        }
    finally:
        conn.close()
