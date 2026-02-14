"""
Upload e listagem de documentos por tenant (base de conhecimento).
"""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from ..auth import get_current_user
from ..config import get_settings
from ..db import get_cursor

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: str
    tenant_id: str
    file_path: str
    embedding_namespace: str


def _ensure_tenant(user: dict):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant")
    return str(tenant_id)


@router.get("", response_model=list[DocumentResponse])
def list_documents(user: dict = Depends(get_current_user)):
    tenant_id = _ensure_tenant(user)
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, tenant_id, file_path, embedding_namespace FROM documents WHERE tenant_id = %s ORDER BY created_at DESC",
            (tenant_id,),
        )
        rows = cur.fetchall()
    return [
        DocumentResponse(
            id=str(r["id"]),
            tenant_id=str(r["tenant_id"]),
            file_path=r["file_path"],
            embedding_namespace=r["embedding_namespace"],
        )
        for r in rows
    ]


@router.post("", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    embedding_namespace: str | None = None,
    user: dict = Depends(get_current_user),
):
    tenant_id = _ensure_tenant(user)
    settings = get_settings()
    os.makedirs(settings.upload_dir, exist_ok=True)
    ext = os.path.splitext(file.filename or "file")[1] or ".bin"
    safe_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.upload_dir, safe_name)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    namespace = embedding_namespace or f"tenant_{tenant_id}"
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO documents (tenant_id, file_path, embedding_namespace)
               VALUES (%s, %s, %s) RETURNING id, tenant_id, file_path, embedding_namespace""",
            (tenant_id, file_path, namespace),
        )
        row = cur.fetchone()
    return DocumentResponse(
        id=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        file_path=row["file_path"],
        embedding_namespace=row["embedding_namespace"],
    )


@router.delete("/{document_id}")
def delete_document(document_id: str, user: dict = Depends(get_current_user)):
    tenant_id = _ensure_tenant(user)
    with get_cursor() as cur:
        cur.execute(
            "SELECT file_path FROM documents WHERE id = %s AND tenant_id = %s",
            (document_id, tenant_id),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    if os.path.isfile(row["file_path"]):
        try:
            os.remove(row["file_path"])
        except OSError:
            pass
    with get_cursor() as cur:
        cur.execute("DELETE FROM documents WHERE id = %s AND tenant_id = %s", (document_id, tenant_id))
    return {"ok": True}
