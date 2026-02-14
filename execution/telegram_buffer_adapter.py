"""
Camada 2 (Adapter): recebe mensagem, salva no buffer Redis, reseta temporizador.
Quando o debounce dispara, consolida mensagens e chama run_agent uma única vez.
Não contém lógica de negócio nem do CORE; apenas buffer + agendamento.
"""

import asyncio
import logging
import os
from typing import Awaitable, Callable

from . import message_buffer as buf

logger = logging.getLogger(__name__)

DEBOUNCE_DEFAULT = 4.0
DEBOUNCE_SHORT = 2.0
DEBOUNCE_EXTENDED = 5.0
DEBOUNCE_MAX = 8.0
DEBOUNCE_MIN = 2.0

BOT_DATA_KEY = "_message_buffer_tasks"


def _debounce_seconds_from_env() -> float | None:
    """Lê MESSAGE_BUFFER_DEBOUNCE_SECONDS (ex.: 5). None se não definido."""
    raw = os.environ.get("MESSAGE_BUFFER_DEBOUNCE_SECONDS", "").strip()
    if not raw:
        return None
    try:
        return max(2.0, min(15.0, float(raw)))
    except ValueError:
        return None


def compute_debounce_delay(message: str) -> float:
    """
    Se MESSAGE_BUFFER_DEBOUNCE_SECONDS estiver definido, usa esse valor (2–15s).
    Senão: regras por mensagem; mínimo 2s, máximo 8s.
    """
    fixed = _debounce_seconds_from_env()
    if fixed is not None:
        return fixed
    msg = (message or "").strip()
    if len(msg) > 200:
        return max(DEBOUNCE_MIN, DEBOUNCE_SHORT)
    if len(msg) < 10 or not msg or (msg and msg[-1] not in ".!?;:"):
        delay = DEBOUNCE_EXTENDED
    else:
        delay = DEBOUNCE_DEFAULT
    return min(DEBOUNCE_MAX, max(DEBOUNCE_MIN, delay))


async def handle_buffered_message(
    tenant_id: str,
    user_id: str,
    message: str,
    update: object,
    context: object,
    run_agent: Callable[[object, object, str, bool], Awaitable[None]],
) -> None:
    """
    Adapter: adiciona mensagem ao buffer, reseta temporizador.
    Quando o debounce dispara, consolida e chama run_agent(update, context, combined_text, False).
    """
    app = getattr(context, "application", None)
    if not app:
        return
    bot_data = getattr(app, "bot_data", None)
    if bot_data is None:
        app.bot_data = {}
        bot_data = app.bot_data
    if BOT_DATA_KEY not in bot_data:
        bot_data[BOT_DATA_KEY] = {}

    key = (tenant_id, user_id)
    pending = bot_data[BOT_DATA_KEY]

    # Adicionar ao buffer (Redis) em thread para não bloquear
    try:
        created, total = await asyncio.to_thread(
            buf.add_message_to_buffer,
            tenant_id,
            user_id,
            message,
            None,
        )
    except Exception as e:
        logger.warning("buffer_unavailable_fallback", extra={"error": str(e)})
        await run_agent(update, context, message, False)
        return

    delay = compute_debounce_delay(message)

    # Cancelar temporizador anterior
    if key in pending:
        try:
            pending[key].cancel()
        except asyncio.CancelledError:
            pass
        except Exception:
            pass
        del pending[key]

    async def delayed_flush() -> None:
        try:
            await asyncio.sleep(delay)
            try:
                if key in pending:
                    del pending[key]
            except KeyError:
                pass
            logger.info("buffer_timeout_triggered", extra={"tenant_id": tenant_id, "user_id": user_id})
            try:
                combined = await asyncio.to_thread(buf.get_combined_messages, tenant_id, user_id)
                await asyncio.to_thread(buf.clear_buffer, tenant_id, user_id)
            except Exception as e:
                logger.warning("buffer_flush_failed", extra={"error": str(e)})
                combined = message
            if combined:
                try:
                    await run_agent(update, context, combined, False)
                except Exception as e:
                    logger.exception("delayed_flush run_agent failed: %s", e)
                    try:
                        if update.message:
                            await update.message.reply_text(
                                "Desculpe, deu um erro ao responder. Pode tentar de novo?"
                            )
                    except Exception:
                        pass
        except asyncio.CancelledError:
            pass

    task = asyncio.create_task(delayed_flush())
    pending[key] = task
