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
from .state_machine import apply_transition


def _drive_search(user_text: str, state: str) -> str:
    """Import lazy para não quebrar na Vercel quando google.* não está no bundle."""
    try:
        from .drive_rag import search as drive_search
        return drive_search(user_text, state=state)
    except Exception as e:
        return (
            "CONTEXTO: A base de conhecimento não está disponível no momento. "
            "Não invente preços ou links; diga que vai verificar. "
            f"(Erro: {e})"
        )


def run_agent_facade(
    lead_id: str,
    user_text: str,
    is_audio: bool = False,
    tenant_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    drive_folder_id_override: Optional[str] = None,
    embedding_namespace_override: Optional[str] = None,
) -> dict[str, Any]:
    """
    Executa uma rodada do agente: sessão, RAG, LLM, transição de estado, log.
    Retorna dict com resposta_texto, enviar_audio, proximo_estado, enviar_imagens, modelos.
    Quando tenant_id e agent_id são informados, usa tabelas multi-tenant (conversations, tenant_conversation_log).
    """
    init_db()
    session = get_or_create_session(lead_id, tenant_id=tenant_id, agent_id=agent_id)
    current_state = session["current_state"]

    # DRIVE_RAG_DISABLED=1 desativa o RAG do Google Drive (usa só base de conhecimento por documentos)
    drive_disabled = os.environ.get("DRIVE_RAG_DISABLED", "").strip() in ("1", "true", "yes")

    if not drive_disabled and drive_folder_id_override:
        rag_context = _rag_for_folder(drive_folder_id_override, user_text, current_state)
    elif not drive_disabled and os.environ.get("DRIVE_FOLDER_ID", "").strip():
        rag_context = _drive_search(user_text, current_state)
    elif tenant_id:
        # Base de conhecimento por documentos enviados no dashboard (pgvector)
        try:
            from .knowledge_rag import search_document_chunks
            rag_context = search_document_chunks(
                tenant_id, user_text, limit=6,
                embedding_namespace=embedding_namespace_override,
            )
        except Exception as e:
            rag_context = (
                "CONTEXTO: Base de conhecimento indisponível. Não invente dados. "
                f"(Erro: {e})"
            )
        if not rag_context or not rag_context.strip():
            rag_context = (
                "CONTEXTO: Nenhum documento na base de conhecimento. "
                "Envie arquivos em Base de conhecimento no dashboard (PDF ou TXT). "
                "Não invente preços ou especificações."
            )
    else:
        rag_context = (
            "CONTEXTO: A base de conhecimento (Google Drive) não está configurada. "
            "Não invente preços, links, modelos ou especificações. "
            "Para dúvidas sobre produtos ou pagamento, diga que vai verificar. "
            "Foque nas perguntas SPIN e no relacionamento consultivo."
        )

    recent_log = get_recent_log(lead_id, limit=12, tenant_id=tenant_id, agent_id=agent_id)

    agent_info = None
    if agent_id:
        try:
            from .tenant_config import get_agent_by_id
            agent_info = get_agent_by_id(agent_id)
        except Exception:
            pass

    from .llm_orchestrator import run as llm_run
    out = llm_run(
        user_id=lead_id,
        user_message=user_text,
        current_state=current_state,
        rag_context=rag_context,
        recent_log=recent_log,
        input_was_audio=is_audio,
        agent_name=(agent_info or {}).get("name"),
        agent_niche=(agent_info or {}).get("niche"),
        agent_prompt_custom=(agent_info or {}).get("prompt_custom"),
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
        return _drive_search(query, state)
    finally:
        if old is not None:
            os.environ["DRIVE_FOLDER_ID"] = old
        elif "DRIVE_FOLDER_ID" in os.environ:
            del os.environ["DRIVE_FOLDER_ID"]
