"""
Webhook público: Telegram envia POST aqui; processamos com o token do tenant e respondemos.
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from ..db import get_cursor
from .telegram import _get_telegram_config

router = APIRouter()


def _process_telegram_update(tenant_id: str, update: dict) -> None:
    """
    Extrai mensagem do update, chama run_agent e envia resposta via API do Telegram.
    Suporta texto; áudio opcional (download + STT).
    """
    cfg = _get_telegram_config(tenant_id)
    if not cfg:
        return
    token = cfg["bot_token"]

    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return
    chat_id = (msg.get("chat") or {}).get("id")
    from_user = msg.get("from") or {}
    user_id = str(from_user.get("id", ""))

    # Comando /start com t_<uuid> -> salvar tenant no Redis (se houver)
    text = (msg.get("text") or "").strip()
    if text.lower().startswith("/start") and " " in text:
        payload = text.split(maxsplit=1)[1].strip().lower()
        if payload.startswith("t_"):
            try:
                from adapters.telegram_adapter import set_telegram_tenant_for_user
                set_telegram_tenant_for_user(user_id, payload)
            except Exception:
                pass

    # Áudio: download e transcrição (opcional)
    voice = msg.get("voice") or msg.get("audio")
    user_text = ""
    is_audio = False
    if voice:
        is_audio = True
        file_id = voice.get("file_id")
        if file_id and token:
            try:
                import httpx
                r = httpx.get(f"https://api.telegram.org/bot{token}/getFile", params={"file_id": file_id}, timeout=15.0)
                data = r.json()
                if data.get("ok"):
                    file_path = data.get("result", {}).get("file_path", "")
                    if file_path:
                        r2 = httpx.get(f"https://api.telegram.org/file/bot{token}/{file_path}", timeout=15.0)
                        if r2.status_code == 200:
                            from pathlib import Path
                            import os
                            ROOT = Path(__file__).resolve().parent.parent.parent
                            tmp = ROOT / ".tmp"
                            tmp.mkdir(parents=True, exist_ok=True)
                            ext = ".ogg" if msg.get("voice") else ".m4a"
                            p = tmp / f"voice_{user_id}{ext}"
                            p.write_bytes(r2.content)
                            try:
                                from execution.stt import transcribe as stt_transcribe
                                user_text = stt_transcribe(p)
                            except Exception:
                                user_text = ""
                            try:
                                p.unlink(missing_ok=True)
                            except Exception:
                                pass
            except Exception:
                pass
        if not user_text:
            _send_telegram_text(token, chat_id, "Áudio não está disponível no momento. Pode mandar em texto?")
            return
    else:
        user_text = text

    if not user_text:
        _send_telegram_text(token, chat_id, "Não consegui entender. Pode mandar em texto ou áudio?")
        return

    # Buffer com debounce (apenas texto): agrupa mensagens antes de responder, se REDIS_URL estiver definido
    if not is_audio:
        try:
            from ..webhook_buffer import buffer_available, add_to_buffer_and_schedule
            if buffer_available() and add_to_buffer_and_schedule(tenant_id, user_id, chat_id, user_text):
                return  # worker vai consolidar e responder após o debounce
        except Exception:
            pass

    from core.agent_runner import run_agent
    response = run_agent(
        tenant_id=tenant_id,
        channel="telegram",
        incoming_message=user_text,
        metadata={"lead_id": user_id, "is_audio": is_audio},
    )

    resposta_texto = (response.get("resposta_texto") or "").strip()
    if resposta_texto:
        _send_telegram_text(token, chat_id, resposta_texto)

    # Opcional: imagens e áudio (resposta TTS) — envio simples
    enviar_imagens = response.get("enviar_imagens", False)
    modelos = response.get("modelos") or []
    if enviar_imagens and modelos:
        try:
            from execution.telegram_handler import _find_products_by_names
            products = _find_products_by_names(modelos[:3])
            for p in products:
                caption = f"{p.get('nome', '')}\n{p.get('indicacao', '')}\n{p.get('diferencial', '')}\nPreço: {p.get('preco', 'Consulte')}"
                img = (p.get("image_url") or p.get("imagem") or "").strip()
                if img and img.startswith("http"):
                    _send_telegram_photo(token, chat_id, img, caption)
                else:
                    _send_telegram_text(token, chat_id, caption)
            if products or modelos:
                _send_telegram_text(token, chat_id, "Qual deles faz mais sentido para você?")
        except Exception:
            pass

    if response.get("enviar_audio") and resposta_texto and is_audio:
        try:
            from execution.tts import synthesize as tts_synthesize
            audio_path = tts_synthesize(resposta_texto)
            _send_telegram_voice(token, chat_id, audio_path)
        except Exception:
            pass


def _send_telegram_text(token: str, chat_id: int, text: str) -> bool:
    import httpx
    try:
        r = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=15.0,
        )
        return r.json().get("ok", False)
    except Exception:
        return False


def _send_telegram_photo(token: str, chat_id: int, photo_url: str, caption: str = "") -> bool:
    import httpx
    try:
        r = httpx.post(
            f"https://api.telegram.org/bot{token}/sendPhoto",
            json={"chat_id": chat_id, "photo": photo_url, "caption": caption},
            timeout=15.0,
        )
        return r.json().get("ok", False)
    except Exception:
        return False


def _send_telegram_voice(token: str, chat_id: int, voice_path: str) -> bool:
    import httpx
    try:
        with open(voice_path, "rb") as f:
            r = httpx.post(
                f"https://api.telegram.org/bot{token}/sendVoice",
                data={"chat_id": chat_id},
                files={"voice": f},
                timeout=30.0,
            )
        return r.json().get("ok", False)
    except Exception:
        return False


@router.post("/{tenant_id}")
async def telegram_webhook_receive(tenant_id: str, request: Request):
    """Recebe o update do Telegram (POST com JSON) e processa de forma síncrona."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Body inválido")
    # Processar em background para retornar 200 rápido ao Telegram (evita retry)
    import threading
    def run():
        try:
            _process_telegram_update(tenant_id, body)
        except Exception:
            pass
    t = threading.Thread(target=run)
    t.start()
    return JSONResponse(content={"ok": True}, status_code=200)
