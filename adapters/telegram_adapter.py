"""
Adapter Telegram: recebe mensagem, extrai tenant_id, chama core.agent_runner.run_agent, envia resposta.
Sem lógica de negócio; apenas transporte.
"""

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from telegram import Update
from telegram.ext import ContextTypes


TELEGRAM_TENANT_KEY_PREFIX = "telegram_tenant"
TELEGRAM_TENANT_TTL_DAYS = 30


def _redis():
    """Cliente Redis opcional (para persistir tenant por user)."""
    url = os.environ.get("REDIS_URL", "").strip()
    if not url:
        return None
    try:
        import redis
        return redis.from_url(url, decode_responses=True)
    except Exception:
        return None


def get_telegram_tenant_for_user(user_id: str) -> str | None:
    """Retorna tenant_id salvo para o user_id no Redis, ou None."""
    r = _redis()
    if not r:
        return None
    try:
        return r.get(f"{TELEGRAM_TENANT_KEY_PREFIX}:{user_id}") or None
    except Exception:
        return None


def set_telegram_tenant_for_user(user_id: str, tenant_id: str) -> None:
    """Salva tenant_id para o user_id no Redis (TTL 30 dias)."""
    r = _redis()
    if not r:
        return
    try:
        key = f"{TELEGRAM_TENANT_KEY_PREFIX}:{user_id}"
        r.setex(key, TELEGRAM_TENANT_TTL_DAYS * 86400, tenant_id)
    except Exception:
        pass


def _resolve_tenant_id(update: Update) -> str:
    """Extrai tenant_id: Redis (user) -> /start t_<uuid> -> TELEGRAM_TENANT_ID -> default."""
    user_id = str(update.effective_user.id) if update.effective_user else ""
    if user_id:
        cached = get_telegram_tenant_for_user(user_id)
        if cached:
            return cached
    if update.message and update.message.text:
        text = (update.message.text or "").strip()
        if text.startswith("/start") and " " in text:
            payload = text.split(maxsplit=1)[1].strip().lower()
            if payload.startswith("t_"):
                return payload
    return os.environ.get("TELEGRAM_TENANT_ID", "default").strip() or "default"


def _response_delay() -> float:
    try:
        return max(0.0, float(os.environ.get("BOT_RESPONSE_DELAY_SECONDS", "2").strip()))
    except ValueError:
        return 2.0


def _pause_between() -> float:
    try:
        return max(0.0, float(os.environ.get("BOT_PAUSE_BETWEEN_MESSAGES", "0.8").strip()))
    except ValueError:
        return 0.8


async def _send_structured_response(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    response: dict,
    is_audio: bool,
) -> None:
    """Envia ao Telegram o conteúdo do dict retornado pelo core (texto, imagens, áudio)."""
    if not update.message:
        return
    resposta_texto = (response.get("resposta_texto") or "").strip()
    enviar_audio = response.get("enviar_audio", False)
    enviar_imagens = response.get("enviar_imagens", False)
    modelos = response.get("modelos") or []

    delay = _response_delay()
    if delay > 0:
        await update.message.chat.send_action("typing")
        await asyncio.sleep(delay)
    if resposta_texto:
        await update.message.reply_text(resposta_texto)

    # Produtos (imagens/legendas) — usa execution para não duplicar lógica de produtos
    from execution.telegram_handler import _find_products_by_names
    if enviar_imagens and modelos:
        await asyncio.sleep(_pause_between())
        products = _find_products_by_names(modelos[:3])
        for i, p in enumerate(products):
            if i > 0:
                await asyncio.sleep(_pause_between())
            caption = f"{p.get('nome', '')}\n{p.get('indicacao', '')}\n{p.get('diferencial', '')}\nPreço: {p.get('preco', 'Consulte')}"
            img = (p.get("image_url") or p.get("imagem") or "").strip()
            if img and img.startswith("http"):
                try:
                    await update.message.reply_photo(photo=img, caption=caption)
                except Exception:
                    await update.message.reply_text(caption)
            elif img:
                path = Path(img)
                if path.exists():
                    try:
                        with open(path, "rb") as f:
                            await update.message.reply_photo(photo=f, caption=caption)
                    except Exception:
                        await update.message.reply_text(caption)
                else:
                    await update.message.reply_text(caption)
            else:
                await update.message.reply_text(caption)
        if products:
            await update.message.reply_text("Qual deles faz mais sentido para você?")
        elif modelos:
            await update.message.reply_text("Segue as opções: " + ", ".join(modelos[:3]) + ". Qual delas faz mais sentido para você?")

    if enviar_imagens:
        try:
            from execution.drive_rag import get_filter_images_from_drive
            drive_images = get_filter_images_from_drive(max_images=2 if modelos else 5)
            if drive_images:
                await asyncio.sleep(_pause_between())
                for path in drive_images:
                    if path.exists():
                        try:
                            with open(path, "rb") as f:
                                await update.message.reply_photo(photo=f)
                        except Exception:
                            pass
        except Exception:
            pass

    if enviar_audio and resposta_texto and is_audio:
        await asyncio.sleep(_pause_between())
        try:
            from execution.tts import synthesize as tts_synthesize
            audio_path = tts_synthesize(resposta_texto)
            with open(audio_path, "rb") as f:
                await update.message.reply_voice(voice=f)
        except Exception:
            pass


async def handle_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Ponto de entrada do adapter: mensagem Telegram -> tenant_id -> core -> envio.
    Chamar a partir de um MessageHandler quando quiser rotear por tenant (multi-tenant).
    """
    if not update.message:
        return
    user_id = str(update.effective_user.id)
    is_audio = bool(update.message.voice or update.message.audio)
    user_text = ""
    if is_audio:
        await update.message.chat.send_action("typing")
        from telegram import Bot
        bot = context.bot
        voice = update.message.voice or update.message.audio
        file = await bot.get_file(voice.file_id)
        suffix = ".ogg" if update.message.voice else ".m4a"
        tmp_path = ROOT / ".tmp" / f"voice_{user_id}{suffix}"
        tmp_path.parent.mkdir(parents=True, exist_ok=True)
        await file.download_to_drive(tmp_path)
        try:
            from execution.stt import transcribe as stt_transcribe
            user_text = stt_transcribe(tmp_path)
        except ValueError as e:
            if "OPENAI_API_KEY" in str(e):
                await update.message.reply_text("Áudio não está disponível no momento. Pode mandar em texto?")
                return
            raise
        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
    else:
        user_text = (update.message.text or "").strip()
    if not user_text:
        await update.message.reply_text("Não consegui entender. Pode mandar de novo em texto ou áudio?")
        return

    tenant_id = _resolve_tenant_id(update)
    if update.message and update.message.text and update.message.text.strip().lower().startswith("/start") and " t_" in update.message.text.strip().lower():
        set_telegram_tenant_for_user(str(update.effective_user.id), tenant_id)
    from core.agent_runner import run_agent
    response = run_agent(
        tenant_id=tenant_id,
        channel="telegram",
        incoming_message=user_text,
        metadata={"lead_id": user_id, "is_audio": is_audio},
    )
    await _send_structured_response(update, context, response, is_audio)
