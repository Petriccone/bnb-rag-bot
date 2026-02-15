"""
Conexão WhatsApp: Cloud API (Meta) ou Evolution API.
Se EVOLUTION_API_URL estiver configurado, o cliente pode conectar só escaneando QR (sem instalar nada).
"""
import os
import re
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from ..auth import get_current_user
from ..db import get_cursor
from ..whatsapp_crypto import encrypt_token, decrypt_token

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

VERIFY_TOKEN = os.environ.get("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "bbrag-verify").strip()
EVOLUTION_API_URL = os.environ.get("EVOLUTION_API_URL", "").strip().rstrip("/")
EVOLUTION_API_KEY = os.environ.get("EVOLUTION_API_KEY", "").strip()
WHATSAPP_WEBHOOK_BASE = os.environ.get("WHATSAPP_WEBHOOK_BASE_URL", "").strip().rstrip("/")


class WhatsAppStatusResponse(BaseModel):
    connected: bool
    message: str
    phone_number_id_mask: str | None = None
    connection_type: str | None = None  # "meta" | "evolution"
    agent_id: str | None = None


class WhatsAppAgentUpdate(BaseModel):
    agent_id: str | None = None


class WhatsAppConnectRequest(BaseModel):
    phone_number_id: str
    access_token: str


class EvolutionConnectRequest(BaseModel):
    base_url: str
    api_key: str
    instance_name: str


def _get_config(tenant_id: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute(
            "SELECT phone_number_id, access_token_encrypted, agent_id FROM tenant_whatsapp_config WHERE tenant_id = %s",
            (tenant_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    try:
        token = decrypt_token(row["access_token_encrypted"])
    except Exception:
        return None
    agent_id = row.get("agent_id")
    return {
        "phone_number_id": row["phone_number_id"],
        "access_token": token,
        "agent_id": str(agent_id) if agent_id else None,
    }


def _get_evolution_config(tenant_id: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute(
            "SELECT base_url, api_key_encrypted, instance_name, agent_id FROM tenant_evolution_config WHERE tenant_id = %s",
            (tenant_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    try:
        api_key = decrypt_token(row["api_key_encrypted"])
    except Exception:
        return None
    agent_id = row.get("agent_id")
    return {
        "base_url": row["base_url"].rstrip("/"),
        "api_key": api_key,
        "instance_name": row["instance_name"],
        "agent_id": str(agent_id) if agent_id else None,
    }


def _evolution_available() -> bool:
    """True se o administrador configurou Evolution API (o cliente só escaneia QR)."""
    return bool(EVOLUTION_API_URL and EVOLUTION_API_KEY)


@router.get("/evolution-available")
def evolution_available(user: dict = Depends(get_current_user)):
    """Indica se a opção 'Conectar com QR' está ativa (Evolution API configurada pelo administrador)."""
    return {"available": _evolution_available()}


@router.get("/status", response_model=WhatsAppStatusResponse)
def whatsapp_status(user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        return WhatsAppStatusResponse(connected=False, message="Usuário sem tenant.")
    evo = _get_evolution_config(tenant_id)
    if evo:
        return WhatsAppStatusResponse(
            connected=True,
            message="WhatsApp conectado via Evolution API (QR Code).",
            phone_number_id_mask=None,
            connection_type="evolution",
            agent_id=evo.get("agent_id"),
        )
    cfg = _get_config(tenant_id)
    if not cfg:
        return WhatsAppStatusResponse(
            connected=False,
            message="Conecte com Evolution API (QR) ou Cloud API (Meta).",
            connection_type=None,
        )
    pid = cfg["phone_number_id"]
    return WhatsAppStatusResponse(
        connected=True,
        message="WhatsApp Cloud API conectado.",
        phone_number_id_mask=pid[:8] + "…" + pid[-4:] if len(pid) > 12 else "***",
        connection_type="meta",
        agent_id=cfg.get("agent_id"),
    )


@router.post("/connect")
def whatsapp_connect(body: WhatsAppConnectRequest, user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant.")
    enc = encrypt_token(body.access_token)
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO tenant_whatsapp_config (tenant_id, phone_number_id, access_token_encrypted, updated_at)
               VALUES (%s, %s, %s, NOW())
               ON CONFLICT (tenant_id) DO UPDATE SET
                 phone_number_id = EXCLUDED.phone_number_id,
                 access_token_encrypted = EXCLUDED.access_token_encrypted,
                 updated_at = NOW()""",
            (tenant_id, body.phone_number_id.strip(), enc),
        )
    return {"ok": True, "message": "WhatsApp conectado."}


@router.patch("/agent")
def whatsapp_set_agent(body: WhatsAppAgentUpdate, user: dict = Depends(get_current_user)):
    """Define qual agente esta conta WhatsApp usa. agent_id null = primeiro agente ativo do tenant."""
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant.")
    agent_id = (body.agent_id or "").strip() or None
    with get_cursor() as cur:
        cur.execute(
            "UPDATE tenant_whatsapp_config SET agent_id = %s, updated_at = NOW() WHERE tenant_id = %s",
            (agent_id, tenant_id),
        )
        cur.execute(
            "UPDATE tenant_evolution_config SET agent_id = %s, updated_at = NOW() WHERE tenant_id = %s",
            (agent_id, tenant_id),
        )
    return {"ok": True, "agent_id": agent_id}


@router.delete("/disconnect")
def whatsapp_disconnect(user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant.")
    with get_cursor() as cur:
        cur.execute("DELETE FROM tenant_whatsapp_config WHERE tenant_id = %s", (tenant_id,))
        cur.execute("DELETE FROM tenant_evolution_config WHERE tenant_id = %s", (tenant_id,))
    return {"ok": True}


# --- Evolution API: conexão por QR (cliente não instala nada) ---

async def _evolution_create_instance_and_qr(tenant_id: str) -> dict:
    """Cria instância na Evolution API (configurada pelo admin), define webhook e retorna QR."""
    import httpx
    instance_name = "bbrag_" + re.sub(r"[^a-zA-Z0-9]", "_", str(tenant_id))[:32]
    webhook_url = f"{WHATSAPP_WEBHOOK_BASE}/api/whatsapp/evolution-webhook" if WHATSAPP_WEBHOOK_BASE else ""
    create_body = {
        "instanceName": instance_name,
        "qrcode": True,
        "integration": "WHATSAPP-BAILEYS",
    }
    if webhook_url:
        create_body["webhook"] = {
            "url": webhook_url,
            "events": ["MESSAGES_UPSERT"],
            "byEvents": False,
        }
    headers = {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{EVOLUTION_API_URL}/instance/create", json=create_body, headers=headers)
        if not r.is_success:
            raise HTTPException(status_code=502, detail=f"Evolution API: {r.text or r.status_code}")
        qr_r = await client.get(f"{EVOLUTION_API_URL}/instance/connect/{instance_name}", headers=headers)
    qr_data = qr_r.json() if qr_r.is_success else {}
    enc = encrypt_token(EVOLUTION_API_KEY)
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO tenant_evolution_config (tenant_id, base_url, api_key_encrypted, instance_name, updated_at)
               VALUES (%s, %s, %s, %s, NOW())
               ON CONFLICT (tenant_id) DO UPDATE SET
                 base_url = EXCLUDED.base_url,
                 api_key_encrypted = EXCLUDED.api_key_encrypted,
                 instance_name = EXCLUDED.instance_name,
                 updated_at = NOW()""",
            (tenant_id, EVOLUTION_API_URL, enc, instance_name),
        )
    return {
        "instance_name": instance_name,
        "qr_code_base64": qr_data.get("base64") or qr_data.get("qrcode", {}).get("base64"),
        "pairing_code": qr_data.get("pairingCode"),
    }


@router.post("/evolution-request-qr")
async def evolution_request_qr(user: dict = Depends(get_current_user)):
    """Gera QR para o tenant escanear (Evolution API já configurada pelo administrador). Cliente não instala nada."""
    if not _evolution_available():
        raise HTTPException(
            status_code=503,
            detail="Conexão por QR não disponível. O administrador da plataforma deve configurar EVOLUTION_API_URL e EVOLUTION_API_KEY.",
        )
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant.")
    try:
        return await _evolution_create_instance_and_qr(tenant_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro ao gerar QR: {e!s}")


@router.post("/connect-evolution")
def whatsapp_connect_evolution(body: EvolutionConnectRequest, user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant.")
    base_url = body.base_url.strip().rstrip("/")
    instance = body.instance_name.strip()
    if not base_url or not instance:
        raise HTTPException(status_code=400, detail="base_url e instance_name são obrigatórios.")
    enc = encrypt_token(body.api_key.strip())
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO tenant_evolution_config (tenant_id, base_url, api_key_encrypted, instance_name, updated_at)
               VALUES (%s, %s, %s, %s, NOW())
               ON CONFLICT (tenant_id) DO UPDATE SET
                 base_url = EXCLUDED.base_url,
                 api_key_encrypted = EXCLUDED.api_key_encrypted,
                 instance_name = EXCLUDED.instance_name,
                 updated_at = NOW()""",
            (tenant_id, base_url, enc, instance),
        )
    return {"ok": True, "message": "Evolution API conectada. Configure o webhook na Evolution apontando para POST /api/whatsapp/evolution-webhook e evento MESSAGES_UPSERT."}


# --- Webhook (Meta chama sem JWT) ---

@router.get("/webhook", response_class=PlainTextResponse)
def webhook_verify(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return hub_challenge
    raise HTTPException(status_code=403, detail="Verify token inválido")


def _get_tenant_and_token_by_phone_number_id(phone_number_id: str) -> tuple[str | None, str | None, str | None]:
    """Retorna (tenant_id, access_token, agent_id) ou (None, None, None)."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT tenant_id, access_token_encrypted, agent_id FROM tenant_whatsapp_config WHERE phone_number_id = %s",
            (phone_number_id,),
        )
        row = cur.fetchone()
    if not row:
        return None, None, None
    try:
        token = decrypt_token(row["access_token_encrypted"])
        agent_id = str(row["agent_id"]) if row.get("agent_id") else None
        return str(row["tenant_id"]), token, agent_id
    except Exception:
        return None, None, None


async def _send_whatsapp_text(phone_number_id: str, access_token: str, to_wa_id: str, text: str) -> bool:
    """Envia mensagem de texto via WhatsApp Cloud API."""
    import httpx
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to_wa_id.replace("+", "").strip(),
        "type": "text",
        "text": {"body": text[:4096]},
    }
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload, headers=headers, timeout=15.0)
            return r.is_success
    except Exception:
        return False


@router.post("/webhook")
async def webhook_receive(request: Request):
    """Recebe mensagens do Meta; obtém tenant, chama core via adapter e envia resposta em texto."""
    body = await request.json()
    if body.get("object") != "whatsapp_business_account":
        return {"ok": True}
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "messages":
                continue
            value = change.get("value", {})
            metadata = value.get("metadata", {})
            phone_number_id = metadata.get("phone_number_id")
            if not phone_number_id:
                continue
            tenant_id, access_token, agent_id = _get_tenant_and_token_by_phone_number_id(phone_number_id)
            if not tenant_id or not access_token:
                continue
            for msg in value.get("messages", []):
                if msg.get("type") != "text":
                    continue
                from_wa = msg.get("from")
                text_body = (msg.get("text") or {}).get("body") or ""
                if not from_wa or not text_body.strip():
                    continue
                from adapters.whatsapp_adapter import get_agent_response
                response = get_agent_response(tenant_id, str(from_wa), text_body.strip(), is_audio=False, agent_id=agent_id)
                reply_text = (response.get("resposta_texto") or "").strip()
                if reply_text:
                    await _send_whatsapp_text(phone_number_id, access_token, str(from_wa), reply_text)
    return {"ok": True}


# --- Evolution API webhook (conexão por QR) ---

def _get_tenant_and_evolution_by_instance(instance_name: str) -> tuple[str | None, dict | None]:
    """Retorna (tenant_id, config) para envio via Evolution API."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT tenant_id, base_url, api_key_encrypted, instance_name, agent_id FROM tenant_evolution_config WHERE instance_name = %s",
            (instance_name,),
        )
        row = cur.fetchone()
    if not row:
        return None, None
    try:
        api_key = decrypt_token(row["api_key_encrypted"])
    except Exception:
        return None, None
    agent_id = str(row["agent_id"]) if row.get("agent_id") else None
    return str(row["tenant_id"]), {
        "base_url": row["base_url"].rstrip("/"),
        "api_key": api_key,
        "instance_name": row["instance_name"],
        "agent_id": agent_id,
    }


async def _send_evolution_text(base_url: str, api_key: str, instance: str, number: str, text: str) -> bool:
    """Envia mensagem de texto via Evolution API."""
    import httpx
    url = f"{base_url}/message/sendText/{instance}"
    headers = {"apikey": api_key, "Content-Type": "application/json"}
    # number: só dígitos, com código do país (ex.: 5531999999999)
    num = number.replace("@s.whatsapp.net", "").replace("@g.us", "").replace("+", "").strip()
    payload = {"number": num, "text": text[:4096]}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload, headers=headers, timeout=15.0)
            return r.is_success
    except Exception:
        return False


def _parse_evolution_message(body: dict) -> list[tuple[str, str, str]]:
    """Extrai (instance_name, remote_jid, text) de um ou mais eventos. Retorna lista."""
    out = []
    event = (body.get("event") or body.get("eventType") or "").upper()
    if "MESSAGES_UPSERT" not in event and "messages.upsert" not in body.get("event", "").lower():
        # Pode vir como array de eventos
        if isinstance(body.get("data"), list):
            for item in body.get("data", []):
                out.extend(_parse_evolution_message({"event": "MESSAGES_UPSERT", "data": item, **item}))
        return out
    instance = body.get("instance") or (body.get("data") or {}).get("instance") or (body.get("data") or {}).get("instanceName")
    if isinstance(instance, dict):
        instance = instance.get("name") or instance.get("instanceName")
    data = body.get("data") or body
    if isinstance(data, list):
        for d in data:
            out.extend(_parse_evolution_message({"event": "MESSAGES_UPSERT", "data": d, "instance": instance}))
        return out
    key = data.get("key") or {}
    if key.get("fromMe") is True:
        return out
    remote_jid = (key.get("remoteJid") or key.get("keyRemoteJid") or data.get("remoteJid") or data.get("keyRemoteJid") or "").strip()
    if not remote_jid:
        return out
    msg = data.get("message") or data.get("content") or {}
    if isinstance(msg, str):
        text = msg
    else:
        text = msg.get("conversation") or msg.get("text") or (msg.get("extendedTextMessage") or {}).get("text") or ""
    text = (text or "").strip()
    if not text and not remote_jid:
        return out
    if instance:
        out.append((str(instance), remote_jid, text or " "))
    return out


@router.post("/evolution-webhook")
async def evolution_webhook(request: Request):
    """Recebe webhook da Evolution API (MESSAGES_UPSERT); chama core e envia resposta."""
    try:
        body = await request.json()
    except Exception:
        return {"ok": True}
    messages = _parse_evolution_message(body)
    for instance_name, remote_jid, text in messages:
        if not instance_name:
            continue
        tenant_id, config = _get_tenant_and_evolution_by_instance(instance_name)
        if not tenant_id or not config:
            continue
        from adapters.whatsapp_adapter import get_agent_response
        response = get_agent_response(tenant_id, remote_jid, text or "", is_audio=False, agent_id=config.get("agent_id"))
        reply_text = (response.get("resposta_texto") or "").strip()
        if reply_text:
            await _send_evolution_text(
                config["base_url"],
                config["api_key"],
                config["instance_name"],
                remote_jid,
                reply_text,
            )
    return {"ok": True}
