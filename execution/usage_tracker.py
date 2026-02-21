"""
Módulo core de rastreamento de uso (Usage Tracker).
Extrai a lógica do roteador para ser usada diretamente pela execução (agent_facade, workers).
"""
import os
from datetime import datetime
from typing import Optional


# Plan limits configuration based on Euro pricing
PLAN_LIMITS = {
    "free": {
        "messages_limit": 100,
        "tokens_limit": 50000,
        "storage_limit_mb": 10,
        "documents_limit": 2,
        "agents_limit": 1,
    },
    "starter": {
        "messages_limit": 2000,
        "tokens_limit": 1000000,
        "storage_limit_mb": 50,
        "documents_limit": 10,
        "agents_limit": 3,
    },
    "growth": {
        "messages_limit": 10000,
        "tokens_limit": 5000000,
        "storage_limit_mb": 500,
        "documents_limit": 50,
        "agents_limit": 10,
    },
    "business": {
        "messages_limit": 50000,
        "tokens_limit": 25000000,
        "storage_limit_mb": 2000,
        "documents_limit": 200,
        "agents_limit": 50,
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


def _get_connection():
    import psycopg2
    from psycopg2.extras import RealDictCursor
    url = (
        os.environ.get("PLATFORM_DATABASE_URL", "").strip()
        or os.environ.get("DATABASE_URL", "").strip()
    )
    if not url:
        raise ValueError("DATABASE_URL ou PLATFORM_DATABASE_URL não configurado")
    if "supabase.com" in url and "?" not in url:
        url = url + "?sslmode=require"
    return psycopg2.connect(url, cursor_factory=RealDictCursor)


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


def track_message_sync(tenant_id: str, tokens_used: int = 0) -> bool:
    """Registra o uso de uma mensagem e os tokens gerados/gastos durante ela."""
    if not tenant_id:
        return False
    
    month = _get_current_month()
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            usage = _ensure_usage_record(tenant_id, cur)
            
            # Atualiza contadores de mensagens enviadas e uso (+ tokens se aplicável)
            cur.execute(
                """UPDATE tenant_usage 
                   SET messages_used = messages_used + 1,
                       messages_sent = messages_sent + 1, 
                       tokens_used = tokens_used + %s,
                       updated_at = NOW()
                   WHERE tenant_id = %s AND year_month = %s""",
                (tokens_used, tenant_id, month)
            )
            
            # Opcionalmente registrar tokens independentes de onde a msg veio. Log de message_sent.
            cur.execute(
                """INSERT INTO tenant_usage_log (tenant_id, event_type, tokens)
                   VALUES (%s, 'message_sent', %s)""",
                (tenant_id, tokens_used)
            )
        conn.commit()
        return True
    except Exception as e:
        # Silencia erros pra não quebrar main flow
        print(f"Error tracking message: {e}")
        return False
    finally:
        conn.close()


def track_storage_sync(tenant_id: str, bytes_delta: int, event_type: str = "document_uploaded") -> dict:
    """Registra uso de storage (adicionar ou remover bytes) para uso do Worker ou Roteador."""
    if not tenant_id:
        return {"ok": False, "error": "No tenant_id"}

    month = _get_current_month()
    mb_delta = bytes_delta / (1024 * 1024)
    
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            usage = _ensure_usage_record(tenant_id, cur)
            
            # Verifica limite de storage
            if usage["storage_limit_mb"] > 0:
                cur.execute(
                    """SELECT storage_mb FROM tenant_usage WHERE tenant_id = %s AND year_month = %s""",
                    (tenant_id, month)
                )
                current = cur.fetchone()
                new_storage = (current["storage_mb"] if current else 0) + mb_delta
                if new_storage > usage["storage_limit_mb"] and event_type != "document_deleted":
                    return {"ok": False, "error": "Limite de storage do plano atingido"}
            
            storage_change = mb_delta if event_type == "document_uploaded" else -mb_delta
            
            # Adjust document count changes
            doc_change = 1 if event_type == "document_uploaded" else -1
            
            cur.execute(
                """UPDATE tenant_usage 
                   SET storage_mb = GREATEST(0, storage_mb + %s),
                       documents_count = GREATEST(0, documents_count + %s),
                       updated_at = NOW()
                   WHERE tenant_id = %s AND year_month = %s""",
                (storage_change, doc_change, tenant_id, month)
            )
            
            cur.execute(
                """INSERT INTO tenant_usage_log (tenant_id, event_type, storage_bytes)
                   VALUES (%s, %s, %s)""",
                (tenant_id, event_type, bytes_delta)
            )
        conn.commit()
        return {"ok": True, "storage_delta_mb": mb_delta}
    except Exception as e:
        print(f"Error tracking storage: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()
