"""
Camada 3 - Execução: handler do bot Telegram.
Recebe mensagem de texto ou áudio, chama STT (se áudio), RAG, orquestrador LLM, atualiza estado,
envia resposta em texto e opcionalmente em áudio (TTS) e imagens de modelos.
"""

import asyncio
import logging
import os
import sys
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

from telegram import Update
from telegram.error import Conflict
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from .db_sessions import (
    append_log,
    get_or_create_session,
    get_recent_log,
    init_db,
    reset_session,
    update_classification,
    update_state,
)
from .drive_rag import get_filter_images_from_drive, search as drive_search
from .llm_orchestrator import run as llm_run
from .message_buffer import buffer_available as message_buffer_available
from .state_machine import apply_transition
from .stt import transcribe as stt_transcribe
from .tts import synthesize as tts_synthesize
from .telegram_buffer_adapter import handle_buffered_message as buffer_adapter_handle


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _get_products_config() -> list[dict]:
    """Carrega configuração de produtos (nome, imagem, indicação, diferencial, preço) de .tmp/products.json ou vazio."""
    path = _project_root() / ".tmp" / "products.json"
    if not path.exists():
        return []
    try:
        import json
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _response_delay_seconds() -> float:
    """Atraso antes de enviar a resposta (segundos), para parecer mais natural. 0 = desligado."""
    try:
        return max(0.0, float(os.environ.get("BOT_RESPONSE_DELAY_SECONDS", "2").strip()))
    except ValueError:
        return 2.0


def _pause_between_messages() -> float:
    """Pausa entre múltiplas mensagens (ex.: texto, depois fotos)."""
    try:
        return max(0.0, float(os.environ.get("BOT_PAUSE_BETWEEN_MESSAGES", "0.8").strip()))
    except ValueError:
        return 0.8


def _find_products_by_names(names: list[str]) -> list[dict]:
    """Retorna itens da config cujo nome está em names (até 3)."""
    config = _get_products_config()
    result = []
    for n in names:
        if len(result) >= 3:
            break
        n_lower = n.strip().lower()
        for p in config:
            if p.get("nome", "").lower() == n_lower or n_lower in p.get("nome", "").lower():
                result.append(p)
                break
    return result


async def run_agent(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_text: str,
    is_audio: bool,
) -> None:
    """
    CORE: recebe texto já consolidado (ou único), executa sessão, RAG, LLM, envia resposta.
    Não contém lógica de buffer; chamado pelo handler ou pelo adapter após flush.
    """
    if not update.message:
        return
    user_id = str(update.effective_user.id)

    async def _send_fallback_error() -> None:
        try:
            await update.message.reply_text(
                "Desculpe, ocorreu um erro ao processar. Pode tentar de novo?"
            )
        except Exception:
            pass

    try:
        await _run_agent_core(update, context, user_text, is_audio)
    except Exception as e:
        logger.exception("run_agent failed: %s", e)
        await _send_fallback_error()


async def _run_agent_core(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_text: str,
    is_audio: bool,
) -> None:
    """Lógica principal do agente (chamada por run_agent com try/except)."""
    if not update.message:
        return
    user_id = str(update.effective_user.id)

    # Sessão e estado
    init_db()
    session = get_or_create_session(user_id)
    current_state = session["current_state"]

    # 3) RAG (opcional: se Drive não configurado, usar contexto vazio e instrução clara)
    if not os.environ.get("DRIVE_FOLDER_ID", "").strip():
        rag_context = (
            "CONTEXTO: A base de conhecimento (Google Drive) não está configurada. "
            "Não invente preços, links, modelos ou especificações. "
            "Para dúvidas sobre produtos ou pagamento, diga que vai verificar. "
            "Foque nas perguntas SPIN e no relacionamento consultivo."
        )
    else:
        try:
            rag_context = drive_search(user_text, state=current_state)
        except Exception as e:
            rag_context = (
                "CONTEXTO: A base de conhecimento não está disponível no momento. "
                "Não invente preços ou links; diga que vai verificar. "
                f"(Erro: {e})"
            )

    # 4) Histórico
    recent_log = get_recent_log(user_id, limit=20)

    # 5) LLM
    await update.message.chat.send_action("typing")
    try:
        out = llm_run(
            user_id=user_id,
            user_message=user_text,
            current_state=current_state,
            rag_context=rag_context,
            recent_log=recent_log,
            input_was_audio=is_audio,
        )
    except Exception as e:
        await update.message.reply_text(f"Desculpe, deu um erro aqui. Pode tentar de novo? ({e})")
        return

    resposta_texto = (out.get("resposta_texto") or "").strip()
    enviar_audio = out.get("enviar_audio", False)
    proximo_estado = out.get("proximo_estado") or current_state
    enviar_imagens = out.get("enviar_imagens", False)
    modelos = out.get("modelos") or []

    # 6) Transição de estado (só se válida)
    new_state = apply_transition(current_state, proximo_estado)
    if new_state != current_state:
        update_state(user_id, new_state)

    # 7) Log
    append_log(user_id, "user", user_text, "audio" if is_audio else "text")
    append_log(user_id, "assistant", resposta_texto, "text")

    # 8) Atraso antes de responder (parecer mais natural)
    delay = _response_delay_seconds()
    if delay > 0:
        await update.message.chat.send_action("typing")
        await asyncio.sleep(delay)

    # 9) Enviar resposta em texto
    if resposta_texto:
        await update.message.reply_text(resposta_texto)

    # 10) Enviar imagens (2–3 modelos) se indicado
    if enviar_imagens and modelos:
        await asyncio.sleep(_pause_between_messages())
        products = _find_products_by_names(modelos[:3])
        for i, p in enumerate(products):
            if i > 0:
                await asyncio.sleep(_pause_between_messages())
            caption = f"{p.get('nome', '')}\n{p.get('indicacao', '')}\n{p.get('diferencial', '')}\nPreço: {p.get('preco', 'Consulte')}"
            img = (p.get("image_url") or p.get("imagem") or "").strip()
            sent_photo = False
            if img:
                try:
                    if img.startswith("http"):
                        await update.message.reply_photo(photo=img, caption=caption)
                        sent_photo = True
                    else:
                        path = Path(img)
                        if path.exists():
                            with open(path, "rb") as f:
                                await update.message.reply_photo(photo=f, caption=caption)
                            sent_photo = True
                except Exception as e:
                    logger.warning("reply_photo falhou (produto %s): %s", p.get("nome"), e)
            if not sent_photo:
                await update.message.reply_text(caption)
        if products:
            await update.message.reply_text("Qual deles faz mais sentido para você?")
        elif modelos:
            await update.message.reply_text(
                "Segue as opções: " + ", ".join(modelos[:3]) + ". Qual delas faz mais sentido para você?"
            )

    # 10b) Imagens da pasta do Drive (ex.: bnbFiltros). Limitar a 2 se já enviou cards de produtos (evitar rajada)
    if enviar_imagens:
        try:
            max_drive = 2 if (modelos and len(modelos) > 0) else 5
            drive_images = get_filter_images_from_drive(max_images=max_drive)
            if drive_images:
                await asyncio.sleep(_pause_between_messages())
                for path in drive_images:
                    if path.exists():
                        try:
                            with open(path, "rb") as f:
                                await update.message.reply_photo(photo=f)
                        except Exception as e:
                            logger.warning("reply_photo Drive falhou (%s): %s", path.name, e)
            else:
                logger.debug("get_filter_images_from_drive retornou vazio (pasta bnbFiltros inexistente ou sem imagens)")
        except Exception as e:
            logger.warning("get_filter_images_from_drive falhou: %s", e)

    # 11) Áudio (TTS) se pedido e entrada foi áudio
    if enviar_audio and resposta_texto and is_audio:
        await asyncio.sleep(_pause_between_messages())
        try:
            audio_path = tts_synthesize(resposta_texto)
            with open(audio_path, "rb") as f:
                await update.message.reply_voice(voice=f)
        except Exception:
            pass  # texto já foi enviado

    # Classificação de lead (heurística)
    if new_state == "fechamento":
        update_classification(user_id, "quente")


async def _handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Entry point: obtém texto (ou áudio), opcionalmente passa pelo buffer adapter e chama run_agent."""
    if not update.message:
        return
    user_id = str(update.effective_user.id)
    is_audio = bool(update.message.voice or update.message.audio)

    # 1) Obter texto da mensagem (ou transcrever áudio)
    if is_audio:
        await update.message.chat.send_action("typing")
        voice = update.message.voice or update.message.audio
        file = await context.bot.get_file(voice.file_id)
        suffix = ".ogg" if update.message.voice else ".m4a"
        tmp_path = _project_root() / ".tmp" / f"voice_{user_id}{suffix}"
        tmp_path.parent.mkdir(parents=True, exist_ok=True)
        await file.download_to_drive(tmp_path)
        try:
            user_text = stt_transcribe(tmp_path)
        except ValueError as e:
            if "OPENAI_API_KEY" in str(e):
                await update.message.reply_text(
                    "Áudio não está disponível no momento. Pode mandar sua mensagem em texto?"
                )
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

    # 1) Multi-tenant: só usa o adapter se TELEGRAM_USE_MULTITENANT=1 (senão o bot segue 100% legado).
    use_multitenant = os.environ.get("TELEGRAM_USE_MULTITENANT", "").strip() in ("1", "true", "yes")
    if use_multitenant:
        try:
            from adapters import telegram_adapter
            tenant_id = telegram_adapter._resolve_tenant_id(update)
            if tenant_id and str(tenant_id).strip().lower() != "default":
                await telegram_adapter.handle_update(update, context)
                return
        except Exception:
            pass

    # 2) Adapter: buffer com debounce (apenas para texto). Se buffer ativo, consolida antes de chamar o CORE.
    if message_buffer_available() and not is_audio:
        tenant_id = os.environ.get("MESSAGE_BUFFER_TENANT_ID", "default")
        try:
            await buffer_adapter_handle(
                tenant_id,
                user_id,
                user_text,
                update,
                context,
                run_agent,
            )
        except Exception:
            await run_agent(update, context, user_text, False)
        return

    # 3) Sem buffer ou áudio: chama o CORE diretamente
    await run_agent(update, context, user_text, is_audio)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    init_db()
    if update.effective_user:
        get_or_create_session(str(update.effective_user.id))
    if os.environ.get("TELEGRAM_USE_MULTITENANT", "").strip() in ("1", "true", "yes"):
        if update.message and update.message.text and " t_" in update.message.text.strip().lower():
            try:
                from adapters import telegram_adapter
                tenant_id = telegram_adapter._resolve_tenant_id(update)
                if tenant_id and str(tenant_id).strip().lower() != "default":
                    telegram_adapter.set_telegram_tenant_for_user(str(update.effective_user.id), tenant_id)
                    await update.message.reply_text(
                        "Bem-vindo! Em que posso ajudar? (pode ser por áudio ou texto.)"
                    )
                    return
            except Exception:
                pass
    if update.message:
        await update.message.reply_text(
            "Oi! Sou seu consultor de filtros de água. "
            "Pode me contar como é a água aí na sua casa e como vocês usam? (pode ser por áudio ou texto.)"
        )


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reseta a conversa: estado, classificação, histórico. O bot volta ao início."""
    if not update.message or not update.effective_user:
        return
    init_db()
    user_id = str(update.effective_user.id)
    reset_session(user_id)
    await update.message.reply_text(
        "Conversa resetada. Pode começar de novo — me conte como é a água aí na sua casa e como vocês usam."
    )


async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trata erros globais; Conflict = outra instância do bot já está rodando."""
    err = context.error
    logger.exception("handler error: %s", err)
    if isinstance(err, Conflict):
        msg = (
            "Conflito: já existe outra instância deste bot rodando (outro terminal, processo ou serviço). "
            "Feche a outra instância e rode apenas um 'python run_bot.py'."
        )
        print(msg)
        sys.exit(1)
    # Enviar feedback ao usuário quando possível (evita "bot parou de responder")
    if isinstance(update, Update) and update.message:
        try:
            await update.message.reply_text("Desculpe, ocorreu um erro. Pode tentar de novo?")
        except Exception:
            pass
    raise err


def build_app(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_error_handler(_on_error)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            _handle_message,
        )
    )
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, _handle_message))
    return app


def _log_buffer_status() -> None:
    """Loga na inicialização se o buffer (Redis) está ativo, para aparecer nos logs do deploy."""
    redis_url = os.environ.get("REDIS_URL", "").strip()
    debounce = os.environ.get("MESSAGE_BUFFER_DEBOUNCE_SECONDS", "5").strip()
    if not redis_url:
        logger.warning(
            "Buffer INATIVO: REDIS_URL não definido. Defina REDIS_URL no Railway (Settings → Variables) "
            "para agrupar mensagens antes de responder. Agora: uma resposta por mensagem."
        )
        return
    try:
        import redis
        r = redis.from_url(redis_url, decode_responses=True)
        r.ping()
        logger.info(
            "Buffer ATIVO (Redis OK). Debounce: %ss — mensagens de texto serão agrupadas antes de responder.",
            debounce,
        )
    except Exception as e:
        logger.warning(
            "Buffer INATIVO: Redis indisponível (%s). Mensagens uma a uma. "
            "Redis Labs: use redis:// (não rediss://) ou abra a porta no firewall.",
            e,
        )


def run_bot() -> None:
    """Ponto de entrada: carrega .env, inicia DB e roda o bot (long polling)."""
    from dotenv import load_dotenv
    load_dotenv(_project_root() / ".env")
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN não configurado.")
    _log_buffer_status()
    init_db()
    app = build_app(token)
    print("Bot iniciado. Use apenas ESTE processo (feche outras instâncias). Ctrl+C para parar.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
