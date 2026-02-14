"""
Camada 3 - Execução: buffer de mensagens em Redis com TTL.
Chave: buffer:{tenant_id}:{user_id}. Uso: add_message_to_buffer, get_combined_messages, clear_buffer.
Processamento assíncrono via chamadas em asyncio.to_thread (não bloqueia a thread principal).
"""

import json
import logging
import os
from typing import Optional

KEY_PREFIX = "buffer"


def _buffer_ttl_seconds() -> int:
    """TTL da chave no Redis: pelo menos debounce + 3s para não expirar antes do flush."""
    try:
        raw = os.environ.get("MESSAGE_BUFFER_DEBOUNCE_SECONDS", "").strip()
        if raw:
            debounce = max(2.0, min(15.0, float(raw)))
            return int(debounce) + 3
    except ValueError:
        pass
    return 5

logger = logging.getLogger(__name__)


def _redis_url() -> str:
    url = os.environ.get("REDIS_URL", "").strip()
    if not url:
        raise ValueError("REDIS_URL não configurado (ex.: redis://localhost:6379/0)")
    return url


def _key(tenant_id: str, user_id: str) -> str:
    return f"{KEY_PREFIX}:{tenant_id}:{user_id}"


def _get_client():
    """Cliente Redis (sync). Para uso assíncrono, chamar via asyncio.to_thread."""
    import redis
    return redis.from_url(_redis_url(), decode_responses=True)


def add_message_to_buffer(tenant_id: str, user_id: str, message: str, timestamp: Optional[str] = None) -> tuple[bool, int]:
    """
    Adiciona uma mensagem ao buffer e atualiza o TTL.
    Retorna (buffer_created, total_messages). buffer_created=True se era o primeiro item.
    """
    import redis
    try:
        client = _get_client()
        key = _key(tenant_id, user_id)
        payload = json.dumps({"message": message, "timestamp": timestamp or ""}, ensure_ascii=False)
        pipe = client.pipeline()
        pipe.rpush(key, payload)
        pipe.expire(key, _buffer_ttl_seconds())
        results = pipe.execute()
        total = results[0]
        if total == 1:
            logger.info("buffer_created", extra={"tenant_id": tenant_id, "user_id": user_id})
        else:
            logger.info("buffer_extended", extra={"tenant_id": tenant_id, "user_id": user_id, "total": total})
        return (total == 1, total)
    except Exception as e:
        logger.warning("buffer_add_failed", extra={"error": str(e), "tenant_id": tenant_id, "user_id": user_id})
        raise


def get_combined_messages(tenant_id: str, user_id: str) -> str:
    """Retorna todas as mensagens do buffer concatenadas em uma única string (ordem cronológica)."""
    try:
        client = _get_client()
        key = _key(tenant_id, user_id)
        raw_list = client.lrange(key, 0, -1)
        if not raw_list:
            return ""
        parts = []
        for raw in raw_list:
            try:
                data = json.loads(raw)
                parts.append((data.get("timestamp", ""), data.get("message", "")))
            except (json.JSONDecodeError, TypeError):
                parts.append(("", raw if isinstance(raw, str) else ""))
        parts.sort(key=lambda x: x[0])
        return " ".join(p.strip() for _, p in parts if p.strip()).strip()
    except Exception as e:
        logger.warning("buffer_get_failed", extra={"error": str(e), "tenant_id": tenant_id, "user_id": user_id})
        raise


def clear_buffer(tenant_id: str, user_id: str) -> None:
    """Remove o buffer do usuário após o flush."""
    try:
        client = _get_client()
        key = _key(tenant_id, user_id)
        client.delete(key)
        logger.info("buffer_flushed", extra={"tenant_id": tenant_id, "user_id": user_id})
    except Exception as e:
        logger.warning("buffer_clear_failed", extra={"error": str(e), "tenant_id": tenant_id, "user_id": user_id})
        raise


def buffer_available() -> bool:
    """Retorna True se REDIS_URL está configurado (buffer disponível)."""
    return bool(os.environ.get("REDIS_URL", "").strip())
