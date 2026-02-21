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

def _get_tenant_agents(tenant_id: str) -> list[dict]:
    """Retorna a lista de agentes ativos disponíveis no tenant."""
    if not _use_postgres():
        return []
    
    conn = _get_pg_connection()
    agents = []
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, niche, prompt_custom FROM agents WHERE tenant_id = %s AND status = 'active'",
                (tenant_id,)
            )
            rows = cur.fetchall()
            for r in rows:
                desc = f"Name: {r['name']} - Niche: {r['niche']}"
                if r['prompt_custom']:
                    # Take only a snippet of custom prompt to save tokens
                    desc += f" - Behavior: {r['prompt_custom'][:100]}..." 
                agents.append({
                    "id": str(r["id"]),
                    "name": r["name"],
                    "description": desc
                })
        return agents
    except Exception as e:
        print(f"Error fetching tenant agents for supervisor: {e}")
        return []
    finally:
        conn.close()

def route_conversation(tenant_id: str, user_message: str, recent_log: list[dict], current_agent_id: str | None = None) -> dict:
    """
    Roteador do AIOS: Analisa a conversa e retorna o id do agente que deve responder.
    Retorna {"target_agent_id": UUID, "reason": str}
    """
    agents = _get_tenant_agents(tenant_id)
    
    # Se só houver 1 agente ou nenhum, não há o que rotear
    if len(agents) <= 1:
         return {"target_agent_id": current_agent_id or (agents[0]["id"] if agents else None), "reason": "Only one or zero agents available"}

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
