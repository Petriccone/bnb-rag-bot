"""
Camada 3 - Execução: orquestrador LLM.
Carrega diretivas, monta prompt (system + user com estado, RAG e histórico), chama OpenRouter
(API compatível com OpenAI), retorna resposta estruturada (texto, enviar_audio, próximo_estado, etc.).
"""

import json
import os
import re
from pathlib import Path
from typing import Any

from openai import OpenAI

from .state_machine import get_state_display_name, apply_transition

DIRECTIVES_DIR = Path(__file__).resolve().parent.parent / "directives"

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _get_client() -> OpenAI:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise ValueError("OPENROUTER_API_KEY não configurado no .env")
    return OpenAI(
        api_key=key,
        base_url=OPENROUTER_BASE_URL,
    )


def load_directives(skip_persona: bool = False, skip_spin_examples: bool = False) -> str:
    """Concatena o conteúdo de todos os .md em directives/ em ordem fixa.
    skip_persona: não carrega sdr_personalidade.md (evita 'filtros de água' sobrescrever agente customizado).
    skip_spin_examples: não carrega spin_selling.md (evita exemplos 'torneira, galão, filtro' no script de descoberta).
    """
    order = [
        "sdr_personalidade.md",
        "spin_selling.md",
        "rag_regras.md",
        "envio_imagens.md",
        "fechamento.md",
        "pos_venda.md",
        "audio_regras.md",
    ]
    parts = []
    for name in order:
        if skip_persona and name == "sdr_personalidade.md":
            continue
        if skip_spin_examples and name == "spin_selling.md":
            continue
        path = DIRECTIVES_DIR / name
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    return "\n\n---\n\n".join(parts)


def build_system_prompt(
    current_state: str,
    agent_name: str | None = None,
    agent_niche: str | None = None,
    agent_prompt_custom: str | None = None,
) -> str:
    state_instruction = (
        f"Estado atual da conversa: **{get_state_display_name(current_state)}** (valor interno: {current_state}). "
        "Siga as regras do SPIN: não pule etapas. Sua resposta (texto e tom) deve refletir SOMENTE este estado — "
        "não faça perguntas de descoberta se já estiver em oferta/fechamento; não pule para fechamento se ainda estiver em descoberta. "
        "proximo_estado: use o estado atual ou o PRÓXIMO na ordem (descoberta -> problema -> implicacao -> solucao -> oferta -> fechamento -> pos_venda). "
        "NUNCA retorne um estado anterior (ex.: se estiver em solucao, não retorne descoberta nem problema)."
    )
    has_custom_persona = bool(
        agent_name or agent_niche or (agent_prompt_custom and agent_prompt_custom.strip())
    )
    directives = load_directives(skip_persona=has_custom_persona, skip_spin_examples=has_custom_persona)

    if has_custom_persona:
        persona = f"Você é {agent_name or 'o agente'}"
        if agent_niche and agent_niche.strip():
            persona += f", atuando como {agent_niche.strip()}"
        persona += ". Apresente-se sempre com esse nome e nicho ao falar com o cliente. "
        if agent_prompt_custom and agent_prompt_custom.strip():
            persona += f"Instruções específicas: {agent_prompt_custom.strip()}. "
        persona += (
            "As diretivas abaixo são apenas para estilo de comunicação; "
            "NÃO fale de filtros, água, torneira, galão ou qualquer produto que não seja do seu nicho. "
            "Use o método SPIN na ordem: descoberta (perguntas sobre a situação do cliente no SEU nicho) -> problema (dores) -> implicação (riscos) -> solução/oferta -> fechamento. "
            "Siga as diretivas abaixo.\n\n"
        )
    else:
        persona = (
            "Você é um SDR de vendas de filtros de água. Siga rigorosamente as diretivas abaixo.\n\n"
        )
    return (
        persona
        + directives
        + "\n\n"
        + state_instruction
        + "\n\nIMPORTANTE: Interprete a mensagem atual e o histórico da conversa antes de responder. "
        "Se o cliente repetir a mesma coisa (ex.: vários 'oi'), varie a resposta em vez de repetir igual. "
        "Cada resposta deve ser específica para o que ele acabou de dizer.\n\n"
        "UMA ENTRADA = UMA RESPOSTA: Se a mensagem do cliente tiver várias linhas ou várias frases juntas "
        "(ex.: 'Oi' 'tudo bem?' 'quero mais informações' em sequência), trate como UMA só intenção e responda "
        "UMA única vez, de forma natural. Não responda ponto a ponto para cada linha ou frase.\n\n"
        "Responda em JSON no formato:\n"
        '{"resposta_texto": "...", "enviar_audio": true/false, "proximo_estado": "...", '
        '"enviar_imagens": true/false, "modelos": ["nome1", "nome2"] ou null}\n'
        "Use apenas informações do CONTEXTO RAG abaixo. Se não estiver no contexto, diga que vai verificar. "
        "resposta_texto: mensagem em texto para o cliente. proximo_estado: um dos estados SPIN. "
        "enviar_imagens: true apenas quando for hora de mostrar 2-3 modelos (fase solucao/oferta). "
        "modelos: lista com 2 ou 3 nomes de modelos da base para enviar imagens; se enviar_imagens false, use null."
    )


def build_user_message(
    user_message: str,
    rag_context: str,
    recent_log: list[dict],
) -> str:
    """Monta a mensagem do usuário com contexto RAG e histórico resumido."""
    parts = ["CONTEXTO DA BASE DE CONHECIMENTO (use apenas isso para preços, links, benefícios):\n", rag_context]
    if recent_log:
        parts.append("\n\nHistórico da conversa (use para interpretar repetições e contexto):")
        for m in recent_log[-12:]:
            role = "Cliente" if m["role"] == "user" else "Você"
            content = (m["content"] or "").strip()
            if content:
                parts.append(f"\n{role}: {content[:300]}")
    parts.append(f"\n\nMensagem atual do cliente (interprete antes de responder): {user_message}")
    return "\n".join(parts)


def _extract_json(text: str) -> dict:
    """Extrai um bloco JSON da resposta (pode vir com markdown ou texto antes/depois)."""
    text = text.strip()
    # Tente bloco ```json ... ```
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        return json.loads(m.group(1).strip())
    # Tente primeiro { ... } na linha
    start = text.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start : i + 1])
    raise ValueError("Nenhum JSON encontrado na resposta do LLM")


def run(
    user_id: str,
    user_message: str,
    current_state: str,
    rag_context: str,
    recent_log: list[dict],
    input_was_audio: bool = False,
    agent_name: str | None = None,
    agent_niche: str | None = None,
    agent_prompt_custom: str | None = None,
) -> dict[str, Any]:
    """
    Executa uma rodada do orquestrador.
    Retorna dict com: resposta_texto, enviar_audio, proximo_estado, enviar_imagens, modelos.
    Se agent_name/niche/prompt_custom forem passados, o system prompt usa a persona desse agente.
    """
    system = build_system_prompt(
        current_state,
        agent_name=agent_name,
        agent_niche=agent_niche,
        agent_prompt_custom=agent_prompt_custom,
    )
    user_content = build_user_message(user_message, rag_context, recent_log)

    client = _get_client()
    model = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        temperature=0.55,
    )
    raw = response.choices[0].message.content or ""

    try:
        out = _extract_json(raw)
    except (json.JSONDecodeError, ValueError):
        out = {
            "resposta_texto": raw[:2000] if raw else "Desculpe, tive um problema. Pode repetir?",
            "enviar_audio": False,
            "proximo_estado": current_state,
            "enviar_imagens": False,
            "modelos": None,
        }

    # Normalizar campos
    out.setdefault("resposta_texto", "")
    out.setdefault("enviar_audio", input_was_audio)
    out.setdefault("enviar_imagens", False)
    out.setdefault("modelos", None)
    # Garantir que proximo_estado nunca volta: só atual ou próximo na sequência
    raw_next = out.get("proximo_estado") or current_state
    out["proximo_estado"] = apply_transition(current_state, raw_next)
    if out.get("modelos") is not None and not isinstance(out["modelos"], list):
        out["modelos"] = None
    return out
