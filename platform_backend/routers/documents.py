"""
Upload e listagem de documentos por tenant (base de conhecimento).
Suporta: PDF, Excel (.xlsx, .xls), Word (.docx), CSV, Markdown, HTML, URLs.
"""
import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from pydantic import BaseModel

from ..dependencies import get_current_user
from ..config import get_settings
from ..db import get_cursor

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: str
    tenant_id: str
    file_path: str
    file_name: str
    file_size_mb: float
    file_type: str
    embedding_namespace: str
    source_url: Optional[str] = None
    status: str  # pending, processing, completed, failed


class URLDocumentRequest(BaseModel):
    url: str
    embedding_namespace: Optional[str] = None


def _ensure_tenant(user: dict):
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Usuário sem tenant")
    return str(tenant_id)


@router.get("", response_model=list[DocumentResponse])
def list_documents(user: dict = Depends(get_current_user)):
    try:
        tenant_id = _ensure_tenant(user)
        with get_cursor() as cur:
            cur.execute(
                """SELECT * FROM documents WHERE tenant_id = %s ORDER BY id DESC""",
                (tenant_id,),
            )
            rows = cur.fetchall()
        return [
            DocumentResponse(
                id=str(r["id"]),
                tenant_id=str(r["tenant_id"]),
                file_path=r.get("file_path") or "",
                file_name=(r.get("file_name") or (r.get("file_path") and os.path.basename(r["file_path"])) or "unknown"),
                file_size_mb=float(r.get("file_size_mb") or 0),
                file_type=(r.get("file_type") or "unknown"),
                embedding_namespace=r.get("embedding_namespace") or "",
                source_url=r.get("source_url"),
                status=(r.get("status") or "pending"),
            )
            for r in rows
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    embedding_namespace: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """
    Upload de documento para a base de conhecimento.
    Suporta: .txt, .pdf, .xlsx, .xls, .docx, .csv, .md, .html
    """
    # #region agent log
    _log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "debug-21fe81.log")
    def _debug_log(msg: str, data: dict, hyp: str):
        import json
        payload = {"sessionId": "21fe81", "location": "documents.py:upload", "message": msg, "data": data, "hypothesisId": hyp, "timestamp": __import__("time").time() * 1000}
        print(f"[DEBUG 21fe81] {json.dumps(payload)}")
        try:
            with open(_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload) + "\n")
        except Exception:
            pass
    # #endregion
    try:
        return await _upload_document_impl(file, embedding_namespace, user, _debug_log, background_tasks)
    except HTTPException:
        raise
    except Exception as e:
        _debug_log("upload_document unhandled", {"error_type": type(e).__name__, "error_msg": str(e)}, "A")
        raise HTTPException(status_code=500, detail=str(e))


async def _upload_document_impl(file, embedding_namespace, user, _debug_log, background_tasks: BackgroundTasks):
    tenant_id = _ensure_tenant(user)
    # #region agent log
    _debug_log("upload_document entry", {"tenant_id": tenant_id, "filename": file.filename}, "A")
    # #endregion
    settings = get_settings()
    
    # Valida extensão
    allowed_extensions = {".txt", ".pdf", ".xlsx", ".xls", ".docx", ".csv", ".md", ".html"}
    ext = os.path.splitext(file.filename or "file")[1].lower()
    
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Formato não suportado. Use: {', '.join(allowed_extensions)}"
        )
    
    row = None
    doc_id = None
    try:
        os.makedirs(settings.upload_dir, exist_ok=True)
        safe_name = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(settings.upload_dir, safe_name)
        # #region agent log
        _debug_log("before file save", {"upload_dir": settings.upload_dir, "file_path": file_path}, "B")
        # #endregion
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        file_size_mb = len(content) / (1024 * 1024)
        namespace = embedding_namespace or f"tenant_{tenant_id}"
        # #region agent log
        _debug_log("before INSERT", {"doc_id": doc_id}, "A")
        # #endregion
        with get_cursor() as cur:
            cur.execute(
                """INSERT INTO documents (tenant_id, file_path, embedding_namespace, file_name, file_size_mb, file_type, status)
                   VALUES (%s, %s, %s, %s, %s, %s, 'pending') 
                   RETURNING id, tenant_id, file_path, embedding_namespace, file_name, file_type""",
                (tenant_id, file_path, namespace, file.filename, file_size_mb, ext[1:]),
            )
            row = cur.fetchone()
            doc_id = str(row["id"])
    except Exception as e:
        # #region agent log
        _debug_log("upload step failed", {"error_type": type(e).__name__, "error_msg": str(e)}, "A")
        # #endregion
        raise

    # Launch background processing
    if doc_id:
        background_tasks.add_task(
            process_document_task,
            doc_id=doc_id,
            file_path=file_path,
            tenant_id=tenant_id,
            embedding_namespace=namespace,
            file_name=file.filename,
            file_type=ext[1:]
        )

    return DocumentResponse(
        id=doc_id,
        tenant_id=str(row["tenant_id"]),
        file_path=row["file_path"],
        file_name=file.filename or row.get("file_name") or "file",
        file_size_mb=float(file_size_mb),
        file_type=ext[1:] or row.get("file_type") or "unknown",
        embedding_namespace=row.get("embedding_namespace") or namespace,
        source_url=row.get("source_url"),
        status="pending",
    )


@router.post("/url", response_model=DocumentResponse)
async def upload_from_url(
    background_tasks: BackgroundTasks,
    request: URLDocumentRequest,
    user: dict = Depends(get_current_user),
):
    """
    Upload de documento a partir de uma URL.
    Faz scraping do conteúdo da página.
    """
    import requests
    from pathlib import Path
    
    tenant_id = _ensure_tenant(user)
    settings = get_settings()
    
    # Baixa conteúdo da URL
    try:
        response = requests.get(request.url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; B&B-RAG-Bot/1.0)'
        })
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao baixar URL: {e}")
    
    # Determina tipo de arquivo pelo content-type
    content_type = response.headers.get('content-type', 'text/html')
    ext_map = {
        'text/html': '.html',
        'text/plain': '.txt',
        'application/pdf': '.pdf',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
        'application/vnd.ms-excel': '.xls',
    }
    ext = ext_map.get(content_type.split(';')[0].strip(), '.html')
    
    # Salva arquivo temporariamente
    os.makedirs(settings.upload_dir, exist_ok=True)
    safe_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.upload_dir, safe_name)
    
    with open(file_path, "wb") as f:
        f.write(response.content)
    
    file_size_mb = len(response.content) / (1024 * 1024)
    namespace = request.embedding_namespace or f"tenant_{tenant_id}"
    doc_id = None
    
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO documents (tenant_id, file_path, embedding_namespace, file_name, file_size_mb, file_type, status)
               VALUES (%s, %s, %s, %s, %s, %s, 'pending') 
               RETURNING id, tenant_id, file_path, embedding_namespace, file_name, file_type""",
            (tenant_id, file_path, namespace, request.url.split("/")[-1] or "webpage", file_size_mb, ext[1:]),
        )
        row = cur.fetchone()
        doc_id = str(row["id"])

    # Launch background processing
    if doc_id:
        background_tasks.add_task(
            process_document_task,
            doc_id=doc_id,
            file_path=file_path,
            tenant_id=tenant_id,
            embedding_namespace=namespace,
            file_name=row.get("file_name") or request.url.split("/")[-1] or "webpage",
            file_type=ext[1:]
        )

    return DocumentResponse(
        id=doc_id,
        tenant_id=str(row["tenant_id"]),
        file_path=row["file_path"],
        file_name=row.get("file_name") or request.url.split("/")[-1] or "webpage",
        file_size_mb=float(file_size_mb),
        file_type=ext[1:] or "unknown",
        embedding_namespace=row.get("embedding_namespace") or namespace,
        source_url=row.get("source_url") or request.url,
        status="pending",
    )


@router.delete("/{document_id}")
def delete_document(document_id: str, user: dict = Depends(get_current_user)):
    """Deleta um documento e seus chunks."""
    tenant_id = _ensure_tenant(user)
    with get_cursor() as cur:
        cur.execute(
            "SELECT file_path FROM documents WHERE id = %s AND tenant_id = %s",
            (document_id, tenant_id),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    # Remove chunks
    try:
        import sys
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from execution.document_ingest import delete_chunks_for_document
        delete_chunks_for_document(document_id)
    except Exception:
        pass
    
    # Remove arquivo físico
    if os.path.isfile(row["file_path"]):
        try:
            os.remove(row["file_path"])
        except OSError:
            pass
    
    # Remove registro
    with get_cursor() as cur:
        cur.execute("DELETE FROM documents WHERE id = %s AND tenant_id = %s", (document_id, tenant_id))
    
    return {"ok": True}


@router.get("/{document_id}/status")
def get_document_status(document_id: str, user: dict = Depends(get_current_user)):
    """Retorna o status do processamento de um documento."""
    tenant_id = _ensure_tenant(user)
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, status, file_name, file_type FROM documents WHERE id = %s AND tenant_id = %s",
            (document_id, tenant_id),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    return {
        "id": str(row["id"]),
        "status": row["status"],
        "file_name": row["file_name"],
        "file_type": row["file_type"],
    }


class DocumentRenameRequest(BaseModel):
    file_name: str


@router.patch("/{document_id}")
def rename_document(document_id: str, request: DocumentRenameRequest, user: dict = Depends(get_current_user)):
    """Renomeia o arquivo na base de dados (apenas o display name visual)."""
    tenant_id = _ensure_tenant(user)
    if not request.file_name or not request.file_name.strip():
        raise HTTPException(status_code=400, detail="Nome do arquivo não pode ser vazio")
        
    with get_cursor() as cur:
        cur.execute(
            "UPDATE documents SET file_name = %s WHERE id = %s AND tenant_id = %s RETURNING id",
            (request.file_name.strip(), document_id, tenant_id)
        )
        row = cur.fetchone()
        
    if not row:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
        
    return {"ok": True, "file_name": request.file_name.strip()}

# --- BACKGROUND WORKER ---

def process_document_task(doc_id: str, file_path: str, tenant_id: str, embedding_namespace: str, file_name: str, file_type: str):
    """Worker de segundo plano para processar documentos (extração + embedding)."""
    import sys
    from pathlib import Path
    
    # Atualiza status inicial
    try:
        with get_cursor() as cur:
            cur.execute(
                "UPDATE documents SET status = 'processing', file_name = %s, file_type = %s, file_size_mb = %s WHERE id = %s",
                (file_name, file_type, os.path.getsize(file_path) / (1024 * 1024), doc_id)
            )
    except Exception:
        pass

    try:
        root = Path(__file__).resolve().parents[2]
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        
        from execution.document_ingest_extended import _extract_text_from_file, _chunk_text
        from execution.knowledge_rag import _embed
        from execution.document_ingest import _get_connection

        # Extração
        text = _extract_text_from_file(file_path)
        chunks = _chunk_text(text)
        
        if not chunks:
            with get_cursor() as cur:
                cur.execute("UPDATE documents SET status = 'completed' WHERE id = %s", (doc_id,))
            return

        # Embeddings
        embeddings = _embed(chunks)
        
        # Salvamento
        conn = _get_connection()
        try:
            with conn.cursor() as cur:
                for i, (content_chunk, emb) in enumerate(zip(chunks, embeddings)):
                    vec_str = "[" + ",".join(str(x) for x in emb) + "]"
                    cur.execute(
                        """INSERT INTO document_chunks (tenant_id, document_id, chunk_index, content, embedding)
                           VALUES (%s, %s, %s, %s, %s::vector)""",
                        (tenant_id, doc_id, i, content_chunk, vec_str),
                    )
            conn.commit()
            
            with get_cursor() as cur:
                cur.execute("UPDATE documents SET status = 'completed' WHERE id = %s", (doc_id,))
        finally:
            conn.close()

    except Exception as e:
        print(f"Error processing document {doc_id}: {e}")
        try:
            with get_cursor() as cur:
                cur.execute("UPDATE documents SET status = 'failed' WHERE id = %s", (doc_id,))
        except Exception:
            pass
