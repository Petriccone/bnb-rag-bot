"""
Conexão Telegram: usuário cola o token do bot no dashboard; webhook recebe mensagens e responde.
Aceita token: no body (bot_token, botToken, ou bot_token_b64), no header X-Telegram-Bot-Token, ou use_server_token.
"""
import base64
import os
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import AliasChoices, BaseModel, Field

from ..auth import get_current_user
from ..db import get_cursor
from ..whatsapp_crypto import encrypt_token, decrypt_token

router = APIRouter(prefix="/telegram", tags=["telegram"])

TELEGRAM_WEBHOOK_BASE = os.environ.get("TELEGRAM_WEBHOOK_BASE_URL", "").strip().rstrip("/") or os.environ.get("WHATSAPP_WEBHOOK_BASE_URL", "").strip().rstrip("/")


class TelegramBotInfo(BaseModel):
    bot_username: str | None = None
    connected: bool = False
    agent_id: str | None = None


class TelegramAgentUpdate(BaseModel):
    agent_id: str | None = None


class TelegramConnectRequest(BaseModel):
    bot_token: str = Field(..., validation_alias=AliasChoices("bot_token", "botToken"))


def _ensure_telegram_table():
    """Cria a tabela tenant_telegram_config se não existir (evita falha se o schema não foi rodado)."""
    with get_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tenant_telegram_config (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE UNIQUE,
                bot_token_encrypted TEXT NOT NULL,
                agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)


def _get_telegram_config(tenant_id: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute(
            "SELECT bot_token_encrypted, agent_id FROM tenant_telegram_config WHERE tenant_id = %s",
            (tenant_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    try:
        token = decrypt_token(row["bot_token_encrypted"])
    except Exception:
        return None
    agent_id = row.get("agent_id")
    return {"bot_token": token, "agent_id": str(agent_id) if agent_id else None}


def _normalize_bot_token(raw: str) -> str:
    """Remove espaços nas pontas e normaliza hífens Unicode para ASCII. Não remove outros caracteres."""
    if not raw:
        return ""
    s = raw.strip()
    # Hífens Unicode (Word, WhatsApp, etc.) -> ASCII
    for char in ("‑", "–", "—", "−", "\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"):
        s = s.replace(char, "-")
    # Remove apenas espaços e quebras de linha no meio (evita cola com Enter)
    s = "".join(s.split())
    return s


def _validate_telegram_token(token: str) -> dict:
    """Chama getMe; retorna { ok, username } ou levanta HTTPException com diagnóstico."""
    import httpx
    token = _normalize_bot_token(token or "")
    if not token:
        raise HTTPException(status_code=400, detail="Token não pode estar vazio.")
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        r = httpx.get(url, timeout=10.0)
        data = r.json()
        if not data.get("ok"):
            desc = data.get("description", "Token rejeitado pelo Telegram.")
            n = len(token)
            raise HTTPException(
                status_code=400,
                detail=f"Token inválido: {desc} (recebido {n} caracteres após limpeza; o token costuma ter 45–60 caracteres).",
            )
        return data.get("result", {})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao validar token: {e!s}")


def _get_telegram_error_message(token: str) -> str:
    """Chama getMe e retorna mensagem de erro do Telegram (para exibir quando setWebhook falha)."""
    import httpx
    try:
        r = httpx.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10.0)
        data = r.json()
        if not data.get("ok"):
            return data.get("description", "Token rejeitado pelo Telegram.")
        return "Não foi possível registrar o webhook. Verifique a URL do servidor (TELEGRAM_WEBHOOK_BASE_URL)."
    except Exception as e:
        return f"Erro ao falar com o Telegram: {e!s}"


def _set_telegram_webhook(token: str, webhook_url: str, secret_token: str) -> bool:
    import httpx
    try:
        r = httpx.get(
            f"https://api.telegram.org/bot{token}/setWebhook",
            params={"url": webhook_url, "secret_token": secret_token},
            timeout=10.0
        )
        return r.json().get("ok", False)
    except Exception:
        return False


def _delete_telegram_webhook(token: str) -> bool:
    import httpx
    try:
        r = httpx.get(f"https://api.telegram.org/bot{token}/deleteWebhook", timeout=10.0)
        return r.json().get("ok", False)
    except Exception:
        return False


@router.get("/check-server-token")
def telegram_check_server_token(user: dict = Depends(get_current_user)):
    """Testa se o TELEGRAM_BOT_TOKEN do .env é válido (sem conectar). Use para diagnosticar."""
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        return {"valid": False, "error": "TELEGRAM_BOT_TOKEN não está definido no servidor. Adicione no .env e reinicie o backend."}
    import httpx
    try:
        r = httpx.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10.0)
        data = r.json()
        if data.get("ok"):
            return {"valid": True, "username": data.get("result", {}).get("username")}
        return {"valid": False, "error": data.get("description", "Token rejeitado pelo Telegram.")}
    except Exception as e:
        return {"valid": False, "error": str(e)}


@router.get("/status", response_model=TelegramBotInfo)
def telegram_status(user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        return TelegramBotInfo(connected=False)
    cfg = _get_telegram_config(tenant_id)
    if not cfg:
        return TelegramBotInfo(
            bot_username=os.environ.get("TELEGRAM_BOT_USERNAME", "").strip().lstrip("@") or None,
            connected=False,
        )
    try:
        me = _validate_telegram_token(cfg["bot_token"])
        return TelegramBotInfo(
            bot_username=me.get("username"),
            connected=True,
            agent_id=cfg.get("agent_id"),
        )
    except Exception:
        return TelegramBotInfo(connected=False)


@router.get("/bot-info", response_model=TelegramBotInfo)
def telegram_bot_info(user: dict = Depends(get_current_user)):
    """Retorna @ do bot e se está conectado (para o link no dashboard)."""
    s = telegram_status(user)
    return s


@router.patch("/agent")
def telegram_set_agent(body: TelegramAgentUpdate, user: dict = Depends(get_current_user)):
    """Define qual agente este bot do Telegram usa. agent_id null = primeiro agente ativo do tenant."""
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant.")
    cfg = _get_telegram_config(tenant_id)
    if not cfg:
        raise HTTPException(status_code=400, detail="Conecte o Telegram antes de escolher o agente.")
    agent_id = body.agent_id.strip() or None if body.agent_id else None
    with get_cursor() as cur:
        cur.execute(
            "UPDATE tenant_telegram_config SET agent_id = %s, updated_at = NOW() WHERE tenant_id = %s",
            (agent_id, tenant_id),
        )
    return {"ok": True, "agent_id": agent_id}


def _extract_token_from_request(body: dict, request: Request) -> str | None:
    """Extrai o token do body (bot_token, botToken, bot_token_b64) ou do header. Retorna None se ausente."""
    if body.get("use_server_token") is True:
        return None
    raw = body.get("bot_token") or body.get("botToken")
    if raw:
        return _normalize_bot_token(str(raw).strip())
    b64 = body.get("bot_token_b64")
    if b64:
        try:
            decoded = base64.b64decode(b64, validate=True).decode("utf-8")
            return _normalize_bot_token(decoded.strip())
        except Exception:
            pass
    header_token = request.headers.get("X-Telegram-Bot-Token")
    if header_token:
        return _normalize_bot_token(header_token.strip())
    return None


@router.post("/connect")
async def telegram_connect(request: Request, user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant.")
    try:
        body = await request.json() or {}
    except Exception:
        body = {}
    use_server_token = body.get("use_server_token") is True
    if use_server_token:
        token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
        if not token:
            raise HTTPException(
                status_code=400,
                detail="Nenhum token no servidor. Defina TELEGRAM_BOT_TOKEN no .env do backend.",
            )
    else:
        token = _extract_token_from_request(body, request)
        if not token:
            raise HTTPException(status_code=400, detail="Informe o token do bot (campo ou arquivo).")
    if not TELEGRAM_WEBHOOK_BASE:
        raise HTTPException(
            status_code=503,
            detail="A conexão com o Telegram não está disponível no momento. O administrador da plataforma precisa configurar a URL pública do servidor.",
        )
    webhook_url = f"{TELEGRAM_WEBHOOK_BASE}/api/webhook/telegram/{tenant_id}"
    
    secret_token = str(tenant_id).replace("-", "")
    if not _set_telegram_webhook(token, webhook_url, secret_token):
        err_msg = _get_telegram_error_message(token)
        raise HTTPException(status_code=502, detail=err_msg)
    enc = encrypt_token(token)
    agent_id = (body.get("agent_id") or "").strip() or None
    _ensure_telegram_table()
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO tenant_telegram_config (tenant_id, bot_token_encrypted, agent_id, updated_at)
               VALUES (%s, %s, %s, NOW())
               ON CONFLICT (tenant_id) DO UPDATE SET
                 bot_token_encrypted = EXCLUDED.bot_token_encrypted,
                 agent_id = COALESCE(EXCLUDED.agent_id, tenant_telegram_config.agent_id),
                 updated_at = NOW()""",
            (tenant_id, enc, agent_id),
        )
    return {"ok": True, "message": "Telegram conectado. Seu bot já pode receber mensagens."}


@router.post("/connect-with-file")
async def telegram_connect_with_file(
    request: Request,
    user: dict = Depends(get_current_user),
    token_file: UploadFile = File(..., description="Arquivo .txt com apenas o token do bot"),
):
    """Conecta usando o conteúdo de um arquivo (evita colar no navegador)."""
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant.")
    content = await token_file.read()
    try:
        raw = content.decode("utf-8").strip()
    except Exception:
        raw = content.decode("latin-1").strip()
    token = _normalize_bot_token(raw)
    if not token:
        raise HTTPException(status_code=400, detail="O arquivo está vazio ou não contém um token válido.")
    if not TELEGRAM_WEBHOOK_BASE:
        raise HTTPException(
            status_code=503,
            detail="O administrador precisa configurar TELEGRAM_WEBHOOK_BASE_URL no servidor.",
        )
    webhook_url = f"{TELEGRAM_WEBHOOK_BASE}/api/webhook/telegram/{tenant_id}"
    
    secret_token = str(tenant_id).replace("-", "")
    if not _set_telegram_webhook(token, webhook_url, secret_token):
        err_msg = _get_telegram_error_message(token)
        raise HTTPException(status_code=502, detail=err_msg)
    enc = encrypt_token(token)
    _ensure_telegram_table()
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO tenant_telegram_config (tenant_id, bot_token_encrypted, updated_at)
               VALUES (%s, %s, NOW())
               ON CONFLICT (tenant_id) DO UPDATE SET
                 bot_token_encrypted = EXCLUDED.bot_token_encrypted,
                 updated_at = NOW()""",
            (tenant_id, enc),
        )
    return {"ok": True, "message": "Telegram conectado. Seu bot já pode receber mensagens."}


@router.delete("/disconnect")
def telegram_disconnect(user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant.")
    cfg = _get_telegram_config(tenant_id)
    if cfg:
        try:
            _delete_telegram_webhook(cfg["bot_token"])
        except Exception:
            pass
    with get_cursor() as cur:
        cur.execute("DELETE FROM tenant_telegram_config WHERE tenant_id = %s", (tenant_id,))
    return {"ok": True}
