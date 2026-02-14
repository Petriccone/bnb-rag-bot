"""
Conexão Postgres para o platform backend.
Usa PLATFORM_DATABASE_URL se existir; senão DATABASE_URL (evita conflito com env do sistema).
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager


def _get_connection():
    url = (
        os.environ.get("PLATFORM_DATABASE_URL", "").strip()
        or os.environ.get("DATABASE_URL", "").strip()
    )
    if not url:
        raise ValueError(
            "PLATFORM_DATABASE_URL ou DATABASE_URL não configurado para o platform backend"
        )
    return psycopg2.connect(url, cursor_factory=RealDictCursor)


@contextmanager
def get_cursor():
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
