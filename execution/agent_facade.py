"""
Fachada de alto nível: executa o fluxo SPIN (sessão, RAG, LLM, estado) e retorna resposta estruturada.
Usado pelo core/agent_runner e pelo handler legado (com tenant_id/agent_id opcionais).
Não envia mensagens; apenas retorna o dict (resposta_texto, enviar_audio, proximo_estado, enviar_imagens, modelos).
"""

import os
from typing import Any, Optional

from .db_sessions import (
    append_log,
    get_or_create_session,
    get_recent_log,
    init_db,
    update_classification,
    update_state,
)
from .drive_rag import search as drive_search
from .llm_orchestrator import run as llm_run
from .state_machine import apply_transition


def run_agent_facade(
    lead_id: str,
    user_text: str,
    is_audio: bool = False,
    tenant_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    drive_folder_id_override: Optional[str] = None,
) -> dict[str, Any]:
    """
    Executa uma rodada do agente: sessão, RAG, LLM, transição de estado, log.
    Retorna dict com resposta_texto, enviar_audio, proximo_estado, enviar_imagens, modelos.
    Quando tenant_id e agent_id são informados, usa tabelas multi-tenant (conversations, tenant_conversation_log).
    """
    init_db()
    session = get_or_create_session(lead_id, tenant_id=tenant_id, agent_id=agent_id)
    current_state = session["current_state"]

    if drive_folder_id_override:
        rag_context = _rag_for_folder(drive_folder_id_override, user_text, current_state)
    elif os.environ.get("DRIVE_FOLDER_ID", "").strip():
        try:
            rag_context = drive_search(user_text, state=current_state)
        except Exception as e:
            rag_context = (
                "CONTEXTO: A base de conhecimento não está disponível no momento. "
                "Não invente preços ou links; diga que vai verificar. "
                f"(Erro: {e})"
            )
    else:
        rag_context = (
            "CONTEXTO: A base de conhecimento (Google Drive) não está configurada. "
            "Não invente preços, links, modelos ou especificações. "
            "Para dúvidas sobre produtos ou pagamento, diga que vai verificar. "
            "Foque nas perguntas SPIN e no relacionamento consultivo."
        )

    recent_log = get_recent_log(lead_id, limit=20, tenant_id=tenant_id, agent_id=agent_id)

    out = llm_run(
        user_id=lead_id,
        user_message=user_text,
        current_state=current_state,
        rag_context=rag_context,
        recent_log=recent_log,
        input_was_audio=is_audio,
    )

    resposta_texto = (out.get("resposta_texto") or "").strip()
    proximo_estado = out.get("proximo_estado") or current_state
    new_state = apply_transition(current_state, proximo_estado)
    if new_state != current_state:
        update_state(lead_id, new_state, tenant_id=tenant_id, agent_id=agent_id)

    append_log(lead_id, "user", user_text, "audio" if is_audio else "text", tenant_id=tenant_id, agent_id=agent_id)
    append_log(lead_id, "assistant", resposta_texto, "text", tenant_id=tenant_id, agent_id=agent_id)

    if new_state == "fechamento":
        update_classification(lead_id, "quente", tenant_id=tenant_id, agent_id=agent_id)

    return {
        "resposta_texto": resposta_texto,
        "enviar_audio": out.get("enviar_audio", False),
        "proximo_estado": new_state,
        "enviar_imagens": out.get("enviar_imagens", False),
        "modelos": out.get("modelos") or [],
    }


def _rag_for_folder(folder_id: str, query: str, state: str) -> str:
    """Busca RAG para um folder_id específico (tenant). Por ora delega para drive_search com env override temporário."""
    old = os.environ.get("DRIVE_FOLDER_ID")
    try:
        os.environ["DRIVE_FOLDER_ID"] = folder_id
        return drive_search(query, state=state)
    finally:
        if old is not None:
            os.environ["DRIVE_FOLDER_ID"] = old
        elif "DRIVE_FOLDER_ID" in os.environ:
            del os.environ["DRIVE_FOLDER_ID"]
