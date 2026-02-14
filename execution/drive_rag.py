"""
Camada 3 - Execução: RAG sobre pasta do Google Drive.
Lista e lê arquivos da pasta configurada; busca por query e retorna trechos para o LLM.
Nunca inventar: o LLM deve usar apenas o contexto retornado.

Credenciais: por arquivos (credentials.json + token.json) ou por variáveis de ambiente
GOOGLE_TOKEN_JSON e opcionalmente GOOGLE_CREDENTIALS_JSON (para deploy em PaaS sem arquivos).
"""

import io
import json
import os
import re
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Escopos necessários
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Mime types para exportar Docs/Sheets como texto
EXPORT_MIMETYPES = {
    "application/vnd.google-apps.document": "text/plain",
    "application/vnd.google-apps.spreadsheet": "text/csv",
}

# Imagens que podemos baixar e enviar (ex.: pasta bnbFiltros)
IMAGE_MIMETYPES = ("image/jpeg", "image/png", "image/webp", "image/gif")


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _get_credentials():
    """
    OAuth: prioridade 1) variáveis GOOGLE_TOKEN_JSON (e opcional GOOGLE_CREDENTIALS_JSON);
    2) arquivos token.json e credentials.json. Em produção (PaaS) use as variáveis.
    """
    creds = None
    token_json_env = os.environ.get("GOOGLE_TOKEN_JSON", "").strip()
    creds_json_env = os.environ.get("GOOGLE_CREDENTIALS_JSON", "").strip()

    if token_json_env:
        try:
            info = json.loads(token_json_env)
            creds = Credentials.from_authorized_user_info(info, SCOPES)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(
                "GOOGLE_TOKEN_JSON inválido. Cole o conteúdo completo do token.json (uma vez, gerado no seu PC)."
            ) from e
    else:
        token_path = _project_root() / "token.json"
        creds_path = _project_root() / "credentials.json"
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if creds_json_env:
                try:
                    secrets = json.loads(creds_json_env)
                    flow = InstalledAppFlow.from_client_config(secrets, SCOPES)
                    creds = flow.run_local_server(port=8080)
                except (json.JSONDecodeError, ValueError):
                    raise ValueError(
                        "GOOGLE_CREDENTIALS_JSON inválido. Use apenas para primeiro login (no PC); em produção use GOOGLE_TOKEN_JSON."
                    )
            else:
                creds_path = _project_root() / "credentials.json"
                if not creds_path.exists():
                    raise FileNotFoundError(
                        "Configure Google Drive: credentials.json + token.json no projeto, "
                        "ou variáveis GOOGLE_TOKEN_JSON (e opcional GOOGLE_CREDENTIALS_JSON) no ambiente."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
                creds = flow.run_local_server(port=8080)
            if not token_json_env:
                token_path = _project_root() / "token.json"
                with open(token_path, "w") as f:
                    f.write(creds.to_json())
    return creds


def _get_drive_service():
    return build("drive", "v3", credentials=_get_credentials())


def get_folder_id() -> str:
    folder_id = os.environ.get("DRIVE_FOLDER_ID", "").strip()
    if not folder_id:
        raise ValueError("DRIVE_FOLDER_ID não configurado no ambiente.")
    return folder_id


def list_files_in_folder(folder_id: str | None = None) -> list[dict]:
    """
    Lista arquivos na pasta (não percorre subpastas por simplicidade).
    Retorna lista de {id, name, mimeType}.
    """
    folder_id = folder_id or get_folder_id()
    service = _get_drive_service()
    results = (
        service.files()
        .list(
            q=f"'{folder_id}' in parents and trashed = false",
            pageSize=100,
            fields="files(id, name, mimeType)",
        )
        .execute()
    )
    return results.get("files", [])


def _download_file_content(service, file_id: str, mime_type: str) -> str:
    """Baixa ou exporta o conteúdo do arquivo como texto."""
    try:
        if mime_type in EXPORT_MIMETYPES:
            export_mime = EXPORT_MIMETYPES[mime_type]
            result = service.files().export(fileId=file_id, mimeType=export_mime).execute()
            return result.decode("utf-8", errors="replace") if isinstance(result, bytes) else str(result)
        # Arquivo binário ou texto: baixar
        request = service.files().get_media(fileId=file_id)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        content = buf.getvalue()
        return content.decode("utf-8", errors="replace")
    except Exception as e:
        return f"[Erro ao ler arquivo {file_id}: {e}]"


def load_folder_content(folder_id: str | None = None, use_cache: bool = True) -> str:
    """
    Carrega todo o texto da pasta (concatenação dos arquivos).
    Opcionalmente usa cache em .tmp/drive_cache.txt para evitar chamadas repetidas.
    """
    folder_id = folder_id or get_folder_id()
    cache_path = _project_root() / ".tmp" / "drive_cache.txt"
    if use_cache and cache_path.exists():
        return cache_path.read_text(encoding="utf-8", errors="replace")

    service = _get_drive_service()
    files = list_files_in_folder(folder_id)
    parts = []
    for f in files:
        mid = f.get("mimeType", "")
        # Ignorar pastas e binários que não exportamos
        if mid == "application/vnd.google-apps.folder":
            continue
        if mid in ("application/vnd.google-apps.document", "application/vnd.google-apps.spreadsheet"):
            text = _download_file_content(service, f["id"], mid)
        else:
            # Tentar baixar como texto (pode falhar para imagens etc.)
            try:
                text = _download_file_content(service, f["id"], mid)
            except Exception:
                continue
        if text.strip():
            parts.append(f"--- {f.get('name', f['id'])} ---\n{text}")
    full = "\n\n".join(parts)
    if use_cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(full, encoding="utf-8")
    return full


def search_chunks(query: str, full_content: str | None = None, chunk_size: int = 400, max_chunks: int = 15) -> str:
    """
    Busca por palavras da query no conteúdo e retorna trechos relevantes (300–500 chars).
    full_content: se None, carrega da pasta (com cache).
    """
    if full_content is None:
        full_content = load_folder_content()
    if not full_content.strip():
        return ""

    # Normalizar query: palavras-chave
    words = [w.strip().lower() for w in re.split(r"\s+", query) if w.strip()]
    if not words:
        return full_content[:3000]  # fallback: início do conteúdo

    # Dividir em blocos por parágrafo ou por tamanho
    blocks = re.split(r"\n\s*\n", full_content)
    scored = []
    for block in blocks:
        block = block.strip()
        if len(block) < 50:
            continue
        lower = block.lower()
        score = sum(1 for w in words if w in lower)
        if score > 0:
            scored.append((score, block))

    scored.sort(key=lambda x: -x[0])
    # Limitar tamanho por bloco e total
    result = []
    total_len = 0
    max_total = 6000
    for _, block in scored[:max_chunks]:
        if total_len >= max_total:
            break
        take = block[:chunk_size] + ("..." if len(block) > chunk_size else "")
        result.append(take)
        total_len += len(take)

    return "\n\n---\n\n".join(result) if result else full_content[:3000]


def find_subfolder_by_name(parent_id: str, folder_name: str) -> str | None:
    """Encontra uma subpasta pelo nome (case insensitive) dentro de parent_id. Retorna o id ou None."""
    service = _get_drive_service()
    files = list_files_in_folder(parent_id)
    name_lower = (folder_name or "").strip().lower()
    for f in files:
        if f.get("mimeType") == "application/vnd.google-apps.folder":
            if (f.get("name") or "").strip().lower() == name_lower:
                return f["id"]
    return None


def list_image_files_in_folder(folder_id: str) -> list[dict]:
    """Lista apenas arquivos de imagem na pasta. Retorna lista de {id, name, mimeType}."""
    service = _get_drive_service()
    results = (
        service.files()
        .list(
            q=f"'{folder_id}' in parents and trashed = false",
            pageSize=50,
            fields="files(id, name, mimeType)",
        )
        .execute()
    )
    files = results.get("files", [])
    return [f for f in files if (f.get("mimeType") or "").startswith("image/")]


def download_file_binary(file_id: str, save_path: Path) -> None:
    """Baixa um arquivo do Drive (ex.: imagem) para o path local."""
    service = _get_drive_service()
    request = service.files().get_media(fileId=file_id)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()


def get_filter_images_from_drive(
    folder_name: str | None = None,
    max_images: int = 5,
) -> list[Path]:
    """
    Localiza a pasta de imagens de filtros (ex.: bnbFiltros) dentro do DRIVE_FOLDER_ID,
    baixa até max_images para .tmp e retorna lista de paths locais.
    Se a pasta não existir ou não houver imagens, retorna lista vazia.
    """
    folder_name = (folder_name or os.environ.get("DRIVE_FILTER_IMAGES_FOLDER", "bnbFiltros")).strip()
    if not folder_name:
        return []
    try:
        parent_id = get_folder_id()
        subfolder_id = find_subfolder_by_name(parent_id, folder_name)
        if not subfolder_id:
            return []
        images = list_image_files_in_folder(subfolder_id)
        if not images:
            return []
        tmp_dir = _project_root() / ".tmp" / "drive_images"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for i, img in enumerate(images[:max_images]):
            ext = ".jpg"  # default
            mime = (img.get("mimeType") or "").lower()
            if "png" in mime:
                ext = ".png"
            elif "webp" in mime:
                ext = ".webp"
            elif "gif" in mime:
                ext = ".gif"
            safe_name = re.sub(r"[^\w\-.]", "_", (img.get("name") or img["id"])[:50])
            path = tmp_dir / f"{safe_name}_{img['id'][:8]}{ext}"
            try:
                download_file_binary(img["id"], path)
                paths.append(path)
            except Exception:
                continue
        return paths
    except Exception:
        return []


def search(query: str, state: str | None = None) -> str:
    """
    API principal para o orquestrador: busca no Drive e retorna contexto para o LLM.
    state pode ser usado para enriquecer a query (ex.: em fechamento incluir "link pagamento").
    """
    if state == "fechamento":
        query = f"{query} link pagamento compra"
    content = load_folder_content()
    return search_chunks(query, full_content=content)


if __name__ == "__main__":
    import sys
    os.chdir(_project_root())
    from dotenv import load_dotenv
    load_dotenv()
    folder_id = get_folder_id()
    print("Listando arquivos em", folder_id)
    for f in list_files_in_folder(folder_id):
        print(f["name"], f["mimeType"])
    q = sys.argv[1] if len(sys.argv) > 1 else "preço filtro"
    print("\nBusca:", q)
    print(search(q)[:1500])
