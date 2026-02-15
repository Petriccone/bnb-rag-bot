"""
Adapter WhatsApp: chama core.agent_runner.run_agent e retorna resposta para envio.
O webhook (platform_backend) parseia o payload do Meta, obtém tenant_id pelo phone_number_id,
chama get_agent_response e envia a resposta via API do Meta.
"""

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def get_agent_response(
    tenant_id: str,
    lead_id: str,
    text: str,
    is_audio: bool = False,
    agent_id: str | None = None,
) -> dict[str, Any]:
    """
    Chama o core e retorna o dict de resposta (resposta_texto, enviar_audio, enviar_imagens, modelos).
    lead_id: identificador do contato no canal (ex.: número WhatsApp).
    agent_id: agente desta conta WhatsApp; None = primeiro agente ativo do tenant.
    """
    from core.agent_runner import run_agent
    return run_agent(
        tenant_id=tenant_id,
        channel="whatsapp",
        incoming_message=text or "",
        metadata={"lead_id": lead_id, "is_audio": is_audio, "agent_id": agent_id},
    )


def resolve_tenant_id_from_whatsapp(payload: dict[str, Any]) -> str:
    """Extrai tenant_id do payload (ex.: número associado a um tenant). Por ora retorna default."""
    return (__import__("os").environ.get("WHATSAPP_TENANT_ID", "default") or "default").strip()
