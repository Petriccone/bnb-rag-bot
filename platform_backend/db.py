"""platform_backend/db.py

Conexão Postgres para o platform backend.

Milestone 1 requirement:
- Every tenant-scoped query must run with tenant context set.
- With RLS enabled, this file is the enforcement point: we set `app.tenant_id` per request.

Notes:
- Uses PLATFORM_DATABASE_URL if present, else DATABASE_URL.
- psycopg2 import is lazy for serverless cold starts.
"""

import os
from contextlib import contextmanager
from typing import Optional


def _get_connection():
    import psycopg2
    from psycopg2.extras import RealDictCursor

    url = (
        os.environ.get("PLATFORM_DATABASE_URL", "").strip()
        or os.environ.get("DATABASE_URL", "").strip()
    )
    if not url:
        raise ValueError("PLATFORM_DATABASE_URL ou DATABASE_URL não configurado")
    if "supabase.com" in url and "?" not in url:
        url = url + "?sslmode=require"
    return psycopg2.connect(url, cursor_factory=RealDictCursor)


@contextmanager
def get_cursor(*, tenant_id: Optional[str] = None, user_id: Optional[str] = None, role: Optional[str] = None):
    """Get a cursor with optional RLS context.

    If tenant_id is provided, we set `SET LOCAL app.tenant_id = ...`.
    Callers should pass tenant_id for any tenant-scoped operation.
    """

    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            if tenant_id:
                cur.execute("SET LOCAL app.tenant_id = %s", (str(tenant_id),))
            if user_id:
                cur.execute("SET LOCAL app.user_id = %s", (str(user_id),))
            if role:
                cur.execute("SET LOCAL app.role = %s", (str(role),))
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
