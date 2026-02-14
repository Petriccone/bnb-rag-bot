"""
Buffer para webhook Telegram: adiciona mensagem ao Redis, agenda flush.
Worker em thread processa flush_queue e chama run_agent + envia resposta.
Usado quando REDIS_URL está definido; senão o webhook processa direto (uma msg por vez).
"""
import json
import logging
import os
import sys
import threading
import time
from pathlib import Path

# Garantir raiz do projeto no path (para execution e core)
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

logger = logging.getLogger(__name__)

REDIS_FLUSH_QUEUE = "buffer:flush_queue"
REDIS_META_PREFIX = "buffer:meta:"
DEBOUNCE_MIN = 2.0
DEBOUNCE_MAX = 15.0


def buffer_available() -> bool:
    return bool(os.environ.get("REDIS_URL", "").strip())


def _debounce_seconds(message: str) -> float:
    raw = os.environ.get("MESSAGE_BUFFER_DEBOUNCE_SECONDS", "").strip()
    if raw:
        try:
            return max(2.0, min(15.0, float(raw)))
        except ValueError:
            pass
    msg = (message or "").strip()
    if len(msg) > 200:
        return 2.0
    if len(msg) < 10 or not msg or (msg and msg[-1] not in ".!?;:"):
        return 5.0
    return min(8.0, max(2.0, 4.0))


def _get_redis():
    import redis
    url = os.environ.get("REDIS_URL", "").strip()
    if not url:
        raise ValueError("REDIS_URL não configurado")
    return redis.from_url(url, decode_responses=True)


def add_to_buffer_and_schedule(
    tenant_id: str,
    user_id: str,
    chat_id: int,
    message: str,
) -> bool:
    """
    Adiciona mensagem ao buffer (execution.message_buffer), grava meta (chat_id, flush_at)
    e adiciona à flush_queue. Retorna True se agendado; False se Redis/buffer indisponível.
    """
    try:
        from execution import message_buffer as buf
    except Exception as e:
        logger.warning("webhook_buffer: execution.message_buffer não disponível: %s", e)
        return False
    if not buffer_available():
        return False
    try:
        buf.add_message_to_buffer(tenant_id, user_id, message, None)
    except Exception as e:
        logger.warning("webhook_buffer: add_message_to_buffer falhou: %s", e)
        return False
    debounce = _debounce_seconds(message)
    flush_at = time.time() + debounce
    meta = {"chat_id": chat_id, "flush_at": flush_at}
    meta_key = f"{REDIS_META_PREFIX}{tenant_id}:{user_id}"
    queue_member = f"{tenant_id}:{user_id}"
    ttl = int(debounce) + 30
    try:
        r = _get_redis()
        r.setex(meta_key, ttl, json.dumps(meta))
        r.zadd(REDIS_FLUSH_QUEUE, {queue_member: flush_at})
        return True
    except Exception as e:
        logger.warning("webhook_buffer: schedule falhou: %s", e)
        return False


def _flush_one(tenant_id: str, user_id: str, chat_id: int) -> None:
    """Obtém mensagens consolidadas, limpa buffer, chama run_agent e envia resposta no Telegram."""
    from execution import message_buffer as buf
    from core.agent_runner import run_agent
    from .routers.telegram_webhook import _get_telegram_config, _send_telegram_text

    try:
        combined = buf.get_combined_messages(tenant_id, user_id)
        buf.clear_buffer(tenant_id, user_id)
    except Exception as e:
        logger.warning("webhook_buffer: get/clear buffer falhou: %s", e)
        return
    if not combined:
        return
    cfg = _get_telegram_config(tenant_id)
    if not cfg:
        return
    token = cfg["bot_token"]
    response = run_agent(
        tenant_id=tenant_id,
        channel="telegram",
        incoming_message=combined,
        metadata={"lead_id": user_id, "is_audio": False},
    )
    resposta_texto = (response.get("resposta_texto") or "").strip()
    if resposta_texto:
        _send_telegram_text(token, chat_id, resposta_texto)


def _worker_loop() -> None:
    """Loop do worker: a cada 1s verifica flush_queue e processa itens com flush_at <= now."""
    import redis
    while True:
        try:
            time.sleep(1)
            if not buffer_available():
                continue
            r = _get_redis()
            now = time.time()
            members = r.zrangebyscore(REDIS_FLUSH_QUEUE, 0, now, start=0, num=50)
            for member in members:
                try:
                    parts = member.split(":", 1)
                    if len(parts) != 2:
                        r.zrem(REDIS_FLUSH_QUEUE, member)
                        continue
                    tenant_id, user_id = parts[0], parts[1]
                    meta_key = f"{REDIS_META_PREFIX}{tenant_id}:{user_id}"
                    raw = r.get(meta_key)
                    if not raw:
                        r.zrem(REDIS_FLUSH_QUEUE, member)
                        continue
                    meta = json.loads(raw)
                    flush_at = meta.get("flush_at", 0)
                    if flush_at > now:
                        continue
                    chat_id = meta.get("chat_id")
                    if chat_id is None:
                        r.delete(meta_key)
                        r.zrem(REDIS_FLUSH_QUEUE, member)
                        continue
                    r.delete(meta_key)
                    r.zrem(REDIS_FLUSH_QUEUE, member)
                    _flush_one(tenant_id, user_id, int(chat_id))
                except Exception as e:
                    logger.exception("webhook_buffer: flush one falhou: %s", e)
                    try:
                        r.zrem(REDIS_FLUSH_QUEUE, member)
                    except Exception:
                        pass
        except redis.ConnectionError:
            logger.debug("webhook_buffer: Redis indisponível no worker")
        except Exception as e:
            logger.exception("webhook_buffer: worker loop: %s", e)


_worker_started = False
_worker_lock = threading.Lock()


def start_worker_if_needed() -> None:
    """Inicia o worker em thread daemon se REDIS_URL estiver definido e ainda não iniciado."""
    global _worker_started
    with _worker_lock:
        if _worker_started or not buffer_available():
            return
        t = threading.Thread(target=_worker_loop, daemon=True)
        t.start()
        _worker_started = True
        logger.info("webhook_buffer: worker iniciado (debounce ativo para webhook Telegram)")
