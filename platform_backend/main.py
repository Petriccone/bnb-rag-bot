"""
Platform Backend (SaaS) — FastAPI.
Autenticação JWT, CRUD tenant/agentes, upload documentos, métricas, WhatsApp (stub).
Consumido apenas pelo frontend_dashboard; o core não chama o platform.
Routers carregados um a um para não derrubar a app na Vercel se um falhar no import.
"""
import os
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

# Force uvicorn reload
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path, override=True)
except ImportError:
    pass

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

_import_errors = []

def _safe_import(name: str):
    try:
        mod = __import__(f"platform_backend.routers.{name}", fromlist=["router"])
        return getattr(mod, "router", None)
    except Exception as e:
        _import_errors.append({"router": name, "error": str(e), "traceback": traceback.format_exc()})
        return None

auth = _safe_import("auth")
tenants = _safe_import("tenants")
agents = _safe_import("agents")
documents = _safe_import("documents")
metrics = _safe_import("metrics")
usage = _safe_import("usage")
whatsapp = _safe_import("whatsapp")
telegram = _safe_import("telegram")
telegram_webhook = _safe_import("telegram_webhook")
billing = _safe_import("billing")
widget = _safe_import("widget")
teams = _safe_import("teams")


def _normalize_api_path(raw: str) -> str:
    if not raw or not raw.startswith("/"):
        return ""
    return raw if raw.startswith("/api") else "/api" + raw


class VercelPathFixMiddleware(BaseHTTPMiddleware):
    """Na Vercel o path chega como "/". Corrige com header X-Request-Path, query _path ou prefixo /api."""
    async def dispatch(self, request, call_next):
        path = request.scope.get("path") or ""
        method = request.scope.get("method") or ""
        fixed = ""
        if path in ("/", "/index.py") and method != "GET":
            fixed = _normalize_api_path(request.headers.get("x-request-path") or "")
            if not fixed:
                fixed = _normalize_api_path(request.query_params.get("_path") or request.query_params.get("path") or "")
        if fixed:
            request.scope["path"] = fixed
        elif path and not path.startswith("/api") and path not in ("/", "/health", "/index.py"):
            request.scope["path"] = "/api" + path
        return await call_next(request)


@asynccontextmanager
async def lifespan(app):
    """Inicia worker do buffer (webhook Telegram) se REDIS_URL estiver definido."""
    # Na Vercel, threads em background não funcionam bem (congelam entre requests).
    # Desativamos para evitar overhead e erros.
    if os.environ.get("VERCEL"):
        yield
        return

    try:
        from .webhook_buffer import start_worker_if_needed
        start_worker_if_needed()
    except Exception:
        pass
    yield


app = FastAPI(title="B&B RAG Platform API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://botfyai.vercel.app",
        "https://botfy-dashboard.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
# VercelPathFixMiddleware deve vir DEPOIS do CORS para não interferir nos headers
app.add_middleware(VercelPathFixMiddleware)

if auth:
    app.include_router(auth, prefix="/api")
if tenants:
    app.include_router(tenants, prefix="/api")
if agents:
    app.include_router(agents, prefix="/api")
if documents:
    app.include_router(documents, prefix="/api")
if metrics:
    app.include_router(metrics, prefix="/api")
if usage:
    app.include_router(usage, prefix="/api")
if whatsapp:
    app.include_router(whatsapp, prefix="/api")
if telegram:
    app.include_router(telegram, prefix="/api")
if telegram_webhook:
    app.include_router(telegram_webhook, prefix="/api/webhook/telegram")
if billing:
    app.include_router(billing, prefix="/api")
if widget:
    app.include_router(widget, prefix="/api")
if teams:
    app.include_router(teams, prefix="/api")


@app.get("/")
@app.get("/api")
@app.get("/api/")
def root():
    """Rota raiz: evita 404 ao abrir a URL da API no navegador."""
    return {
        "message": "B&B RAG Platform API",
        "docs": "/docs",
        "health": "/api/health",
        "api": "/api",
        "import_errors": "/api/import-error"
    }


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/import-error")
@app.get("/api/import-error")
def import_error():
    """Diagnóstico: lista routers que falharam no import (para debug na Vercel)."""
    return {"errors": _import_errors}
