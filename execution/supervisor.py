"""
AIOS Supervisor Engine
Avalia a intenção do usuário e decide para qual agente a conversa deve ser direcionada,
com base no perfil (niche/description) de cada agente disponível no Tenant.
"""

import json
import os
from execution.db_sessions import _use_postgres, _get_pg_connection

# Fallback models in order of preference for pure routing logic (requires fast inference + tool calling)
SUPERVISOR_MODELS = [
    "anthropic/claude-3-haiku-20240307",  # Fast & cheap for routing
    "openai/gpt-4o-mini",
    "google/gemini-flash-1.5"
]

def _get_tenant_agents(tenant_id: str, allowed_ids: list[str] | None = None, team_id: str | None = None) -> list[dict]:
    """Retorna a lista de agentes ativos disponíveis no tenant.
    Se allowed_ids for fornecido, filtra apenas esses agentes (para can_delegate_to).
    Se team_id for fornecido, filtra apenas agentes daquela equipe.
    """
    if not _use_postgres():
        return []
    
    conn = _get_pg_connection()
    agents = []
    try:
        with conn.cursor() as cur:
            query = "SELECT id, name, niche, prompt_custom, settings FROM agents WHERE tenant_id = %s AND active = true"
            params = [tenant_id]
            if team_id:
                query += " AND team_id = %s"
                params.append(team_id)
                
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            for r in rows:
                agent_id = str(r["id"])
                # Filter by allowed_ids if provided
                if allowed_ids is not None and agent_id not in allowed_ids:
                    continue
                desc = f"Name: {r['name']} - Niche: {r['niche']}"
                if r['prompt_custom']:
                    desc += f" - Behavior: {r['prompt_custom'][:100]}..."
                agents.append({
                    "id": agent_id,
                    "name": r["name"],
                    "description": desc
                })
        return agents
    except Exception as e:
        print(f"Error fetching tenant agents for supervisor: {e}")
        return []
    finally:
        conn.close()


def _get_agent_settings(tenant_id: str, agent_id: str) -> dict:
    """Busca settings do agente atual para ler can_delegate_to."""
    if not _use_postgres():
        return {}
    conn = _get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT settings FROM agents WHERE id = %s AND tenant_id = %s",
                (agent_id, tenant_id)
            )
            row = cur.fetchone()
            if row and row["settings"]:
                settings = row["settings"]
                if isinstance(settings, str):
                    settings = json.loads(settings)
                return settings if isinstance(settings, dict) else {}
        return {}
    except Exception as e:
        print(f"Error fetching agent settings: {e}")
        return {}
    finally:
        conn.close()


def _get_agent_team_id(tenant_id: str, agent_id: str) -> str | None:
    """Busca o team_id do agente atual."""
    if not _use_postgres():
        return None
    conn = _get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT team_id FROM agents WHERE id = %s AND tenant_id = %s", (agent_id, tenant_id))
            row = cur.fetchone()
            if row and row["team_id"]:
                return str(row["team_id"])
        return None
    except Exception:
        return None
    finally:
        conn.close()


def route_conversation(tenant_id: str, user_message: str, recent_log: list[dict], current_agent_id: str | None = None) -> dict:
    """
    Roteador do AIOS: Analisa a conversa e retorna o id do agente que deve responder.
    Respeita can_delegate_to nos settings do agente atual.
    Retorna {"target_agent_id": UUID, "reason": str}
    """
    allowed_ids: list[str] | None = None
    team_id: str | None = None
    if current_agent_id and tenant_id:
        settings = _get_agent_settings(tenant_id, current_agent_id)
        can_delegate_to = settings.get("can_delegate_to")
        if isinstance(can_delegate_to, list) and len(can_delegate_to) > 0:
            allowed_ids = [str(aid) for aid in can_delegate_to]
        else:
            # Fallback para roteamento de equipe inteira
            team_id = _get_agent_team_id(tenant_id, current_agent_id)
            if not team_id:
                # Sem configuração de delegação ativa e fora de equipe -> não roteia
                return {"target_agent_id": current_agent_id, "reason": "No delegation or team configured for this agent"}

    agents = _get_tenant_agents(tenant_id, allowed_ids=allowed_ids, team_id=team_id)

    # Se só houver 1 agente ou nenhum (além do atual), não há o que rotear
    callable_agents = [a for a in agents if a["id"] != current_agent_id]
    if not callable_agents:
        return {"target_agent_id": current_agent_id or (agents[0]["id"] if agents else None), "reason": "No callable agents available"}

    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
         return {"target_agent_id": current_agent_id, "reason": "Missing OpenRouter API Key"}

    import httpx
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.environ.get("OPENROUTER_REFERER", "http://localhost:8000"),
        "X-Title": "AIOS-Supervisor",
    }
    
    system_prompt = (
        "You are the AIOS Supervisor Router. Your job is to analyze the conversation and route the user to the correct specialized agent.\n"
        "Here are the available agents for this tenant:\n\n"
    )
    for a in agents:
         system_prompt += f"AGENT_ID: {a['id']} | {a['description']}\n"
    
    if current_agent_id:
        system_prompt += f"\nThe user is currently talking to AGENT_ID: {current_agent_id}. DO NOT ROUTE unless the user's intent clearly falls outside the current agent's niche and perfectly matches another's.\n"

    system_prompt += "\nRespond ONLY with a JSON object. No markdown, no conversational text. Example: {\"target_agent_id\": \"uuid-here\", \"reason\": \"User asks about X, which fits agent Y.\"}"

    messages = [{"role": "system", "content": system_prompt}]
    
    # Add a bit of context for the supervisor (last 3 messages)
    context_msgs = recent_log[-3:] if len(recent_log) > 3 else recent_log
    for m in context_msgs:
         messages.append({"role": m["role"], "content": m["content"][:200]}) # Truncate message for speed
         
    messages.append({"role": "user", "content": f"New Message: {user_message}\n\nSelect the best AGENT_ID for this message as JSON."})

    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(
                url,
                json={
                    "model": SUPERVISOR_MODELS[0],
                    "models": SUPERVISOR_MODELS, # Allows fallback
                    "route": "fallback",
                    "messages": messages,
                    "response_format": {"type": "json_object"}
                },
                headers=headers
            )
            r.raise_for_status()
            data = r.json()
            response_text = data["choices"][0]["message"]["content"]
            parsed = json.loads(response_text)
            
            target_agent_id = parsed.get("target_agent_id")
            # Verify if the returned ID actually exists
            if target_agent_id and any(a["id"] == target_agent_id for a in agents):
                 return {
                     "target_agent_id": target_agent_id,
                     "reason": parsed.get("reason", "Supervisor decision")
                 }
                 
    except Exception as e:
        print(f"Supervisor routing error: {e}")
        
    return {"target_agent_id": current_agent_id, "reason": "Fallback to current due to error"}
