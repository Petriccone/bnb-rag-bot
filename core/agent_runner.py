"""
Core engine: executa o agente SPIN para um tenant/canal sem conhecer dashboard nem UI.
Chama execution (facade, db, RAG, LLM) e retorna resposta estruturada.
"""

import sys
from pathlib import Path

# Raiz do projeto no path para imports execution
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from typing import Any


def run_agent(
    tenant_id: str,
    channel: str,
    incoming_message: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """
    Executa uma rodada do agente para o tenant/canal.
    - tenant_id: UUID do tenant (ou "default" para legado).
    - channel: "telegram" | "whatsapp" (informativo).
    - incoming_message: texto da mensagem do lead.
    - metadata: {"lead_id": str, "is_audio": bool, "agent_id": str opcional}.
    Retorna: {"resposta_texto", "enviar_audio", "proximo_estado", "enviar_imagens", "modelos"}.
    """
    lead_id = str(metadata.get("lead_id", ""))
    is_audio = bool(metadata.get("is_audio", False))
    agent_id = metadata.get("agent_id")
    drive_folder_id_override = None

    if not lead_id:
        return {
            "resposta_texto": "Não foi possível identificar o contato.",
            "enviar_audio": False,
            "proximo_estado": "descoberta",
            "enviar_imagens": False,
            "modelos": [],
        }

    # Modo legado: tenant_id default ou ausente
    if not tenant_id or str(tenant_id).strip().lower() == "default":
        from execution.agent_facade import run_agent_facade
        return run_agent_facade(
            lead_id=lead_id,
            user_text=incoming_message.strip(),
            is_audio=is_audio,
            tenant_id=None,
            agent_id=None,
        )

    # Multi-tenant: resolver agente e config do tenant
    from execution import tenant_config
    tenant = tenant_config.get_tenant(tenant_id)
    if not tenant:
        return {
            "resposta_texto": "Empresa não encontrada. Entre em contato com o suporte.",
            "enviar_audio": False,
            "proximo_estado": "descoberta",
            "enviar_imagens": False,
            "modelos": [],
        }
    if not agent_id:
        agent = tenant_config.get_active_agent_for_tenant(tenant_id)
        agent_id = str(agent["id"]) if agent else None
    else:
        agent = tenant_config.get_agent_by_id(agent_id)
    if not agent_id or not agent:
        # Fallback: tenant existe mas não tem agente ativo — usa fluxo legado com tenant_id (sessão/log isolados)
        from execution.agent_facade import run_agent_facade
        settings = tenant.get("settings") or {}
        drive_folder_id_override = settings.get("drive_folder_id") if isinstance(settings, dict) else None
        return run_agent_facade(
            lead_id=lead_id,
            user_text=incoming_message.strip(),
            is_audio=is_audio,
            tenant_id=tenant_id,
            agent_id=None,
            drive_folder_id_override=drive_folder_id_override,
        )
    settings = tenant.get("settings") or {}
    if isinstance(settings, dict) and settings.get("drive_folder_id"):
        drive_folder_id_override = settings["drive_folder_id"]

    from execution.agent_facade import run_agent_facade
    return run_agent_facade(
        lead_id=lead_id,
        user_text=incoming_message.strip(),
        is_audio=is_audio,
        tenant_id=tenant_id,
        agent_id=str(agent["id"]),
        drive_folder_id_override=drive_folder_id_override,
    )
