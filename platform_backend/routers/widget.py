"""
Widget Chat Router: endpoint público para o chat do widget embeddable.
Não requer autenticação JWT — usa agent_id + tenant_id no body (validados separadamente).
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/widget", tags=["widget"])


class WidgetChatRequest(BaseModel):
    agent_id: str
    tenant_id: str
    message: str
    session_id: str | None = None  # Optional: client can maintain session


@router.post("/chat")
def widget_chat(body: WidgetChatRequest):
    """Endpoint público para o widget de chat embeddable em websites."""
    msg = (body.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Mensagem vazia")

    # Validate agent belongs to tenant
    try:
        from ..db import get_cursor
        with get_cursor() as cur:
            cur.execute(
                "SELECT id, name, niche, prompt_custom, embedding_namespace FROM agents WHERE id = %s AND tenant_id = %s AND active = true",
                (body.agent_id, body.tenant_id),
            )
            row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Agente não encontrado ou inativo")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro de banco: {e}")

    # Use session_id from body or create a widget-specific lead_id
    lead_id = f"widget-{body.session_id or 'anonymous'}"

    try:
        import sys
        import os
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if root not in sys.path:
            sys.path.insert(0, root)
        from execution.agent_facade import run_agent_facade
        out = run_agent_facade(
            lead_id=lead_id,
            user_text=msg,
            tenant_id=body.tenant_id,
            agent_id=str(row["id"]),
            embedding_namespace_override=row.get("embedding_namespace"),
            agent_name_override=row.get("name"),
            agent_niche_override=row.get("niche"),
            agent_prompt_custom_override=row.get("prompt_custom"),
        )
        reply = (out.get("resposta_texto") or "").strip()
        return {"reply": reply, "estado": out.get("proximo_estado")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/{agent_id}")
def widget_config(agent_id: str, tenant_id: str):
    """Retorna configurações públicas do agente para inicializar o widget."""
    try:
        from ..db import get_cursor
        with get_cursor() as cur:
            cur.execute(
                "SELECT name, niche FROM agents WHERE id = %s AND tenant_id = %s AND active = true",
                (agent_id, tenant_id),
            )
            row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Agente não encontrado")
        return {"name": row["name"], "niche": row["niche"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
