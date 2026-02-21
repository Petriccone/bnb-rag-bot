"""
CRUD para Equipes de Agentes (Agent Teams/Swarms)
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import json

from ..dependencies import get_current_user
from ..db import get_cursor

router = APIRouter(prefix="/teams", tags=["teams"])


def _ensure_teams_table():
    with get_cursor() as cur:
        # Create the agent_teams table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_teams (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                description TEXT,
                settings JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        
        # Add team_id to agents table safely
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'agents' AND column_name = 'team_id') THEN
                    ALTER TABLE agents ADD COLUMN team_id UUID REFERENCES agent_teams(id) ON DELETE SET NULL;
                END IF;
            END
            $$;
        """)


class TeamCreate(BaseModel):
    name: str
    description: str | None = None
    settings: dict | None = {}


class TeamUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    settings: dict | None = None


class TeamResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str | None
    settings: dict = {}
    agents_count: int = 0


@router.get("", response_model=list[TeamResponse])
def list_teams(user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant")
    
    _ensure_teams_table()
    
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT t.id, t.tenant_id, t.name, t.description, t.settings,
                   COUNT(a.id) as agents_count
            FROM agent_teams t
            LEFT JOIN agents a ON a.team_id = t.id AND a.active = true
            WHERE t.tenant_id = %s
            GROUP BY t.id
            ORDER BY t.created_at DESC
            """,
            (tenant_id,)
        )
        rows = cur.fetchall()
        
    return [
        TeamResponse(
            id=str(r["id"]),
            tenant_id=str(r["tenant_id"]),
            name=r["name"],
            description=r.get("description"),
            settings=r.get("settings") if isinstance(r.get("settings"), dict) else {},
            agents_count=int(r["agents_count"])
        )
        for r in rows
    ]


@router.post("", response_model=TeamResponse)
def create_team(body: TeamCreate, user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant")
    
    _ensure_teams_table()
    
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO agent_teams (tenant_id, name, description, settings)
               VALUES (%s, %s, %s, %s) RETURNING id, tenant_id, name, description, settings""",
            (tenant_id, body.name, body.description, json.dumps(body.settings or {}))
        )
        row = cur.fetchone()
        
    return TeamResponse(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        name=row["name"],
        description=row.get("description"),
        settings=row.get("settings") if isinstance(row.get("settings"), dict) else {},
        agents_count=0
    )


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(team_id: str, user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant")
    
    _ensure_teams_table()
    
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT t.id, t.tenant_id, t.name, t.description, t.settings,
                   COUNT(a.id) as agents_count
            FROM agent_teams t
            LEFT JOIN agents a ON a.team_id = t.id AND a.active = true
            WHERE t.id = %s AND t.tenant_id = %s
            GROUP BY t.id
            """,
            (team_id, tenant_id)
        )
        row = cur.fetchone()
        
    if not row:
        raise HTTPException(status_code=404, detail="Team not found")
        
    return TeamResponse(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        name=row["name"],
        description=row.get("description"),
        settings=row.get("settings") if isinstance(row.get("settings"), dict) else {},
        agents_count=int(row["agents_count"])
    )


@router.patch("/{team_id}", response_model=TeamResponse)
def update_team(team_id: str, body: TeamUpdate, user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant")
    
    _ensure_teams_table()
    
    updates = []
    params = []
    if body.name is not None:
        updates.append("name = %s")
        params.append(body.name)
    if body.description is not None:
        updates.append("description = %s")
        params.append(body.description)
    if body.settings is not None:
        updates.append("settings = %s")
        params.append(json.dumps(body.settings))
        
    if not updates:
        return get_team(team_id, user=user)
        
    updates.append("updated_at = NOW()")
    params.extend([team_id, tenant_id])
    
    query = f"UPDATE agent_teams SET {', '.join(updates)} WHERE id = %s AND tenant_id = %s RETURNING id"
    
    with get_cursor() as cur:
        cur.execute(query, tuple(params))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Team not found")
            
    return get_team(team_id, user=user)


@router.delete("/{team_id}")
def delete_team(team_id: str, user: dict = Depends(get_current_user)):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant")
    
    _ensure_teams_table()
    
    with get_cursor() as cur:
        # Puts team_id = NULL on agents is handled by ON DELETE SET NULL cascade
        cur.execute("DELETE FROM agent_teams WHERE id = %s AND tenant_id = %s RETURNING id", (team_id, tenant_id))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Team not found")
            
    return {"ok": True}
