"""
Platform Backend (SaaS) — FastAPI.
Autenticação JWT, CRUD tenant/agentes, upload documentos, métricas, WhatsApp (stub).
Consumido apenas pelo frontend_dashboard; o core não chama o platform.
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path, override=True)
except ImportError:
    pass

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, tenants, agents, documents, metrics, whatsapp, telegram, telegram_webhook


class VercelPathFixMiddleware(BaseHTTPMiddleware):
    """Na Vercel (api/index.py), o path pode chegar sem o prefixo /api (ex: /auth/register). Corrige para /api/..."""
    async def dispatch(self, request, call_next):
        path = request.scope.get("path") or ""
        method = request.scope.get("method") or ""
        # Vercel pode passar path real no query (quando dest usa ?path=/$1)
        if (path == "/" or path == "/index.py") and method != "GET":
            path_from_query = request.query_params.get("path")
            if path_from_query and path_from_query.startswith("/"):
                path = path_from_query
                request.scope["path"] = path
        if path and not path.startswith("/api") and path != "/" and path != "/health":
            if path.startswith("/auth") or path.startswith("/webhook") or path.startswith("/tenants") or path.startswith("/agents") or path.startswith("/documents") or path.startswith("/metrics") or path.startswith("/docs"):
                request.scope["path"] = "/api" + path
        return await call_next(request)


@asynccontextmanager
async def lifespan(app):
    """Inicia worker do buffer (webhook Telegram) se REDIS_URL estiver definido."""
    try:
        from .webhook_buffer import start_worker_if_needed
        start_worker_if_needed()
    except Exception:
        pass
    yield


app = FastAPI(title="B&B RAG Platform API", version="1.0.0", lifespan=lifespan)

app.add_middleware(VercelPathFixMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(tenants.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(whatsapp.router, prefix="/api")
app.include_router(telegram.router, prefix="/api")
app.include_router(telegram_webhook.router, prefix="/api/webhook/telegram")


@app.get("/")
def root():
    """Rota raiz: evita 404 ao abrir a URL da API no navegador."""
    return {
        "message": "B&B RAG Platform API",
        "docs": "/docs",
        "health": "/health",
        "api": "/api",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
