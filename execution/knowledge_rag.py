"""
Base de conhecimento: embeddings (OpenAI) e busca vetorial (pgvector).
Usado pelo agent_facade quando o tenant tem document_chunks e não (ou além do) Drive.
Requer: OPENAI_API_KEY, tabela document_chunks com vector(1536).
"""

import json
import os
from typing import List, Optional


def _get_connection():
    """Conexão Postgres (DATABASE_URL ou PLATFORM_DATABASE_URL)."""
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


def _embed(texts: List[str]) -> List[List[float]]:
    """Gera embeddings via OpenAI (text-embedding-3-small, 1536 dims)."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY não configurado. Defina no .env para usar a base de conhecimento."
        )
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        model = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        out = client.embeddings.create(input=texts, model=model)
        return [e.embedding for e in out.data]
    except Exception as e:
        raise RuntimeError(f"Erro ao gerar embeddings: {e}") from e


def search_document_chunks(
    tenant_id: str,
    query: str,
    limit: int = 6,
) -> str:
    """
    Busca na base de conhecimento do tenant.
    Retorna um único texto com os trechos mais relevantes para o LLM.
    Se não houver OPENAI_API_KEY ou não existir tabela/extension, retorna string vazia ou mensagem de fallback.
    """
    if not query or not query.strip():
        return ""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return (
            "CONTEXTO: A base de conhecimento está configurada mas OPENAI_API_KEY não foi definida. "
            "Não invente dados; diga que vai verificar."
        )
    try:
        embeddings = _embed([query.strip()])
        query_embedding = embeddings[0]
        vec_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    except Exception as e:
        return f"CONTEXTO: Erro ao buscar na base de conhecimento ({e}). Não invente dados."

    conn = None
    try:
        conn = _get_connection()
        with conn.cursor() as cur:
            # pgvector: <=> = cosine distance (menor = mais similar)
            cur.execute(
                """
                SELECT content FROM document_chunks
                WHERE tenant_id = %s AND embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (tenant_id, vec_str, limit),
            )
            rows = cur.fetchall()
    except Exception as e:
        # Tabela ou extensão pode não existir
        return (
            "CONTEXTO: Base de conhecimento indisponível no momento. "
            "Não invente preços ou especificações."
        )
    finally:
        if conn:
            conn.close()

    if not rows:
        return ""
    parts = [r["content"] for r in rows if r.get("content")]
    if not parts:
        return ""
    return "CONTEXTO (base de conhecimento):\n" + "\n\n---\n\n".join(parts)
