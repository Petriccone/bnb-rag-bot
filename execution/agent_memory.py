"""
Gerencia a Memória Compartilhada entre agentes no ecossistema AIOS.
Quando uma sessão é transferida (handoff) de um agente para outro, 
resumos e metadados são salvos aqui para dar contexto ao próximo agente.
"""

from execution.db_sessions import _use_postgres, _get_pg_connection

def save_shared_memory(tenant_id: str, session_id: str, source_agent_id: str, target_agent_id: str, content: str, memory_type: str = "handoff_summary") -> bool:
    """Salva um bloco de memória compartilhada quando ocorre um handoff ou extração de entidade."""
    if not _use_postgres():
        return False
        
    conn = _get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tenant_shared_memory 
                (tenant_id, session_id, source_agent_id, target_agent_id, memory_type, content)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (tenant_id, session_id, source_agent_id, target_agent_id, memory_type, content))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving shared memory: {e}")
        return False
    finally:
        conn.close()


def get_shared_memory(tenant_id: str, session_id: str, target_agent_id: str) -> list[dict]:
    """Recupera as memórias direcionadas a este agente para a sessão atual."""
    if not _use_postgres():
        return []
        
    conn = _get_pg_connection()
    try:
        with conn.cursor() as cur:
            # Busca memórias direcionadas a ele OU memórias públicas (target_agent_id IS NULL)
            cur.execute("""
                SELECT source_agent_id, memory_type, content, created_at 
                FROM tenant_shared_memory 
                WHERE tenant_id = %s 
                  AND session_id = %s 
                  AND (target_agent_id = %s OR target_agent_id IS NULL)
                ORDER BY created_at ASC
            """, (tenant_id, session_id, target_agent_id))
            
            rows = cur.fetchall()
            return [
                {
                    "source_agent_id": str(r["source_agent_id"]) if r["source_agent_id"] else None,
                    "memory_type": r["memory_type"],
                    "content": r["content"],
                    "created_at": r["created_at"].isoformat()
                } for r in rows
            ]
    except Exception as e:
        print(f"Error retrieving shared memory: {e}")
        return []
    finally:
        conn.close()

def build_shared_memory_prompt(tenant_id: str, session_id: str, agent_id: str) -> str:
    """Gera o texto de contexto das memórias recentes para injetar no LLM orchestrator."""
    memories = get_shared_memory(tenant_id, session_id, agent_id)
    if not memories:
        return ""
        
    prompt = "--- AIOS SHARED CONTEXT ---\nYou have been handed off this conversation or received extracted data from another agent. Consider the following context:\n"
    for m in memories:
        # Simplificação: Não exibir o source ID, apenas o tipo e conteúdo
        prompt += f"[{m['memory_type'].upper()}]: {m['content']}\n"
    
    prompt += "---------------------------\n"
    return prompt
