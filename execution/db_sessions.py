"""
Camada 3 - Execução: persistência de sessões, estado SPIN e classificação de leads.
Suporta: PostgreSQL (DATABASE_URL com postgresql://), Supabase REST (SUPABASE_URL + key) ou SQLite.
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Quando tenant_id é None ou "default", usa tabelas legado (sessions, conversation_log).
# Quando tenant_id é um UUID válido, usa tabelas multi-tenant (conversations, tenant_conversation_log, leads).
def _use_tenant_tables(tenant_id: Optional[str]) -> bool:
    if not tenant_id or str(tenant_id).strip().lower() == "default":
        return False
    return True

# Estados válidos da máquina SPIN (ordem importa para transição)
STATES = (
    "descoberta",
    "problema",
    "implicacao",
    "solucao",
    "oferta",
    "fechamento",
    "pos_venda",
)

# Classificação de lead
CLASSIFICATIONS = ("frio", "morno", "quente", "cliente")

# Caminho padrão do banco SQLite
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), ".tmp", "sdr_bot.db"
)


def _use_postgres() -> bool:
    url = os.environ.get("DATABASE_URL", "").strip()
    return url.startswith("postgresql://") or url.startswith("postgres://")


def _get_pg_connection():
    """Conexão PostgreSQL (ex.: pooler Supabase). Supabase exige SSL."""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise ValueError("DATABASE_URL não configurado")
    # Supabase exige SSL; adiciona sslmode=require se for host Supabase e não tiver parâmetros
    if "supabase.com" in url and "?" not in url:
        url = url + "?sslmode=require"
    return psycopg2.connect(url, cursor_factory=RealDictCursor)


def _use_supabase() -> bool:
    """Supabase via REST API (não usado se DATABASE_URL for Postgres)."""
    if _use_postgres():
        return False
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    return bool(url and key)


def _get_supabase():
    """Cliente Supabase (usa service role para acesso total às tabelas)."""
    from supabase import create_client
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not key:
        raise ValueError("SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY devem estar no .env")
    return create_client(url, key)


def _get_db_path() -> str:
    return os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)


def _ensure_dir(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    path = _get_db_path()
    _ensure_dir(path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Cria as tabelas se não existirem (legado + multi-tenant). Postgres: cria automaticamente. Supabase REST: rode supabase_schema.sql no SQL Editor."""
    if _use_postgres():
        conn = _get_pg_connection()
        try:
            schema_sql = """
                CREATE TABLE IF NOT EXISTS sessions (
                    user_id TEXT PRIMARY KEY,
                    current_state TEXT NOT NULL DEFAULT 'descoberta',
                    lead_classification TEXT NOT NULL DEFAULT 'frio',
                    spin_answers JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS conversation_log (
                    id BIGSERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content_type TEXT NOT NULL DEFAULT 'text',
                    content TEXT NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_conversation_log_user_ts ON conversation_log (user_id, timestamp DESC);
            """
            with conn.cursor() as cur:
                cur.execute(schema_sql)
            multi_tenant_sql = """
                CREATE TABLE IF NOT EXISTS tenants (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    company_name TEXT NOT NULL,
                    plan TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'enterprise')),
                    settings JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS agents (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    niche TEXT,
                    prompt_custom TEXT,
                    active BOOLEAN NOT NULL DEFAULT true,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_agents_tenant ON agents (tenant_id);
                CREATE TABLE IF NOT EXISTS conversations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
                    lead_id TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'descoberta',
                    spin_answers JSONB DEFAULT '{}',
                    lead_classification TEXT NOT NULL DEFAULT 'frio',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (tenant_id, agent_id, lead_id)
                );
                CREATE INDEX IF NOT EXISTS idx_conversations_tenant_lead ON conversations (tenant_id, lead_id);
                CREATE TABLE IF NOT EXISTS tenant_conversation_log (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
                    lead_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content_type TEXT NOT NULL DEFAULT 'text',
                    content TEXT NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_tenant_conversation_log_lead_ts ON tenant_conversation_log (tenant_id, lead_id, timestamp DESC);
                CREATE TABLE IF NOT EXISTS leads (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    lead_id TEXT NOT NULL,
                    classification TEXT NOT NULL DEFAULT 'frio' CHECK (classification IN ('frio', 'morno', 'quente', 'cliente')),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (tenant_id, lead_id)
                );
                CREATE TABLE IF NOT EXISTS documents (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    file_path TEXT NOT NULL,
                    embedding_namespace TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """
            with conn.cursor() as cur:
                for stmt in multi_tenant_sql.split(";"):
                    stmt = stmt.strip()
                    if stmt and not stmt.startswith("--"):
                        try:
                            cur.execute(stmt)
                        except Exception:
                            pass
            conn.commit()
        finally:
            conn.close()
        return
    if _use_supabase():
        return
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                user_id TEXT PRIMARY KEY,
                current_state TEXT NOT NULL DEFAULT 'descoberta',
                lead_classification TEXT NOT NULL DEFAULT 'frio',
                spin_answers TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS conversation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content_type TEXT NOT NULL DEFAULT 'text',
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES sessions(user_id)
            );
            CREATE INDEX IF NOT EXISTS idx_log_user_ts ON conversation_log(user_id, timestamp);
        """)
        conn.commit()
    finally:
        conn.close()


def get_or_create_session(
    user_id: str,
    tenant_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> dict:
    """
    Retorna a sessão do usuário (ou conversa tenant+agent+lead). Se não existir, cria com estado 'descoberta' e classificação 'frio'.
    Quando tenant_id e agent_id são informados (e tenant_id != 'default'), usa tabelas conversations/tenant_conversation_log.
    """
    user_id = str(user_id)
    if _use_tenant_tables(tenant_id) and agent_id and _use_postgres():
        conn = _get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT lead_id, state, lead_classification, spin_answers, created_at, updated_at
                       FROM conversations WHERE tenant_id = %s AND agent_id = %s AND lead_id = %s""",
                    (tenant_id, agent_id, user_id),
                )
                row = cur.fetchone()
            if row:
                spin = row["spin_answers"] if isinstance(row["spin_answers"], dict) else (json.loads(row["spin_answers"]) if row["spin_answers"] else {})
                return {
                    "user_id": row["lead_id"],
                    "current_state": row["state"],
                    "lead_classification": row["lead_classification"],
                    "spin_answers": spin,
                    "created_at": str(row["created_at"]) if row["created_at"] else "",
                    "updated_at": str(row["updated_at"]) if row["updated_at"] else "",
                }
            now = datetime.utcnow().isoformat() + "Z"
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO conversations (tenant_id, agent_id, lead_id, state, lead_classification, spin_answers, created_at, updated_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (tenant_id, agent_id, user_id, "descoberta", "frio", json.dumps({}), now, now),
                )
            conn.commit()
            return {
                "user_id": user_id,
                "current_state": "descoberta",
                "lead_classification": "frio",
                "spin_answers": {},
                "created_at": now,
                "updated_at": now,
            }
        finally:
            conn.close()
    if _use_postgres():
        conn = _get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT user_id, current_state, lead_classification, spin_answers, created_at, updated_at FROM sessions WHERE user_id = %s",
                    (user_id,),
                )
                row = cur.fetchone()
            if row:
                spin = row["spin_answers"] if isinstance(row["spin_answers"], dict) else (json.loads(row["spin_answers"]) if row["spin_answers"] else {})
                return {
                    "user_id": row["user_id"],
                    "current_state": row["current_state"],
                    "lead_classification": row["lead_classification"],
                    "spin_answers": spin,
                    "created_at": str(row["created_at"]) if row["created_at"] else "",
                    "updated_at": str(row["updated_at"]) if row["updated_at"] else "",
                }
            now = datetime.utcnow().isoformat() + "Z"
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO sessions (user_id, current_state, lead_classification, spin_answers, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s)",
                    (user_id, "descoberta", "frio", json.dumps({}), now, now),
                )
            conn.commit()
            return {
                "user_id": user_id,
                "current_state": "descoberta",
                "lead_classification": "frio",
                "spin_answers": {},
                "created_at": now,
                "updated_at": now,
            }
        finally:
            conn.close()
    if _use_supabase():
        sb = _get_supabase()
        r = sb.table("sessions").select("*").eq("user_id", user_id).execute()
        if r.data and len(r.data) > 0:
            row = r.data[0]
            return {
                "user_id": row["user_id"],
                "current_state": row["current_state"],
                "lead_classification": row["lead_classification"],
                "spin_answers": row.get("spin_answers") or {},
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        now = datetime.utcnow().isoformat() + "Z"
        sb.table("sessions").insert({
            "user_id": user_id,
            "current_state": "descoberta",
            "lead_classification": "frio",
            "spin_answers": {},
            "created_at": now,
            "updated_at": now,
        }).execute()
        return {
            "user_id": user_id,
            "current_state": "descoberta",
            "lead_classification": "frio",
            "spin_answers": {},
            "created_at": now,
            "updated_at": now,
        }
    # SQLite
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT user_id, current_state, lead_classification, spin_answers, created_at, updated_at FROM sessions WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row:
            return {
                "user_id": row["user_id"],
                "current_state": row["current_state"],
                "lead_classification": row["lead_classification"],
                "spin_answers": json.loads(row["spin_answers"]) if row["spin_answers"] else {},
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        now = datetime.utcnow().isoformat() + "Z"
        conn.execute(
            "INSERT INTO sessions (user_id, current_state, lead_classification, spin_answers, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, "descoberta", "frio", "{}", now, now),
        )
        conn.commit()
        return {
            "user_id": user_id,
            "current_state": "descoberta",
            "lead_classification": "frio",
            "spin_answers": {},
            "created_at": now,
            "updated_at": now,
        }
    finally:
        conn.close()


def update_state(
    user_id: str,
    new_state: str,
    tenant_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> None:
    """Atualiza o estado da sessão (ou da conversa multi-tenant)."""
    if new_state not in STATES:
        raise ValueError(f"Estado inválido: {new_state}")
    user_id = str(user_id)
    now = datetime.utcnow().isoformat() + "Z"
    if _use_tenant_tables(tenant_id) and agent_id and _use_postgres():
        conn = _get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE conversations SET state = %s, updated_at = %s WHERE tenant_id = %s AND agent_id = %s AND lead_id = %s",
                    (new_state, now, tenant_id, agent_id, user_id),
                )
            conn.commit()
        finally:
            conn.close()
        return
    if _use_postgres():
        conn = _get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE sessions SET current_state = %s, updated_at = %s WHERE user_id = %s",
                    (new_state, now, user_id),
                )
            conn.commit()
        finally:
            conn.close()
        return
    if _use_supabase():
        _get_supabase().table("sessions").update({
            "current_state": new_state,
            "updated_at": now,
        }).eq("user_id", user_id).execute()
        return
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE sessions SET current_state = ?, updated_at = ? WHERE user_id = ?",
            (new_state, now, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def reset_session(
    user_id: str,
    tenant_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> None:
    """
    Reseta a conversa: estado 'descoberta', classificação 'frio', spin_answers vazio e apaga histórico.
    Com tenant_id/agent_id usa tabelas multi-tenant.
    """
    user_id = str(user_id)
    now = datetime.utcnow().isoformat() + "Z"
    empty_spin = json.dumps({}, ensure_ascii=False)
    if _use_tenant_tables(tenant_id) and agent_id and _use_postgres():
        conn = _get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE conversations SET state = %s, lead_classification = %s, spin_answers = %s, updated_at = %s WHERE tenant_id = %s AND agent_id = %s AND lead_id = %s",
                    ("descoberta", "frio", empty_spin, now, tenant_id, agent_id, user_id),
                )
                cur.execute(
                    "DELETE FROM tenant_conversation_log WHERE tenant_id = %s AND lead_id = %s",
                    (tenant_id, user_id),
                )
            conn.commit()
        finally:
            conn.close()
        return
    if _use_postgres():
        conn = _get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE sessions SET current_state = %s, lead_classification = %s, spin_answers = %s, updated_at = %s WHERE user_id = %s",
                    ("descoberta", "frio", empty_spin, now, user_id),
                )
                cur.execute("DELETE FROM conversation_log WHERE user_id = %s", (user_id,))
            conn.commit()
        finally:
            conn.close()
        return
    if _use_supabase():
        sb = _get_supabase()
        sb.table("sessions").update({
            "current_state": "descoberta",
            "lead_classification": "frio",
            "spin_answers": {},
            "updated_at": now,
        }).eq("user_id", user_id).execute()
        sb.table("conversation_log").delete().eq("user_id", user_id).execute()
        return
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE sessions SET current_state = ?, lead_classification = ?, spin_answers = ?, updated_at = ? WHERE user_id = ?",
            ("descoberta", "frio", empty_spin, now, user_id),
        )
        conn.execute("DELETE FROM conversation_log WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


def update_classification(
    user_id: str,
    classification: str,
    tenant_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> None:
    """Atualiza a classificação do lead (sessão legado ou conversa multi-tenant)."""
    if classification not in CLASSIFICATIONS:
        raise ValueError(f"Classificação inválida: {classification}")
    user_id = str(user_id)
    now = datetime.utcnow().isoformat() + "Z"
    if _use_tenant_tables(tenant_id) and agent_id and _use_postgres():
        conn = _get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE conversations SET lead_classification = %s, updated_at = %s WHERE tenant_id = %s AND agent_id = %s AND lead_id = %s",
                    (classification, now, tenant_id, agent_id, user_id),
                )
            conn.commit()
        finally:
            conn.close()
        return
    if _use_postgres():
        conn = _get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE sessions SET lead_classification = %s, updated_at = %s WHERE user_id = %s",
                    (classification, now, user_id),
                )
            conn.commit()
        finally:
            conn.close()
        return
    if _use_supabase():
        _get_supabase().table("sessions").update({
            "lead_classification": classification,
            "updated_at": now,
        }).eq("user_id", user_id).execute()
        return
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE sessions SET lead_classification = ?, updated_at = ? WHERE user_id = ?",
            (classification, now, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def update_spin_answers(
    user_id: str,
    spin_answers: dict[str, Any],
    tenant_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> None:
    """Substitui ou mescla as respostas SPIN da sessão (ou conversa multi-tenant)."""
    user_id = str(user_id)
    if _use_tenant_tables(tenant_id) and agent_id and _use_postgres():
        conn = _get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT spin_answers FROM conversations WHERE tenant_id = %s AND agent_id = %s AND lead_id = %s", (tenant_id, agent_id, user_id))
                row = cur.fetchone()
            current = {}
            if row and row.get("spin_answers"):
                current = row["spin_answers"] if isinstance(row["spin_answers"], dict) else json.loads(row["spin_answers"])
            merged = {**current, **spin_answers}
            now = datetime.utcnow().isoformat() + "Z"
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE conversations SET spin_answers = %s, updated_at = %s WHERE tenant_id = %s AND agent_id = %s AND lead_id = %s",
                    (json.dumps(merged, ensure_ascii=False), now, tenant_id, agent_id, user_id),
                )
            conn.commit()
        finally:
            conn.close()
        return
    if _use_postgres():
        conn = _get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT spin_answers FROM sessions WHERE user_id = %s", (user_id,))
                row = cur.fetchone()
            current = {}
            if row and row.get("spin_answers"):
                current = row["spin_answers"] if isinstance(row["spin_answers"], dict) else json.loads(row["spin_answers"])
            merged = {**current, **spin_answers}
            now = datetime.utcnow().isoformat() + "Z"
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE sessions SET spin_answers = %s, updated_at = %s WHERE user_id = %s",
                    (json.dumps(merged, ensure_ascii=False), now, user_id),
                )
            conn.commit()
        finally:
            conn.close()
        return
    if _use_supabase():
        sb = _get_supabase()
        r = sb.table("sessions").select("spin_answers").eq("user_id", user_id).execute()
        current = {}
        if r.data and len(r.data) > 0:
            current = r.data[0].get("spin_answers") or {}
        merged = {**current, **spin_answers}
        now = datetime.utcnow().isoformat() + "Z"
        sb.table("sessions").update({
            "spin_answers": merged,
            "updated_at": now,
        }).eq("user_id", user_id).execute()
        return
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT spin_answers FROM sessions WHERE user_id = ?", (user_id,)
        ).fetchone()
        current = json.loads(row["spin_answers"]) if row and row["spin_answers"] else {}
        merged = {**current, **spin_answers}
        now = datetime.utcnow().isoformat() + "Z"
        conn.execute(
            "UPDATE sessions SET spin_answers = ?, updated_at = ? WHERE user_id = ?",
            (json.dumps(merged, ensure_ascii=False), now, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def append_log(
    user_id: str,
    role: str,
    content: str,
    content_type: str = "text",
    tenant_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> None:
    """Append uma mensagem ao log da conversa (role: user ou assistant). Com tenant_id usa tenant_conversation_log."""
    if role not in ("user", "assistant"):
        raise ValueError("role deve ser 'user' ou 'assistant'")
    user_id = str(user_id)
    now = datetime.utcnow().isoformat() + "Z"
    if _use_tenant_tables(tenant_id) and agent_id and _use_postgres():
        conn = _get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO tenant_conversation_log (tenant_id, agent_id, lead_id, role, content_type, content, timestamp)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (tenant_id, agent_id, user_id, role, content_type, content, now),
                )
            conn.commit()
        finally:
            conn.close()
        return
    if _use_postgres():
        conn = _get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO conversation_log (user_id, role, content_type, content, timestamp) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, role, content_type, content, now),
                )
            conn.commit()
        finally:
            conn.close()
        return
    if _use_supabase():
        _get_supabase().table("conversation_log").insert({
            "user_id": user_id,
            "role": role,
            "content_type": content_type,
            "content": content,
            "timestamp": now,
        }).execute()
        return
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO conversation_log (user_id, role, content_type, content, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, role, content_type, content, now),
        )
        conn.commit()
    finally:
        conn.close()


def get_recent_log(
    user_id: str,
    limit: int = 20,
    tenant_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> list[dict]:
    """Retorna as últimas N mensagens do usuário (para contexto do LLM). Com tenant_id usa tenant_conversation_log."""
    user_id = str(user_id)
    if _use_tenant_tables(tenant_id) and agent_id and _use_postgres():
        conn = _get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT role, content_type, content, timestamp FROM tenant_conversation_log
                       WHERE tenant_id = %s AND lead_id = %s ORDER BY timestamp DESC LIMIT %s""",
                    (tenant_id, user_id, limit),
                )
                rows = cur.fetchall()
            out = []
            for row in reversed(rows):
                out.append({
                    "role": row["role"],
                    "content_type": row.get("content_type", "text"),
                    "content": row["content"],
                    "timestamp": str(row["timestamp"]) if row.get("timestamp") else "",
                })
            return out
        finally:
            conn.close()
    if _use_postgres():
        conn = _get_pg_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT role, content_type, content, timestamp FROM conversation_log WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s",
                    (user_id, limit),
                )
                rows = cur.fetchall()
            out = []
            for row in reversed(rows):
                out.append({
                    "role": row["role"],
                    "content_type": row.get("content_type", "text"),
                    "content": row["content"],
                    "timestamp": str(row["timestamp"]) if row.get("timestamp") else "",
                })
            return out
        finally:
            conn.close()
    if _use_supabase():
        r = (
            _get_supabase()
            .table("conversation_log")
            .select("role, content_type, content, timestamp")
            .eq("user_id", user_id)
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        rows = r.data or []
        out = []
        for row in reversed(rows):
            out.append({
                "role": row["role"],
                "content_type": row.get("content_type", "text"),
                "content": row["content"],
                "timestamp": row["timestamp"],
            })
        return out
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT role, content_type, content, timestamp
            FROM conversation_log
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        out = []
        for r in reversed(rows):
            out.append({
                "role": r["role"],
                "content_type": r["content_type"],
                "content": r["content"],
                "timestamp": r["timestamp"],
            })
        return out
    finally:
        conn.close()


def classify_lead_heuristic(
    user_id: str,
    state: str,
    signals: dict,
    tenant_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> str:
    """Heurística de classificação. Atualiza e retorna a classificação."""
    session = get_or_create_session(user_id, tenant_id=tenant_id, agent_id=agent_id)
    current = session["lead_classification"]
    if signals.get("paid"):
        update_classification(user_id, "cliente", tenant_id=tenant_id, agent_id=agent_id)
        return "cliente"
    if signals.get("asked_payment_link") or state == "fechamento":
        update_classification(user_id, "quente", tenant_id=tenant_id, agent_id=agent_id)
        return "quente"
    if state in ("solucao", "oferta") or signals.get("engagement") == "high":
        if current == "frio":
            update_classification(user_id, "morno", tenant_id=tenant_id, agent_id=agent_id)
            return "morno"
        return current
    return current


if __name__ == "__main__":
    init_db()
    if _use_postgres():
        print("DB: PostgreSQL (DATABASE_URL)")
    elif _use_supabase():
        print("DB: Supabase REST")
    else:
        print("DB: SQLite", _get_db_path())
